"""
Path: src/interfaces.py
Este script define la interfaz de la clase DatabaseRepository.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict

from src.domain.modbus_register import ModbusRegister
from src.domain.reading import Reading


class IDatabaseRepository(ABC):
    """Interfaz para la clase DatabaseRepository."""
    @abstractmethod
    def actualizar_registro(self, register: ModbusRegister) -> None:
        """Ejecuta una consulta de actualización de un registro de Modbus."""

    @abstractmethod
    def insert_reading(self, reading: Reading) -> None:
        """Inserta una lectura de tipo Reading"""

    @abstractmethod
    def commit(self):
        """Persiste los cambios"""


class IModbusConnectionManager(ABC):
    """Puerto para la gestión de conexiones Modbus (descubrimiento, apertura, cierre)."""
    @abstractmethod
    def detectar_dispositivos(self) -> list:
        """Detecta dispositivos Modbus disponibles en el entorno."""

    @abstractmethod
    def abrir_conexion(self, direccion: str) -> Any:
        """Abre una conexión Modbus con la dirección especificada."""

    @abstractmethod
    def cerrar_conexion(self, conexion: Any) -> None:
        """Cierra la conexión Modbus proporcionada."""


class IModbusDevice(ABC):
    """Puerto para operaciones sobre un dispositivo Modbus."""
    @abstractmethod
    def leer_registro(self, direccion: int) -> int:
        """Lee el valor de un registro Modbus."""

    @abstractmethod
    def escribir_registro(self, direccion: int, valor: int) -> None:
        """Escribe un valor en un registro Modbus."""


class IModbusProcessor(ABC):
    """Puerto para el procesamiento de datos Modbus (aplicación de lógica de negocio sobre lecturas)."""
    @abstractmethod
    def procesar_datos(self, datos: dict) -> dict:
        """Procesa los datos leídos de un dispositivo Modbus y retorna el resultado."""


class IDataCache(ABC):
    """"""
