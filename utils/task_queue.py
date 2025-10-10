# task_queue.py
import asyncio
from typing import Any, Awaitable, Callable, Optional, List

_queue: Optional[asyncio.Queue] = None
_workers: List[asyncio.Task] = []
_workers_started = False

async def _worker():
    while True:
        func, args, kwargs, fut = await _queue.get()
        try:
            res = await func(*args, **kwargs)
            if not fut.cancelled():
                fut.set_result(res)
        except Exception as e:
            if not fut.cancelled():
                fut.set_exception(e)
        finally:
            _queue.task_done()

async def start_task_queue(max_concurrency: int = 1) -> None:
    """
    Асинхронный запуск очереди.
    max_concurrency=1 — строго по очереди; >1 — ограниченный параллелизм.
    Идемпотентно: повторный вызов ничего не сломает.
    """
    global _queue, _workers_started, _workers
    if _workers_started:
        return
    _queue = asyncio.Queue()
    for _ in range(max_concurrency):
        _workers.append(asyncio.create_task(_worker()))
    _workers_started = True
    await asyncio.sleep(0)

async def enqueue(func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
    """
    Поставить корутину в очередь и дождаться результата.
    """
    if not _workers_started:
        # ленивый старт на 1 воркера, если забыли вызвать start_task_queue()
        await start_task_queue(1)
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    await _queue.put((func, args, kwargs, fut))
    return await fut
