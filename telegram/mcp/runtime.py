"""Thread bridge between MCP's event loop and AsyncTelegram."""
import asyncio
import threading
from typing import Any, Callable, Optional

from telegram.client import AsyncTelegram, Settings


class TelegramMCPError(RuntimeError):
    """A safe error suitable for returning to an MCP client."""


def _create_mcp_client(settings: Settings) -> AsyncTelegram:
    """Create a client without replacing the MCP process signal handlers."""
    return AsyncTelegram(settings, install_signal_handlers=False)


class TelegramRuntime:
    def __init__(
        self,
        settings: Settings,
        client_factory: Callable[[Settings], AsyncTelegram] = _create_mcp_client,
        on_ready: Optional[Callable[[], None]] = None,
    ) -> None:
        self.settings = settings
        self.client_factory = client_factory
        self.on_ready = on_ready
        self.client: Optional[AsyncTelegram] = None
        self.thread: Optional[threading.Thread] = None

    async def start(self) -> None:
        self.client = self.client_factory(self.settings)
        try:
            # AsyncTelegram owns and drives a separate event loop.  Calling its
            # blocking login method from MCP's running asyncio loop raises
            # "Cannot run the event loop while another loop is running".
            await asyncio.to_thread(self.client.login, timeout=10)
        except Exception as error:
            raise TelegramMCPError(
                'Telegram authorization is incomplete; run `pytdjson-mcp login`.'
            ) from error

        def run_client() -> None:
            assert self.client is not None
            self.client.run()

        self.thread = threading.Thread(target=run_client, daemon=True)
        self.thread.start()
        for _ in range(50):
            if self.client.is_enabled:
                break
            await asyncio.sleep(0.1)
        else:
            raise TelegramMCPError('TDLib client failed to start')
        if self.on_ready:
            self.on_ready()

    async def call(self, method: str, *args: Any, **kwargs: Any) -> dict:
        if not self.client or not self.client.is_enabled:
            raise TelegramMCPError('TDLib client is not running')
        coroutine = getattr(self.client.api, method)(*args, **kwargs)
        future = asyncio.run_coroutine_threadsafe(coroutine, self.client._loop)
        result = await asyncio.wrap_future(future)
        if result.update is None:
            raise TelegramMCPError('TDLib returned no response')
        if result.error_received:
            raise TelegramMCPError(
                result.update.get('message', 'Telegram request failed')
            )
        return result.update

    async def stop(self) -> None:
        if not self.client:
            return
        if self.client.is_enabled:
            self.client._loop.call_soon_threadsafe(self.client.kill)
        if self.thread:
            await asyncio.to_thread(self.thread.join, 5)
        self.client = None
