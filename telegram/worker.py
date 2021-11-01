import logging
import threading
from queue import Queue

logger = logging.getLogger(__name__)


class BaseWorker:
    """
    Base worker class.
    Each worker must implement the run method to start listening to the queue
    and calling handler functions
    """

    def __init__(self, queue_size: int = 1000):

        self._queue = Queue(maxsize=queue_size)
        self._is_enabled = True

    def run(self) -> None:
        raise NotImplementedError()

    def stop(self):
        self._is_enabled = False

    def put(self, item, timeout):
        self._queue.put(item, timeout=timeout)


class SimpleWorker(BaseWorker):
    """Simple one-thread worker"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread = None

    def run(self) -> None:
        self._is_enabled = True
        self._thread = threading.Thread(
            target=self._run_thread,
            daemon=True,
        )
        self._thread.start()

    def _run_thread(self) -> None:
        while self._is_enabled:
            handler, update = self._queue.get()
            handler(update)
            self._queue.task_done()

    def stop(self):
        super().stop()
        self._thread.join()
