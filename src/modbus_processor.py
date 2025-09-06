"""
Path: src/core/modbus_processor.py
Este módulo se encarga de procesar las operaciones Modbus siguiendo principios SOLID y POO.
"""
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from functools import partial

import minimalmodbus  # pylint: disable=import-error
import serial.tools.list_ports  # pylint: disable=import-error
from serial_controller import get_com_ports

from src.domain.modbus_register import ModbusRegister
from src.domain.reading import Reading, ReadingCache
from src.infrastructure.db_operations import DatabaseUpdateError
from src.application.interfaces import IDatabaseRepository
from src.utils.logging.decorators import a_handle_errors, a_log_execution
# from src.utils.logging.dependency_injection import get_logger
from src.utils.scheduler import ScheduledController

# logger = get_logger()


# Excepciones específicas
class ModbusConnectionError(Exception):
    """Excepción para errores de conexión con el dispositivo Modbus."""
    pass


class ModbusReadError(Exception):
    """Excepción para errores de lectura del dispositivo Modbus."""
    pass


class ModbusConnectionManager:
    """
    Encapsula la lógica para detectar y establecer una conexión Modbus.
    """
    def __init__(self, log, device_address=1):
        self.logger = log
        self.device_address = device_address
        self._instrument = None

    @property
    def instrument(self):
        if self._instrument is None:
            self._instrument = self.establish_connection()
        return self._instrument

    def detect_com_port(self, device_description: str):
        """
        Busca y retorna el puerto serie que coincide con la descripción del dispositivo.
        """
        available_ports = get_com_ports()  # list(serial.tools.list_ports.comports())
        for port, desc, _ in available_ports:
            if device_description in desc:
                return port
        return None

    def establish_connection(self) -> minimalmodbus.Instrument:
        """
        Inicializa y establece la conexión Modbus.
        Retorna un objeto minimalmodbus.Instrument.
        """
        # Intentar detectar el dispositivo "DigiRail Connect"
        device_description = "DigiRail Connect"
        com_port = self.detect_com_port(device_description)
        if com_port:
            self.logger.info(f"Puerto {device_description} detectado: {com_port}")
        else:
            # Intentar con "USB-SERIAL CH340"
            device_description = "USB-SERIAL CH340"
            com_port = self.detect_com_port(device_description)
            if com_port:
                self.logger.info(f"Puerto detectado: {com_port}")
            else:
                error_msg = "No se detectaron puertos COM para el dispositivo."
                self.logger.error(error_msg)
                raise ModbusConnectionError(error_msg)

        try:
            instrument = minimalmodbus.Instrument(com_port, self.device_address)
            self.logger.info(
                f"Conexión Modbus establecida en puerto {com_port}, dirección {self.device_address}"
            )
            return instrument
        except minimalmodbus.ModbusException as e:
            error_msg = f"Error al configurar el puerto serie: {e}"
            self.logger.error(error_msg)
            raise ModbusConnectionError(error_msg) from e


@dataclass
class ModbusReadAddress:
    address: int = None
    bytes_count: int = 2


@dataclass
class ModbusReadingSetup:
    read_address: ModbusReadAddress = None
    name: str = None
    period: float = 0


class ModbusDevice:
    """
    Envuelve el objeto minimalmodbus.Instrument y provee métodos seguros para leer datos.
    """
    def __init__(self, connection_manager, device_logger, instrument=None):
        self.connection_manager = connection_manager
        self._instrument = instrument
        self.logger = device_logger

    @property
    def instrument(self):
        if self._instrument is None:
            self._instrument = self.connection_manager.instrument
        return self._instrument

    def safe_read(self, method, *args, __retries__=0, **kwargs):
        """
        Realiza una lectura segura usando el método proporcionado.
        """
        try:
            return method(*args, **kwargs)
        except (serial.SerialException, IOError, ValueError, minimalmodbus.ModbusException) as e:
            self.logger.error(f"Error al leer del dispositivo Modbus: {e}")
            return None

    def read_digital_input(self, address: int):
        """
        Lee el estado de una entrada digital.
        """
        return self.safe_read(self.instrument.read_bit, address, functioncode=2)

    def read_register(self, register: int, functioncode: int = 3):
        """
        Lee el valor de un registro de alta resolución.
        """
        return self.safe_read(self.instrument.read_register, register, functioncode=functioncode)

    def read_modbus_address(self, read_address: ModbusReadAddress, functioncode: int = 3):
        addres, count = read_address.address, read_address.bytes_count
        reading = 0
        for offset in range(count):
            reading += (self.read_register(addres + offset, functioncode) or 0) * 8**offset
        return reading


class ModbusScanner:
    def __init__(self, device_reader, cache: ReadingCache):
        self.reader: ModbusDevice = device_reader
        self.cache = cache
        self.scheduler = ScheduledController()

    @a_handle_errors()
    # @a_log_execution()
    async def process(self):
        """Iters over registered reading setups to perform the reading and stores it"""
        now = datetime.now(UTC).timestamp()
        await self.scheduler.process(now)

    @staticmethod
    async def process_reading(now, setup, reader, cache):
        value = reader.read_modbus_address(setup.read_address)
        reading = Reading(timestamp=now, label=setup.name, reading=value)
        cache.save_reading(reading)

    def read(self, setup):
        return self.reader.read_modbus_address(setup.read_address)

    def book_up_reading(self, reading_setup: ModbusReadingSetup):
        self.scheduler.set(partial(self.process_reading,
                                   setup=reading_setup,
                                   reader=self.reader,
                                   cache=self.cache),
                           period=reading_setup.period, label=f"modbus-{reading_setup.name}")
