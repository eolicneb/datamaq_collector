"""
Decoradores reutilizables para manejo de errores y logging.
"""
import functools
import inspect
from src.logger import logger as app_logger


def get_logger(logger, args):
    if logger:
        return logger
    return args and getattr(args[0], 'logger', None) or app_logger


def handle_errors(logger=None):
    """Decorador para capturar y loguear excepciones en funciones críticas."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = get_logger(logger, args)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.error(f"Error en {func.__name__}: {e}")
                raise
        return wrapper
    return decorator


def log_execution(logger=None):
    """Decorador para loguear entrada y salida de funciones."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = get_logger(logger, args)
            # log.debug(f"Entrando a {func.__name__}")
            result = func(*args, **kwargs)
            # log.debug(f"Saliendo de {func.__name__}")
            return result
        return wrapper
    return decorator


async def a_log(log_method, *args, **kwargs):
    log_awaitable = log_method(*args, **kwargs)
    if inspect.isawaitable(log_awaitable):
        await log_awaitable


def a_handle_errors(logger=None):
    """Decorador para capturar y loguear excepciones en funciones críticas."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            log = get_logger(logger, args)
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await a_log(log.error, f"Error en {func.__name__}: {e}")
                raise
        return wrapper
    return decorator


def a_log_execution(logger=None):
    """Decorador para loguear entrada y salida de funciones."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            log = get_logger(logger, args)
            await a_log(log.debug, f"Entrando a {func.__name__}")
            result = await func(*args, **kwargs)
            await a_log(log.debug, f"Saliendo de {func.__name__}")
            return result
        return wrapper
    return decorator
