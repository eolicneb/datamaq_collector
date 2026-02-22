from src.data_persist_controller import DataPersistSetup
from src.modbus_processor import ModbusConnectionManager, ModbusDevice, ModbusScanner, ModbusReadingSetup, \
    ModbusReadAddress


def create_modbus_client(a_logger, cache):
    conn_manager = ModbusConnectionManager(a_logger)
    device = ModbusDevice(conn_manager, a_logger)
    modbus = ModbusScanner(device, cache)
    get_setup = ModbusReadingSetup(read_address=ModbusReadAddress(address=22, bytes_count=2),
                                   name="vel_upm", period=0.2)
    modbus.book_up_reading(get_setup)
    return modbus


def set_modbus_client_transfer(transfer):
    put_setup = DataPersistSetup(label="vel_upm", period=5, method="average_readings", units="unidades/min")
    transfer.set(put_setup)
