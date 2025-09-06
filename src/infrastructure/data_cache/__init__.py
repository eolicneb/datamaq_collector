from typing import Union

from src.domain.reading import Reading, ReadingCache


class MemoryCache(ReadingCache):
    def __init__(self, max_readings=None):
        self.cache = {}
        self.max_readings = max_readings

    def save_reading(self, reading: Reading):
        if reading.label not in self.cache:
            self.cache[reading.label] = []
        self.cache[reading.label].append(reading)
        if self.max_readings:
            self.cache[reading.label] = self.cache[reading.label][-self.max_readings:]

    def get_last_reading_for_label(self, label: str, count=None, since=None) -> Union[Reading, list[Reading]] | None:
        if label not in self.cache or not self.cache[label]:
            if count or since:
                return []
            return None
        if count:
            if self.max_readings and count > self.max_readings:
                raise ValueError(f"'count' param cannot exceed established max_readings = {self.max_readings}")
            return self.cache[label][-count:]
        if since:
            result = []
            for data in reversed(self.cache[label]):
                if data.timestamp > since:
                    result.insert(0, data)
                else:
                    break
            return result
        return self.cache[label][-1]
