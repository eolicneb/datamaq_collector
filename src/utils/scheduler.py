import asyncio
from time import time
from dataclasses import dataclass
from collections import OrderedDict
from typing import Callable, Tuple, Union, Optional
from uuid import uuid4

from src.utils.logging.decorators import a_handle_errors, a_log_execution


@dataclass
class Schedule:
    label: str
    period: float = None
    last: float = None
    next: float = None
    lost_steps: int = 0

    def is_time(self, now: float):
        if self.next is None or now > self.next:
            self._set_next(now)
            self.last = now
            return True
        return False

    def _set_next(self, now):
        self.lost_steps = 0
        if self.next is None:
            self.last = now
            self.next = now + self.period or 0
        over_timed = False
        while self.next < now:
            if over_timed:
                self.lost_steps += 1
            self.next = (self.next + self.period) if self.period else now
            over_timed = True

    def __hash__(self):
        return hash(self.label + str(self.period))

    def __eq__(self, other):
        return self.__hash__() == hash(other)


class ScheduledController:
    def __init__(self, *setups: Tuple[Callable, Optional[Union[Tuple[str, float], Schedule, float]]]):
        self._scheduled = OrderedDict()
        for params in setups:
            if len(params) == 1:
                params = params, None
            method, schedule = params
            if not isinstance(schedule, Schedule):
                if isinstance(schedule, float):
                    label, period = uuid4().hex, schedule
                else:
                    label, period = schedule
                schedule = Schedule(label=label, period=period)
            self._scheduled[schedule] = method

    def set(self, process_callable: Callable, period: float = None, label: str = None):
        label = label or uuid4().hex
        if label in self._scheduled:
            raise ValueError(f"Label {label} already scheduled")
        schedule = Schedule(label=label, period=period)
        self._scheduled[schedule] = process_callable

    @a_handle_errors()
    @a_log_execution()
    async def process(self, now):
        tasks = []
        for schedule, method in self._scheduled.items():
            if schedule.is_time(now):
                tasks.append(method(now))
        await asyncio.gather(*tasks)
