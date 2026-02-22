from src.app.modbus_data import create_modbus_client, set_modbus_client_transfer
from src.async_main import *

# The executor keeps controlled the count of threads that the service will handle
executor = ThreadPoolExecutor(max_workers=10)
a_logger.set_executor(executor)

cache = MemoryCache(max_readings=5)
repo = SQLAlchemyDatabaseRepository()
transfer = CachedDataTransferController(a_logger, cache, repo)

modbus = create_modbus_client(a_logger, cache)
set_modbus_client_transfer(transfer)

rest_client = create_rest_client(cache)
set_rest_client_transfer(transfer)


async def fail_at(delay: float = 10):
    await asyncio.sleep(delay)
    # raise RuntimeError("Failed!")


async def process():
    await asyncio.gather(modbus.process(), rest_client.process(), transfer.process())  # fail_at(3),
    return


controller = AsyncAppController(process, period=.01, executor=executor)
main = MainApplication(controller)
main.run()