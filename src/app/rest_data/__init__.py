from src.data_persist_controller import CachedDataTransferController, DataPersistSetup
from src.rest_client import *


# Edge
@dataclass
class RestEdge(RestObject):
    name = "edge"
    fields = [RestObjectField(name="position", type=int, units="px")]


# Buttler
def ints_list(data: str) -> list[int]:
    return [int(x) for x in data.split(",")]


class RestButtler(RestObject):
    name = "buttler"
    fields = [RestObjectField(name="diameter", type=int, units="px"),
              RestObjectField(name="width", type=int, units="px"),
              RestObjectField(name="height", type=ints_list, units="px")]


def create_rest_client(cache: ReadingCache):
    edge_setup = RestObjectSetup(
        name="edge",
        request=RestRequestSetup(uri="http://localhost:5001/edge"),
        object_class=RestEdge,
        period=0.5,
    )
    buttler_setup = RestObjectSetup(
        name="buttler",
        request=RestRequestSetup(uri="http://localhost:5000/reel"),
        object_class=RestButtler,
        period=5,
    )
    rest_client = RestClient(cache)
    rest_client.book_up_request(edge_setup)
    rest_client.book_up_request(buttler_setup)
    return rest_client


def set_rest_client_transfer(transfer: CachedDataTransferController):
    transfer.set(DataPersistSetup(label="edge_position", period=5, method="average_readings", units="px"))
    transfer.set(DataPersistSetup(label="buttler_diameter", period=5, method="average_readings", units="px"))
    transfer.set(DataPersistSetup(label="buttler_width", period=5, method="average_readings", units="px"))


if __name__ == "__main__":
    from src.infrastructure.data_cache import MemoryCache
    import asyncio
    from logger import logger

    logger.setLevel("DEBUG")

    cache = MemoryCache(max_readings=5)
    rest_client = create_rest_client(cache)
    asyncio.run(rest_client.process())
    print(cache.get_last_reading_for_label("edge_position"))
    print(cache.get_last_reading_for_label("buttler_diameter"))
    print(cache.get_last_reading_for_label("buttler_width"))
