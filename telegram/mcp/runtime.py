"""Thread bridge between MCP's event loop and AsyncTelegram."""
import asyncio
from collections import deque
import threading
from typing import Any, Callable, Deque, Optional

from telegram.client import AsyncTelegram, Settings


class TelegramMCPError(RuntimeError):
    """A safe error suitable for returning to an MCP client."""


class _UpdateBuffer:
    def __init__(self, maxlen: int = 2000) -> None:
        self.maxlen = maxlen
        self.events: Deque[tuple[int, dict]] = deque(maxlen=self.maxlen)
        self.next_sequence = 0
        self.waiters: set[asyncio.Future[None]] = set()

    def add(self, update: dict) -> None:
        self.next_sequence += 1
        self.events.append((self.next_sequence, update))
        for waiter in tuple(self.waiters):
            if not waiter.done():
                waiter.set_result(None)

    @property
    def oldest_cursor(self) -> int:
        if not self.events:
            return self.next_sequence
        return self.events[0][0] - 1

    @property
    def size(self) -> int:
        return len(self.events)

    def remove_chats(self, chat_ids: frozenset[int]) -> None:
        self.events = deque(
            (
                (sequence, update)
                for sequence, update in self.events
                if _update_chat_id(update) not in chat_ids
            ),
            maxlen=self.maxlen,
        )

    def remove_message(self, message_id: int) -> None:
        self.events = deque(
            (
                (sequence, update)
                for sequence, update in self.events
                if _update_message_id(update) != message_id
            ),
            maxlen=self.maxlen,
        )

    def wake_waiters(self) -> None:
        for waiter in tuple(self.waiters):
            if not waiter.done():
                waiter.set_result(None)

    def first_matching(
        self,
        chat_ids: frozenset[int],
        after_sequence: int,
    ) -> Optional[tuple[int, dict]]:
        for sequence, update in self.events:
            if sequence > after_sequence and _update_chat_id(update) in chat_ids:
                return sequence, update
        return None

    def commit(self, cursor: int) -> int:
        if cursor > self.next_sequence:
            raise ValueError('cursor is ahead of the latest update')
        removed = 0
        while self.events and self.events[0][0] <= cursor:
            self.events.popleft()
            removed += 1
        return removed


def _update_chat_id(update: dict) -> Optional[int]:
    if update.get('chat_id') is not None:
        return update['chat_id']
    message = update.get('message') or {}
    if message.get('chat_id') is not None:
        return message['chat_id']
    chat = update.get('chat') or {}
    if chat.get('id') is not None:
        return chat['id']
    return None


def _update_message_id(update: dict) -> Optional[int]:
    return (update.get('message') or {}).get('id')


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
        self._mcp_loop: Optional[asyncio.AbstractEventLoop] = None
        self._updates = _UpdateBuffer()
        self._subscribed_chat_ids: set[int] = set()
        self._ignored_message_ids: set[int] = set()
        self._ignored_message_order: Deque[int] = deque()

    async def start(self) -> None:
        self._mcp_loop = asyncio.get_running_loop()
        self._subscribed_chat_ids.clear()
        self._updates = _UpdateBuffer()
        self._ignored_message_ids.clear()
        self._ignored_message_order.clear()
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

        self.client.add_update_handler('*', self._handle_update)

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

    async def _handle_update(self, update: Any) -> None:
        raw_update = getattr(update, 'raw', update)
        if not isinstance(raw_update, dict) or self._mcp_loop is None:
            return
        self._mcp_loop.call_soon_threadsafe(self._record_update, raw_update)

    def _record_update(self, update: dict) -> None:
        if update.get('@type') != 'updateNewMessage':
            return
        chat_id = _update_chat_id(update)
        if (
            chat_id in self._subscribed_chat_ids
            and _update_message_id(update) not in self._ignored_message_ids
        ):
            self._updates.add(update)

    def _remember_sent_message(self, message_id: int) -> None:
        if message_id in self._ignored_message_ids:
            return
        self._ignored_message_ids.add(message_id)
        self._ignored_message_order.append(message_id)
        if len(self._ignored_message_order) > self._updates.maxlen:
            expired_id = self._ignored_message_order.popleft()
            self._ignored_message_ids.discard(expired_id)
        self._updates.remove_message(message_id)

    async def subscribe_for_updates(self, chat_ids: frozenset[int]) -> dict:
        added_chat_ids = chat_ids - self._subscribed_chat_ids
        self._subscribed_chat_ids.update(chat_ids)
        return {
            'subscribed_chat_ids': sorted(self._subscribed_chat_ids),
            'added_chat_ids': sorted(added_chat_ids),
        }

    async def unsubscribe_from_updates(self, chat_ids: frozenset[int]) -> dict:
        removed_chat_ids = chat_ids & self._subscribed_chat_ids
        self._subscribed_chat_ids.difference_update(chat_ids)
        self._updates.remove_chats(chat_ids)
        return {
            'subscribed_chat_ids': sorted(self._subscribed_chat_ids),
            'removed_chat_ids': sorted(removed_chat_ids),
        }

    def update_subscription(self) -> dict:
        return {
            'subscribed_chat_ids': sorted(self._subscribed_chat_ids),
            'buffer_size': self._updates.size,
            'buffer_limit': self._updates.events.maxlen,
            'oldest_cursor': self._updates.oldest_cursor,
            'next_cursor': self._updates.next_sequence,
        }

    async def poll_updates(
        self,
        timeout: float,
        cursor: Optional[int] = None,
    ) -> tuple[Optional[dict], int, bool, bool]:
        """Wait for new updates from subscribed chats and return a cursor."""
        if not self._subscribed_chat_ids:
            raise ValueError('no update subscriptions configured')

        loop = asyncio.get_running_loop()
        after_sequence = (
            self._updates.oldest_cursor if cursor is None else max(cursor, 0)
        )
        deadline = loop.time() + timeout
        subscribed_chat_ids = frozenset(self._subscribed_chat_ids)
        cursor_expired = (
            cursor is not None and after_sequence < self._updates.oldest_cursor
        )

        while True:
            match = self._updates.first_matching(
                subscribed_chat_ids,
                after_sequence,
            )
            if match:
                sequence, update = match
                return (
                    update,
                    sequence,
                    False,
                    cursor_expired,
                )

            remaining = deadline - loop.time()
            if remaining <= 0:
                return None, self._updates.next_sequence, True, cursor_expired

            waiter = loop.create_future()
            self._updates.waiters.add(waiter)
            try:
                await asyncio.wait_for(waiter, timeout=remaining)
            except asyncio.TimeoutError:
                return None, self._updates.next_sequence, True, cursor_expired
            finally:
                self._updates.waiters.discard(waiter)

    async def commit_updates(self, cursor: int) -> dict:
        removed_count = self._updates.commit(cursor)
        return {
            'committed_through': cursor,
            'removed_count': removed_count,
            **self.update_subscription(),
        }

    async def send_message(self, *args: Any, **kwargs: Any) -> dict:
        result = await self.call('send_message', *args, **kwargs)
        message_id = result.get('id')
        if message_id is not None:
            self._remember_sent_message(message_id)
        return result

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
        self._updates.wake_waiters()
        self._subscribed_chat_ids.clear()
        self.client = None
        self._mcp_loop = None
