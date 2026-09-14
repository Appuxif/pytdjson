import asyncio
import threading
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from telegram.mcp.runtime import TelegramRuntime, _create_mcp_client


class LoopStub:
    def call_soon_threadsafe(self, callback):
        callback()


class ClientStub:
    def __init__(self):
        self.is_enabled = False
        self._loop = LoopStub()
        self.login_thread = None
        self._stopped = threading.Event()

    def login(self, timeout):
        self.login_thread = threading.get_ident()
        return True

    def run(self):
        self.is_enabled = True
        self._stopped.wait()
        self.is_enabled = False

    def kill(self):
        self._stopped.set()


class RuntimeTestCase(TestCase):
    @patch('telegram.mcp.runtime.AsyncTelegram')
    def test_mcp_client_does_not_replace_process_signal_handlers(self, client_class):
        settings = SimpleNamespace()

        _create_mcp_client(settings)

        client_class.assert_called_once_with(settings, install_signal_handlers=False)

    def test_login_runs_outside_the_mcp_event_loop(self):
        client = ClientStub()
        main_thread = threading.get_ident()
        ready = []

        async def start_and_stop():
            runtime = TelegramRuntime(
                SimpleNamespace(),
                client_factory=lambda _settings: client,
                on_ready=lambda: ready.append(True),
            )
            await runtime.start()
            await runtime.stop()

        asyncio.run(start_and_stop())

        self.assertNotEqual(main_thread, client.login_thread)
        self.assertEqual([True], ready)
