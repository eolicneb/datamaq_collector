from src.async_main import *

executor = ThreadPoolExecutor(max_workers=10)
a_logger.set_executor(executor)

conn_manager = ModbusConnectionManager(a_logger)
device = ModbusDevice(conn_manager, a_logger)
cache = MemoryCache(max_readings=5)
modbus = ModbusScanner(device, cache)
get_setup = ModbusReadingSetup(read_address=ModbusReadAddress(address=22, bytes_count=2),
                               name="vel_upm", period=0.2)
modbus.book_up_reading(get_setup)

put_setup = DataPersistSetup(label="vel_upm", period=5, method="average_readings", units="unidades/min")
repo = SQLAlchemyDatabaseRepository()
transfer = CachedDataTransferController(a_logger, cache, repo)
transfer.set(put_setup)

rest_client = create_rest_client(cache)
set_rest_client_transfer(transfer)


async def fail_at(delay: float = 10):
    await asyncio.sleep(delay)
    # raise RuntimeError("Failed!")


async def process():
    # await asyncio.sleep(.01)
    await asyncio.gather(modbus.process(), rest_client.process(), transfer.process())  # fail_at(3),
    # await unblocker(modbus.process, executor=executor)
    # logger.warning(f"Reading: {get_setup.name} = {cache.get_last_reading_for_label(get_setup.name)}")
    # logger.info("Process finished")
    return


controller = AsyncAppController(process, period=.01, executor=executor)
main = MainApplication(controller)
main.run()