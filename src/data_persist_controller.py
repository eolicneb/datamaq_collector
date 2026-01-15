from dataclasses import dataclass, InitVar
from datetime import datetime
from functools import partial
from typing import Union, Collection, Optional, Callable, Iterable

from sqlalchemy.exc import IntegrityError

from src.logger import a_logger
from src.application.interfaces import IDatabaseRepository
from src.domain.reading import Reading
from src.infrastructure.data_cache import MemoryCache
from src.utils.scheduler import ScheduledController

ReadingData = Union[Reading, Collection[Reading]]


@dataclass
class DataPersistSetup:
    label: Optional[str] = None
    units: Optional[str] = None
    period: Optional[float] = None
    method: InitVar[str] = None
    aggregation: Optional[Callable[[float, ReadingData], ReadingData]] = None

    def __post_init__(self, method: str = None):
        if method:
            aggregation_obj = AggregationDataProcessMethods(self)
            self.aggregation = getattr(aggregation_obj, method)


class AggregationDataProcessMethods:
    def __init__(self, setup: DataPersistSetup):
        self.setup = setup

    def average_readings(self, now, data):
        if not isinstance(data, Collection):
            return data
        return Reading(timestamp=int(sum(r.timestamp for r in data)/len(data)),
                       reading=sum(r.reading for r in data)/len(data),
                       label=self.setup.label, units=self.setup.units)


class CachedDataTransferController:
    def __init__(self, logger, cache: MemoryCache, repository: IDatabaseRepository):
        self.logger = logger
        self.cache = cache
        self.repository = repository
        self.__must_commit = False

        self.setups: dict[str, DataPersistSetup] = {}
        self.scheduler = ScheduledController()

    def set(self, setup: DataPersistSetup):
        if setup.label in self.setups:
            return
        self.setups[setup.label] = setup
        self.scheduler.set(self._make_method(setup), setup.period)

    async def process(self):
        now = datetime.now().timestamp()
        await self.scheduler.process(now)
        if self.__must_commit:
            self.__must_commit = False
            try:
                self.repository.commit()
            except IntegrityError as e:
                await a_logger.warning(f"{self.__class__.__name__} EXCEPTION: {e}")

    def _make_method(self, setup: DataPersistSetup):
        async def _a__inner(now, setup):
            since = now - setup.period
            label = setup.label
            data = await self._retrieve(label, since, self.cache)
            if not data:
                return
            processed = setup.aggregation(now, data)
            if not isinstance(processed, Iterable):
                processed = [processed]
            for reading in processed:
                self.repository.insert_reading(reading)
            if processed:
                self.__must_commit = True
        return partial(_a__inner, setup=setup)

    @staticmethod
    async def _retrieve(label, since, cache: MemoryCache):
        data: list[Reading] = cache.get_last_reading_for_label(label, since=since)
        if not data:
            return None
        return data
