import asyncio
import logging
import queue
import threading
from typing import Any, Callable

import esd


logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class SofascoreWorker:
    def __init__(self):
        self._task_queue: queue.Queue = queue.Queue()
        self._ready = threading.Event()
        self._init_error: BaseException | None = None
        self._client = None
        self._thread = threading.Thread(
            target=self._run,
            name='sofascore-worker',
            daemon=True,
        )
        self._thread.start()

        if not self._ready.wait(timeout=120):
            raise TimeoutError('Sofascore worker не запустился за 120 с')

        if self._init_error is not None:
            raise self._init_error

    def _run(self):
        asyncio.set_event_loop(None)

        try:
            self._client = esd.SofascoreClient()
        except Exception as exc:
            self._init_error = exc
            self._ready.set()
            logger.exception('Не удалось инициализировать SofascoreClient')
            return

        self._ready.set()
        logger.info('Sofascore worker запущен')

        while True:
            task = self._task_queue.get()

            if task is _SHUTDOWN:
                break

            func, args, kwargs, result_queue = task

            try:
                result = func(self._client, *args, **kwargs)
                result_queue.put((True, result))
            except Exception as exc:
                result_queue.put((False, exc))

        if self._client is not None and hasattr(self._client, 'close'):
            try:
                self._client.close()
            except Exception:
                logger.exception('Ошибка при закрытии SofascoreClient')

        logger.info('Sofascore worker остановлен')

    def run(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        if self._init_error is not None:
            raise self._init_error

        result_queue: queue.Queue = queue.Queue(maxsize=1)
        self._task_queue.put((func, args, kwargs, result_queue))
        ok, value = result_queue.get()

        if ok:
            return value

        raise value

    def shutdown(self):
        if not self._thread.is_alive():
            return

        self._task_queue.put(_SHUTDOWN)
        self._thread.join(timeout=30)


_worker: SofascoreWorker | None = None
_worker_lock = threading.Lock()


def get_sofascore_worker() -> SofascoreWorker:
    global _worker

    if _worker is None:
        with _worker_lock:
            if _worker is None:
                _worker = SofascoreWorker()

    return _worker


def run_in_playwright_thread(func: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Выполняет func(client, *args, **kwargs) в dedicated-потоке с одним SofascoreClient.
    """
    return get_sofascore_worker().run(func, *args, **kwargs)


def shutdown_sofascore_worker():
    global _worker

    with _worker_lock:
        if _worker is None:
            return

        _worker.shutdown()
        _worker = None
