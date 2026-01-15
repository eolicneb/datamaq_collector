"""
Path: src/db_operations.py
Este módulo se encarga de realizar operaciones de lectura y escritura en la base de datos.
"""
from collections.abc import Iterable
from dataclasses import asdict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing_extensions import TypeVar

from src.logger import logger
from src import settings
from src.application.interfaces import IDatabaseRepository
from src.domain.modbus_register import ModbusRegister
from src.domain.reading import Reading

from . import models

_T = TypeVar('reading_model', default=Reading)


class SQLAlchemyDatabaseRepository(IDatabaseRepository):
    """Implementación de la interfaz IDatabaseRepository utilizando SQLAlchemy."""

    def __init__(self):
        # Inicializa el engine y la sesión utilizando la configuración definida
        self.engine = self.obtener_engine()
        self.session_local = sessionmaker(bind=self.engine)
        self.session = self.session_local()

    def get_db_config(self):
        """
        Obtiene la configuración de la base de datos desde variables de entorno o parámetros.
        
        Returns:
            dict: Un diccionario con la configuración de la base de datos.
        """
        try:
            return {
                'host': settings.DB_HOST,
                'user': settings.DB_USER,
                'password': settings.DB_PASSWORD,
                'port': settings.DB_PORT,
                'db': settings.DB_NAME,
            }
        except Exception as e:
            logger.error(f"Error al obtener la configuración de la base de datos: {e}")
            raise e

    def obtener_engine(self) -> any:
        """
        Retorna el objeto engine de SQLAlchemy configurado para la conexión a la base de datos.
        """
        try:
            config = self.get_db_config()
            conn_str = (
                f"mysql+pymysql://{config['user']}:{config['password']}@"
                f"{config['host']}:{config['port']}/{config['db']}"
            )
            engine = create_engine(conn_str, pool_pre_ping=True)
            return engine
        except Exception as e:
            logger.error(f"Error al obtener el engine de SQLAlchemy: {e}")
            raise e

    def raw_connection(self):
        """
        Retorna una conexión en bruto (DBAPI connection) desde el engine.
        Esto permite compatibilidad con código legado que utiliza métodos de cursor.
        """
        try:
            return self.engine.raw_connection()
        except Exception as e:
            logger.error(f"Error al obtener una conexión raw desde el engine: {e}")
            raise DatabaseConnectionError(f"Error al conectar con la base de datos: {e}") from e

    def ejecutar_consulta(self, consulta: str, parametros: dict) -> any:
        """
        Ejecuta una consulta de lectura (SELECT) y retorna los resultados.
        """
        try:
            result = self.session.execute(text(consulta), parametros)
            rows = result.fetchall()
            return rows
        except Exception as e:
            logger.error(
                f"Error ejecutando consulta: {consulta} con parámetros {parametros}. Error: {e}"
            )
            self.session.rollback()
            raise e

    def actualizar_registro(self, register: ModbusRegister) -> None:

        def _build_update_query(address: int, value):
            """
            Construye la consulta SQL para actualizar el registro.
            """
            query = "UPDATE registros_modbus SET valor = :valor WHERE direccion_modbus = :direccion"
            params = {'valor': value, 'direccion': address}
            return query, params

        try:
            with self.session.begin():
                query, params = _build_update_query(register.address, register.value)
                self.session.execute(text(query), params)
                logger.info(
                    f"Actualización exitosa con consulta: {query} y parámetros: {params}"
                )
        except Exception as e:
            logger.error(
                f"Error actualizando registro con consulta: {query} y "
                f"parámetros: {params}. Error: {e}"
            )
            raise DatabaseUpdateError(f"Error al actualizar la base de datos: {e}") from e

    def insertar_lote(self, consulta: str, lista_parametros: list) -> None:
        """
        Realiza inserciones en lote (batch insert) de manera transaccional.
        """
        try:
            self.session.execute(text(consulta), lista_parametros)
            self.session.commit()
            logger.info(f"Inserción en lote exitosa con consulta: {consulta}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error insertando lote con consulta: {consulta}. Error: {e}")
            raise e

    def commit(self) -> None:
        """
        Confirma la transacción actual.
        """
        try:
            self.session.commit()
        except Exception as e:
            logger.error(f"Error al hacer commit: {e}")
            self.session.rollback()
            raise e

    def rollback(self) -> None:
        """
        Revierte la transacción actual.
        """
        self.session.rollback()

    def cerrar_conexion(self) -> None:
        """
        Cierra la sesión y la conexión de la base de datos.
        """
        self.session.close()
        self.engine.dispose()
        logger.info("Conexión cerrada exitosamente")

    def insert_reading(self, reading: Reading):
        try:
            with self.session.begin():
                new_reading = models.Reading(**asdict(reading))
                self.session.add(new_reading)
                logger.info(f"Inserción exitosa de reading: {reading}")
        except Exception as e:
            logger.error(
                f"Error insertando reading: {reading}. Error: {e}"
            )
            raise DatabaseUpdateError(f"Error al actualizar la base de datos: {e}") from e

    def get_reading(self, label: str, id: int = None, limit: int = None, offset: int = None, since: float = None):
        try:
            with self.session.begin():
                _filters = [models.Reading.label == label]
                if id:
                    _filters.append(models.Reading.id == id)
                if since:
                    _filters.append(models.Reading.timestamp >= since)
                readings = self.session.query(models.Reading).filter(*_filters).order_by(models.Reading.id.desc())
                if limit or offset:
                    offset = offset or 0
                    _end = limit and (limit + offset)
                    _slice = slice(offset, _end)
                    yield from self._to_reading(readings[_slice])
                else:
                    yield from self._to_reading(readings.all())
        except Exception as e:
            logger.error(f"Error leyendo readings for label '{label}': id={id}, limit={limit}, offset={offset}, since={since}\n{e}")
            return None

    def _to_reading(self, db_readings: Iterable[type[models.Reading]]) -> Iterable[Reading]:
        fields = Reading.__match_args__
        for db_reading in db_readings:
            yield Reading(**{f: getattr(db_reading, f) for f in fields})


class DatabaseUpdateError(Exception):
    """Excepción para errores en la actualización de la base de datos."""


class DatabaseConnectionError(Exception):
    """Excepción para errores en la conexión a la base de datos."""
