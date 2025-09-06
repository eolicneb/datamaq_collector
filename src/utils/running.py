import asyncio
from concurrent.futures import ThreadPoolExecutor


async def unblocker(blocking_method, *args, executor: ThreadPoolExecutor = None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, blocking_method, *args)


async def unblocked_task(blocking_method, *args, executor: ThreadPoolExecutor = None):
    return asyncio.create_task(unblocker(blocking_method, *args, executor=executor))
