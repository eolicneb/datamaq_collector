import sys
import logging
from concurrent.futures import ThreadPoolExecutor

from src.utils.running import unblocker

logger = logging.getLogger("datamaq")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

file_handler = logging.FileHandler('salame.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
logger.addHandler(file_handler)


class AsyncLoggerWrapper:
    def __init__(self, logger, executor: ThreadPoolExecutor = None):
        self.__logger = logger
        self.__executor = executor

    def __getattr__(self, level):
        if level not in ('debug', 'info', 'warning', 'error', 'critical'):
            return super().__getattribute__(level)
        async def __inner(*args):
            await unblocker(getattr(self.__logger, level), *args)
        return __inner

    def set_executor(self, executor):
        self.__executor = executor

a_logger = AsyncLoggerWrapper(logger)
