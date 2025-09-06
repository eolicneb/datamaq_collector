"""
Test unitario: ModbusProcessor funciona con mocks de sus dependencias.
"""
import pytest  # pylint: disable=import-error
from src.modbus_processor import ModbusProcessor

class MockModbusDevice:
    def read_digital_input(self, address):
        return 1 if address == 70 else 0
    def read_register(self, register, functioncode=3):
        return 1234

class MockRepository:
    def __init__(self):
        self.actualizaciones = []
    def actualizar_registro(self, query, params):
        self.actualizaciones.append((query, params))

class MockLogger:
    def info(self, msg): pass
    def error(self, msg): pass

@pytest.fixture
def processor():
    device = MockModbusDevice()
    repo = MockRepository()
    logger = MockLogger()
    return ModbusProcessor(repo, logger, device), repo

def test_process_digital_inputs(processor):
    proc, repo = processor
    proc.process_digital_inputs()
    assert len(repo.actualizaciones) == 2
    for query, params in repo.actualizaciones:
        assert "UPDATE registros_modbus" in query
        assert "direccion" in params
        assert "valor" in params

def test_process_high_resolution_registers(processor):
    proc, repo = processor
    proc.process_high_resolution_registers()
    assert len(repo.actualizaciones) == 4
    for query, params in repo.actualizaciones:
        assert params["valor"] == 1234
