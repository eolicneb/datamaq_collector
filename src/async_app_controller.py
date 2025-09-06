import asyncio
import signal
import platform
from concurrent.futures.thread import ThreadPoolExecutor
from time import time
from traceback import format_exc
from typing import Awaitable, Callable, Coroutine, Union

from logger import logger, AsyncLoggerWrapper
from src.utils.logging.decorators import a_handle_errors, a_log_execution
from src.utils.running import unblocked_task, unblocker

AsyncFuncType = Callable[[], Union[Awaitable, Coroutine]]


class AsyncAppController:
    def __init__(self, process_method: AsyncFuncType, period:float = 0,
                 executor: ThreadPoolExecutor = None, max_workers=10):
        self.process_method = process_method
        self.period = period

        self._running = True
        self._next_operation: float = 0
        self._executor = executor or ThreadPoolExecutor(max_workers=max_workers)
        self.logger = AsyncLoggerWrapper(logger, self._executor)

    def setup_signal_handlers(self):
        """Configura los manejadores de señales para el sistema operativo actual."""
        current_os = platform.system()
        logger.info(f"Sistema operativo detectado: {current_os}")
        logger.debug(f"Sistema operativo detectado: {current_os}") # para testerar el nivel de debug
        if current_os != "Windows":
            logger.info("Configurando manejadores de señales para sistema Unix")
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        else:
            logger.info("Sistema Windows detectado, se manejará mediante KeyboardInterrupt")

    def _handle_signal(self, signum, _frame):
        """ Manejador de señales para SIGINT y SIG"""
        logger.warning(f"Señal {signum} recibida. Terminando el bucle principal...")
        self._running = False

    @a_handle_errors()
    # @a_log_execution()
    async def _execute_main_operations(self):
        try:
            return await self.process_method()
        except Exception as e:
            await asyncio.gather(self.logger.warning(e),
                                 self.logger.debug(format_exc()))

    async def run(self):
        """Ejecuta el ciclo principal de la aplicación."""
        self.setup_signal_handlers()
        self._next_operation = time()
        try:
            await self.logger.info("Iniciando bucle principal")
            # input("Presione Enter para comenzar el bucle principal...")
            while self._running:
                now = time()
                if now < self._next_operation:
                    continue
                await asyncio.gather(self._set_next(now),
                                     self._execute_main_operations())

        except KeyboardInterrupt:
            await self.logger.info("Interrupción (Ctrl+C) recibida. Terminando el bucle principal...")

    async def _set_next(self, now):
        over_timed, lost_steps = False, 0
        while self._next_operation < now:
            if over_timed:
                lost_steps += 1
            self._next_operation += self.period
            over_timed = True
        if lost_steps:
            await self.logger.warning(f"{self.__class__.__name__} lost {lost_steps} steps")
