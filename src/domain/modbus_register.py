"""
Entidad de dominio: ModbusRegister
Representa un registro Modbus con dirección, valor y metadatos opcionales.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModbusRegister:
    address: int
    value: Optional[int] = None
    description: Optional[str] = None
    unit: Optional[str] = None
