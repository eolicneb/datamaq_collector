from datetime import datetime, UTC
from functools import partial

import aiohttp
from typing import ClassVar, Callable
from dataclasses import dataclass, field

from src.logger import logger
from src.domain.reading import ReadingCache, Reading
from src.utils.logging.decorators import a_handle_errors
from src.utils.scheduler import ScheduledController


@dataclass
class RestObjectField:
    name: str = None
    type: type | Callable = float
    units: str = None


@dataclass
class RestObject:
    name: ClassVar[str] = None
    fields: ClassVar[list[RestObjectField]]
    data: dict = field(default_factory=dict)

    _fields_dict: dict[str, RestObjectField] = None

    def __post_init__(self):
        self._fields_dict = {f.name: f for f in self.fields}

    @property
    def field_labels(self):
        return [f.name for f in self.fields]

    def __getitem__(self, item):
        f = self._fields_dict.get(item)
        data = self.data.get(item)
        if not f or not data:
            return
        return Reading(label=f'{self.name}_{f.name}', reading=f.type(data), units=f.units)


@dataclass
class RestRequestSetup:
    uri: str = None
    headers: dict = None
    params: dict = None
    data: dict = None
    json: dict = None
    timeout: int = None


@dataclass
class RestObjectSetup:
    name: str = None
    request: RestRequestSetup = None
    object_class: type(RestObject)= None
    period: float = None


async def fetch_json(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as response:
            return await response.json()


class RestRequestException(Exception):
    """Exception when fetching a rest request"""


async def fetch_object(now, request: RestObjectSetup) -> RestObject:
    try:
        logger.debug(f"Fetching rest object {request.name} in {request.request.uri}")
        json = await fetch_json(request.request.uri)
        return request.object_class(data=json)
    except Exception as e:
        raise RestRequestException(f"Error fetching rest object {request.name}: <{type(e)}> {e}")


class RestClient:
    def __init__(self, cache: ReadingCache = None):
        self.cache = cache
        self.scheduler = ScheduledController()

    @a_handle_errors()
    async def process(self):
        now = datetime.now(UTC).timestamp()
        await self.scheduler.process(now)

    @staticmethod
    async def process_request(now, request: RestObjectSetup, cache: ReadingCache):
        obj = await fetch_object(now, request)
        logger.info(f"Fetched rest object {request.name}: {obj}")
        for field_ in obj.field_labels:
            reading = obj[field_]
            if reading is None:
                continue
            reading.timestamp = now
            cache.save_reading(reading)

    def book_up_request(self, request: RestObjectSetup):
        self.scheduler.set(partial(self.process_request,
                                   request=request,
                                   cache=self.cache),
                           period=request.period,
                           label=f"rest-{request.name}")
