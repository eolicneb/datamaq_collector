from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Union


@dataclass
class Reading:
    timestamp: int = None
    label: str = None
    reading: Any = None
    units: str = None


class ReadingCache(ABC):
    @abstractmethod
    def save_reading(self, reading: Reading):
        """Stores de reading"""

    @abstractmethod
    def get_last_reading_for_label(self, label: str, count=None, since=None) -> Union[Reading, list[Reading]] | None:
        """Returns the last reading stored for a label"""
