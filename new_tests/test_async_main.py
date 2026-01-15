import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from src.logger import a_logger
from src.async_app_controller import AsyncAppController
from src.async_main import MainApplication
from src.data_persist_controller import DataPersistSetup, CachedDataTransferController
from src.infrastructure.data_cache import MemoryCache
from src.infrastructure.db_operations import SQLAlchemyDatabaseRepository
from src.modbus_processor import ModbusConnectionManager, ModbusDevice, ModbusScanner, ModbusReadingSetup, \
    ModbusReadAddress


def test_main():
    executor = ThreadPoolExecutor(max_workers=10)
    a_logger.set_executor(executor)

    conn_manager = ModbusConnectionManager(a_logger)
    device = ModbusDevice(conn_manager, a_logger)
    cache = MemoryCache(max_readings=50)
    modbus = ModbusScanner(device, cache)
    get_setup_0 = ModbusReadingSetup(read_address=ModbusReadAddress(address=22, bytes_count=2),
                                     name="counter_0", period=1)
    get_setup_1 = ModbusReadingSetup(read_address=ModbusReadAddress(address=24, bytes_count=2),
                                     name="counter_1", period=.2)
    modbus.book_up_reading(get_setup_0)
    modbus.book_up_reading(get_setup_1)

    repo = SQLAlchemyDatabaseRepository()
    transfer = CachedDataTransferController(a_logger, cache, repo)
    put_setup_0 = DataPersistSetup(label="counter_0", period=3, method="average_readings")
    put_setup_1 = DataPersistSetup(label="counter_1", period=1, method="average_readings")
    transfer.set(put_setup_0)
    transfer.set(put_setup_1)

    class FailAtNTimes:
        def __init__(self, fail_delay_times: int):
            self.count: int = 0
            self.times: int = fail_delay_times

        async def fail_at(self):
            if self.count >= self.times:
                raise KeyboardInterrupt
            self.count += 1

    fail_delay = FailAtNTimes(100)

    async def process():
        await asyncio.gather(modbus.process(), transfer.process(), fail_delay.fail_at())  # fail_at(3),
        # await unblocker(modbus.process, executor=executor)
        # logger.warning(f"Reading: {get_setup_0.name} = {cache.get_last_reading_for_label(get_setup_0.name)}")
        # logger.info("Process finished")
        return

    logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
    controller = AsyncAppController(process, period=.1, executor=executor)
    try:
        MainApplication(controller).run()
    except KeyboardInterrupt:
        print("Terminated")
