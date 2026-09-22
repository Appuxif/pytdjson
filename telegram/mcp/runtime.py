"""Thread bridge between MCP's event loop and AsyncTelegram."""
import asyncio
from collections import deque
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Callable, Deque, Optional

from telegram.client import AsyncTelegram, Settings


class TelegramMCPError(RuntimeError):
    """A safe error suitable for returning to an MCP client."""


class _UpdateBuffer:
    def __init__(self, maxlen: int = 2000, dropped_count: int = 0) -> None:
        self.maxlen = maxlen
        self.events: Deque[tuple[int, dict]] = deque(maxlen=self.maxlen)
        self.next_sequence = 0
        self.dropped_count = dropped_count
        self.waiters: set[asyncio.Future[None]] = set()

    def add(self, update: dict) -> int:
        if len(self.events) >= self.maxlen:
            self.dropped_count += 1
        self.next_sequence += 1
        self.events.append((self.next_sequence, update))
        for waiter in tuple(self.waiters):
            if not waiter.done():
                waiter.set_result(None)
        return self.next_sequence

    @property
    def oldest_cursor(self) -> int:
        if not self.events:
            return self.next_sequence
        return self.events[0][0] - 1

    @property
    def size(self) -> int:
        return len(self.events)

    def remove_chats(self, chat_ids: frozenset[int]) -> list[int]:
        removed = [
            sequence
            for sequence, update in self.events
            if _update_chat_id(update) in chat_ids
        ]
        self.events = deque(
            (
                (sequence, update)
                for sequence, update in self.events
                if _update_chat_id(update) not in chat_ids
            ),
            maxlen=self.maxlen,
        )
        return removed

    def remove_message(self, message_id: int) -> list[int]:
        removed = [
            sequence
            for sequence, update in self.events
            if _update_message_id(update) == message_id
        ]
        self.events = deque(
            (
                (sequence, update)
                for sequence, update in self.events
                if _update_message_id(update) != message_id
            ),
            maxlen=self.maxlen,
        )
        return removed

    def wake_waiters(self) -> None:
        for waiter in tuple(self.waiters):
            if not waiter.done():
                waiter.set_result(None)

    def matching(
        self,
        subscriptions: dict[int, dict],
        after_sequence: int,
        limit: int,
    ) -> list[tuple[int, dict]]:
        matches = []
        for sequence, update in self.events:
            if sequence > after_sequence and _update_matches_subscription(
                update, subscriptions
            ):
                matches.append((sequence, update))
                if len(matches) >= limit:
                    break
        return matches

    def commit(self, cursor: int) -> list[int]:
        if cursor > self.next_sequence:
            raise ValueError('cursor is ahead of the latest update')
        removed = []
        while self.events and self.events[0][0] <= cursor:
            sequence, _ = self.events.popleft()
            removed.append(sequence)
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
    if update.get('message_id') is not None:
        return update['message_id']
    return (update.get('message') or {}).get('id')


def _update_topic_id(update: dict) -> Optional[int]:
    message = update.get('message') or update.get('original_message') or {}
    topic = message.get('topic_id') or {}
    for key in (
        'forum_topic_id',
        'message_thread_id',
        'direct_messages_chat_topic_id',
        'saved_messages_topic_id',
    ):
        if topic.get(key) is not None:
            return topic[key]
    return None


DEFAULT_UPDATE_EVENT_TYPES = frozenset({'updateNewMessage', 'mcpMessageTranscription'})


def _update_matches_subscription(update: dict, subscriptions: dict[int, dict]) -> bool:
    chat_id = _update_chat_id(update)
    subscription = subscriptions.get(chat_id)
    if subscription is None:
        return False
    if update.get('@type') == 'mcpMessageTranscription':
        topic_ids = subscription.get('topic_ids') or set()
        return not topic_ids or _update_topic_id(update) in topic_ids
    event_types = subscription.get('event_types') or DEFAULT_UPDATE_EVENT_TYPES
    if '*' not in event_types and update.get('@type') not in event_types:
        return False
    topic_ids = subscription.get('topic_ids') or set()
    return not topic_ids or _update_topic_id(update) in topic_ids


def _speech_recognition_result(content: Optional[dict]) -> Optional[dict]:
    if not content:
        return None
    content_type = content.get('@type')
    media_key = {
        'messageVoiceNote': 'voice_note',
        'messageVideoNote': 'video_note',
    }.get(content_type)
    if media_key is None:
        return None
    media = content.get(media_key) or {}
    result = media.get('speech_recognition_result') or {}
    result_type = result.get('@type')
    if result_type == 'speechRecognitionResultText':
        return {'status': 'completed', 'text': result.get('text', '')}
    if result_type == 'speechRecognitionResultError':
        return {'status': 'failed', 'error': result.get('error') or {}}
    return None


def _transcription_message_metadata(message: dict, chat_id: int) -> dict:
    metadata = {
        key: message[key]
        for key in (
            'id',
            'sender_id',
            'sender',
            'date',
            'edit_date',
            'is_outgoing',
            'topic_id',
            'reply_to',
        )
        if key in message
    }
    metadata['chat_id'] = message.get('chat_id', chat_id)
    content = message.get('content') or {}
    metadata['content'] = {'@type': content.get('@type')}
    return metadata


class _PersistentState:
    """SQLite-backed state stored next to the TDLib client data."""

    def __init__(self, files_directory: Optional[str]) -> None:
        self.path = (
            Path(files_directory) / 'mcp_state.sqlite3' if files_directory else None
        )
        database = str(self.path) if self.path else ':memory:'
        try:
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(
                database,
                timeout=30,
                check_same_thread=False,
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute('PRAGMA busy_timeout = 30000')
            if self.path:
                self.connection.execute('PRAGMA journal_mode = WAL')
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS mcp_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mcp_subscriptions (
                    chat_id INTEGER PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS mcp_updates (
                    sequence INTEGER PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mcp_ignored_messages (
                    message_id INTEGER PRIMARY KEY,
                    sequence INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mcp_transcription_requests (
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    original_message TEXT NOT NULL,
                    PRIMARY KEY(chat_id, message_id)
                );
                """
            )
            columns = {
                row['name']
                for row in self.connection.execute(
                    'PRAGMA table_info(mcp_subscriptions)'
                )
            }
            if 'event_types' not in columns:
                self.connection.execute(
                    "ALTER TABLE mcp_subscriptions ADD COLUMN event_types TEXT"
                )
            if 'topic_ids' not in columns:
                self.connection.execute(
                    "ALTER TABLE mcp_subscriptions ADD COLUMN topic_ids TEXT"
                )
            self.connection.commit()
            if self.path:
                os.chmod(self.path, 0o600)
        except (OSError, sqlite3.Error) as error:
            raise TelegramMCPError(
                f'cannot initialize MCP state database at {database}'
            ) from error

    def _metadata_int(self, key: str) -> int:
        row = self.connection.execute(
            'SELECT value FROM mcp_metadata WHERE key = ?',
            (key,),
        ).fetchone()
        return int(row['value']) if row else 0

    def _set_metadata(self, key: str, value: int) -> None:
        self.connection.execute(
            'INSERT OR REPLACE INTO mcp_metadata(key, value) VALUES (?, ?)',
            (key, str(value)),
        )

    def load(self, maxlen: int) -> dict:
        try:
            subscription_rows = {
                row['chat_id']: {
                    'event_types': set(
                        json.loads(row['event_types'])
                        if row['event_types']
                        else DEFAULT_UPDATE_EVENT_TYPES
                    ),
                    'topic_ids': set(
                        json.loads(row['topic_ids']) if row['topic_ids'] else []
                    ),
                }
                for row in self.connection.execute(
                    'SELECT chat_id, event_types, topic_ids '
                    'FROM mcp_subscriptions ORDER BY chat_id'
                )
            }
            rows = list(
                self.connection.execute(
                    'SELECT sequence, payload FROM mcp_updates '
                    'ORDER BY sequence DESC LIMIT ?',
                    (maxlen,),
                )
            )
            events = []
            for row in reversed(rows):
                payload = json.loads(row['payload'])
                if not isinstance(payload, dict):
                    raise ValueError('stored update is not an object')
                events.append((row['sequence'], payload))
            ignored_rows = list(
                self.connection.execute(
                    'SELECT message_id FROM mcp_ignored_messages '
                    'ORDER BY sequence DESC LIMIT ?',
                    (maxlen,),
                )
            )
            ignored_message_ids = [row['message_id'] for row in reversed(ignored_rows)]
            transcription_requests = []
            for row in self.connection.execute(
                'SELECT chat_id, message_id, original_message '
                'FROM mcp_transcription_requests ORDER BY chat_id, message_id'
            ):
                original_message = json.loads(row['original_message'])
                if not isinstance(original_message, dict):
                    raise ValueError('stored original message is not an object')
                transcription_requests.append(
                    {
                        'chat_id': row['chat_id'],
                        'message_id': row['message_id'],
                        'original_message': original_message,
                    }
                )
            return {
                'subscribed_chat_ids': set(subscription_rows),
                'subscriptions': subscription_rows,
                'events': events,
                'next_sequence': self._metadata_int('next_sequence'),
                'dropped_count': self._metadata_int('dropped_count'),
                'ignored_message_ids': ignored_message_ids,
                'ignored_next_sequence': self._metadata_int('ignored_next_sequence'),
                'transcription_requests': transcription_requests,
            }
        except (TypeError, ValueError, json.JSONDecodeError, sqlite3.Error) as error:
            raise TelegramMCPError('cannot load MCP state database') from error

    def save_subscriptions(self, subscriptions: dict[int, dict]) -> None:
        try:
            with self.connection:
                self.connection.execute('DELETE FROM mcp_subscriptions')
                self.connection.executemany(
                    'INSERT INTO mcp_subscriptions(chat_id, event_types, topic_ids) '
                    'VALUES (?, ?, ?)',
                    (
                        (
                            chat_id,
                            json.dumps(sorted(item.get('event_types') or [])),
                            json.dumps(sorted(item.get('topic_ids') or [])),
                        )
                        for chat_id, item in sorted(subscriptions.items())
                    ),
                )
        except sqlite3.Error as error:
            raise TelegramMCPError('cannot persist MCP subscriptions') from error

    def add_update(
        self,
        sequence: int,
        update: dict,
        maxlen: int,
        dropped_count: Optional[int] = None,
    ) -> None:
        try:
            with self.connection:
                self.connection.execute(
                    'INSERT OR REPLACE INTO mcp_updates(sequence, payload) '
                    'VALUES (?, ?)',
                    (sequence, json.dumps(update, ensure_ascii=False)),
                )
                self._set_metadata('next_sequence', sequence)
                if dropped_count is not None:
                    self._set_metadata('dropped_count', dropped_count)
                self.connection.execute(
                    'DELETE FROM mcp_updates WHERE sequence <= ?',
                    (sequence - maxlen,),
                )
        except (TypeError, ValueError, sqlite3.Error) as error:
            raise TelegramMCPError('cannot persist MCP update') from error

    def delete_updates(self, sequences: list[int]) -> None:
        if not sequences:
            return
        try:
            placeholders = ','.join('?' for _ in sequences)
            with self.connection:
                self.connection.execute(
                    f'DELETE FROM mcp_updates WHERE sequence IN ({placeholders})',
                    sequences,
                )
        except sqlite3.Error as error:
            raise TelegramMCPError('cannot remove MCP updates from state') from error

    def add_transcription_request(
        self, chat_id: int, message_id: int, original_message: dict
    ) -> None:
        try:
            with self.connection:
                self.connection.execute(
                    'INSERT OR REPLACE INTO mcp_transcription_requests '
                    '(chat_id, message_id, original_message) VALUES (?, ?, ?)',
                    (
                        chat_id,
                        message_id,
                        json.dumps(original_message, ensure_ascii=False),
                    ),
                )
        except (TypeError, ValueError, sqlite3.Error) as error:
            raise TelegramMCPError('cannot persist transcription request') from error

    def delete_transcription_request(self, chat_id: int, message_id: int) -> None:
        try:
            with self.connection:
                self.connection.execute(
                    'DELETE FROM mcp_transcription_requests '
                    'WHERE chat_id = ? AND message_id = ?',
                    (chat_id, message_id),
                )
        except sqlite3.Error as error:
            raise TelegramMCPError('cannot remove transcription request') from error

    def add_ignored_message(
        self, message_id: int, sequence: int, maxlen: int
    ) -> list[int]:
        try:
            with self.connection:
                self.connection.execute(
                    'INSERT OR REPLACE INTO mcp_ignored_messages '
                    '(message_id, sequence) VALUES (?, ?)',
                    (message_id, sequence),
                )
                self._set_metadata('ignored_next_sequence', sequence)
                stale_rows = list(
                    self.connection.execute(
                        'SELECT message_id FROM mcp_ignored_messages '
                        'ORDER BY sequence ASC LIMIT -1 OFFSET ?',
                        (maxlen,),
                    )
                )
                stale_ids = [row['message_id'] for row in stale_rows]
                if stale_ids:
                    placeholders = ','.join('?' for _ in stale_ids)
                    self.connection.execute(
                        'DELETE FROM mcp_ignored_messages '
                        f'WHERE message_id IN ({placeholders})',
                        stale_ids,
                    )
                return stale_ids
        except sqlite3.Error as error:
            raise TelegramMCPError('cannot persist ignored MCP message ID') from error


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
        self._state = _PersistentState(getattr(settings, 'files_directory', None))
        self._updates = _UpdateBuffer()
        self._subscribed_chat_ids: set[int] = set()
        self._subscriptions: dict[int, dict] = {}
        self._ignored_message_ids: set[int] = set()
        self._ignored_message_order: Deque[int] = deque()
        self._ignored_next_sequence = 0
        self._transcription_requests: dict[tuple[int, int], dict] = {}
        self._load_persistent_state()

    def _load_persistent_state(self) -> None:
        state = self._state.load(_UpdateBuffer().maxlen)
        self._subscribed_chat_ids = set(state['subscribed_chat_ids'])
        self._updates = _UpdateBuffer()
        self._updates.next_sequence = state['next_sequence']
        self._updates.dropped_count = state.get('dropped_count', 0)
        self._updates.events.extend(state['events'][-self._updates.maxlen :])
        self._subscriptions = {
            chat_id: {
                'event_types': set(
                    item.get('event_types') or DEFAULT_UPDATE_EVENT_TYPES
                ),
                'topic_ids': set(item.get('topic_ids') or set()),
            }
            for chat_id, item in state.get('subscriptions', {}).items()
        }
        if not self._subscriptions:
            self._subscriptions = {
                chat_id: {
                    'event_types': set(DEFAULT_UPDATE_EVENT_TYPES),
                    'topic_ids': set(),
                }
                for chat_id in state['subscribed_chat_ids']
            }
        self._subscribed_chat_ids = set(self._subscriptions)
        self._ignored_message_order = deque(state['ignored_message_ids'])
        self._ignored_message_ids = set(self._ignored_message_order)
        self._ignored_next_sequence = state['ignored_next_sequence']
        self._transcription_requests = {
            (item['chat_id'], item['message_id']): item['original_message']
            for item in state['transcription_requests']
        }

    async def start(self) -> None:
        self._mcp_loop = asyncio.get_running_loop()
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
        await self._recover_transcription_requests()
        if self.on_ready:
            self.on_ready()

    async def _handle_update(self, update: Any) -> None:
        raw_update = getattr(update, 'raw', update)
        if not isinstance(raw_update, dict) or self._mcp_loop is None:
            return
        self._mcp_loop.call_soon_threadsafe(self._record_update, raw_update)

    def _record_update(self, update: dict) -> None:
        update_type = update.get('@type')
        if update_type == 'updateMessageContent':
            self._record_transcription_update(update)
        if update_type == 'mcpMessageTranscription':
            return
        if _update_message_id(update) in self._ignored_message_ids:
            return
        if _update_matches_subscription(update, self._subscriptions):
            sequence = self._updates.add(update)
            self._state.add_update(
                sequence,
                update,
                self._updates.maxlen,
                self._updates.dropped_count,
            )

    def _record_transcription_update(self, update: dict) -> None:
        chat_id = _update_chat_id(update)
        message_id = _update_message_id(update)
        if chat_id is None or message_id is None:
            return
        if chat_id not in self._subscribed_chat_ids:
            return
        if (chat_id, message_id) not in self._transcription_requests:
            return
        result = _speech_recognition_result(update.get('new_content'))
        if result is not None:
            self._record_transcription_result(chat_id, message_id, result)

    def _record_transcription_result(
        self, chat_id: int, message_id: int, result: dict
    ) -> None:
        original_message = self._transcription_requests.get((chat_id, message_id))
        if original_message is None:
            return
        update = {
            '@type': 'mcpMessageTranscription',
            'chat_id': chat_id,
            'message_id': message_id,
            'status': result['status'],
            'original_message': original_message,
        }
        if result['status'] == 'completed':
            update['text'] = result.get('text', '')
        else:
            update['error'] = result.get('error') or {}
        sequence = self._updates.add(update)
        self._state.add_update(
            sequence,
            update,
            self._updates.maxlen,
            self._updates.dropped_count,
        )
        self._transcription_requests.pop((chat_id, message_id), None)
        self._state.delete_transcription_request(chat_id, message_id)

    async def _recover_transcription_requests(self) -> None:
        for chat_id, message_id in tuple(self._transcription_requests):
            try:
                message = await self.call('get_message', message_id, chat_id)
            except TelegramMCPError:
                continue
            result = _speech_recognition_result(message.get('content'))
            if result is not None:
                self._record_transcription_result(chat_id, message_id, result)

    def _remember_sent_message(self, message_id: int) -> None:
        if message_id in self._ignored_message_ids:
            return
        self._ignored_message_ids.add(message_id)
        self._ignored_message_order.append(message_id)
        self._ignored_next_sequence += 1
        expired_ids = self._state.add_ignored_message(
            message_id,
            self._ignored_next_sequence,
            self._updates.maxlen,
        )
        for expired_id in expired_ids:
            try:
                self._ignored_message_order.remove(expired_id)
            except ValueError:
                pass
            self._ignored_message_ids.discard(expired_id)
        removed = self._updates.remove_message(message_id)
        self._state.delete_updates(removed)

    async def subscribe_for_updates(
        self,
        chat_ids: frozenset[int],
        event_types: Optional[set[str]] = None,
        topic_ids: Optional[set[int]] = None,
    ) -> dict:
        added_chat_ids = chat_ids - self._subscribed_chat_ids
        normalized_event_types = set(
            DEFAULT_UPDATE_EVENT_TYPES if event_types is None else event_types
        )
        if not normalized_event_types:
            raise ValueError('event_types must not be empty')
        normalized_topic_ids = set(topic_ids or set())
        self._subscribed_chat_ids.update(chat_ids)
        for chat_id in chat_ids:
            if (
                chat_id not in self._subscriptions
                or event_types is not None
                or topic_ids is not None
            ):
                self._subscriptions[chat_id] = {
                    'event_types': normalized_event_types,
                    'topic_ids': normalized_topic_ids,
                }
        self._state.save_subscriptions(self._subscriptions)
        return {
            'subscribed_chat_ids': sorted(self._subscribed_chat_ids),
            'added_chat_ids': sorted(added_chat_ids),
            'subscriptions': self._subscription_payload(),
        }

    async def unsubscribe_from_updates(self, chat_ids: frozenset[int]) -> dict:
        removed_chat_ids = chat_ids & self._subscribed_chat_ids
        self._subscribed_chat_ids.difference_update(chat_ids)
        for chat_id in removed_chat_ids:
            self._subscriptions.pop(chat_id, None)
        removed_sequences = self._updates.remove_chats(chat_ids)
        self._state.delete_updates(removed_sequences)
        for request_chat_id, request_message_id in tuple(self._transcription_requests):
            if request_chat_id in removed_chat_ids:
                self._transcription_requests.pop(
                    (request_chat_id, request_message_id), None
                )
                self._state.delete_transcription_request(
                    request_chat_id, request_message_id
                )
        self._state.save_subscriptions(self._subscriptions)
        return {
            'subscribed_chat_ids': sorted(self._subscribed_chat_ids),
            'removed_chat_ids': sorted(removed_chat_ids),
            'subscriptions': self._subscription_payload(),
        }

    def _subscription_payload(self) -> list[dict]:
        return [
            {
                'chat_id': chat_id,
                'event_types': sorted(item.get('event_types') or []),
                'topic_ids': sorted(item.get('topic_ids') or []),
            }
            for chat_id, item in sorted(self._subscriptions.items())
        ]

    def update_subscription(self) -> dict:
        return {
            'subscribed_chat_ids': sorted(self._subscribed_chat_ids),
            'buffer_size': self._updates.size,
            'buffer_limit': self._updates.events.maxlen,
            'oldest_cursor': self._updates.oldest_cursor,
            'next_cursor': self._updates.next_sequence,
            'dropped_count': self._updates.dropped_count,
            'subscriptions': self._subscription_payload(),
            'pending_transcriptions': [
                {'chat_id': chat_id, 'message_id': message_id}
                for chat_id, message_id in sorted(self._transcription_requests)
            ],
        }

    async def poll_updates(
        self,
        timeout: float,
        limit: int = 1,
        cursor: Optional[int] = None,
    ) -> tuple[list[dict], int, bool, bool]:
        """Wait for updates from subscribed chats and return a cursor."""
        if not self._subscribed_chat_ids:
            raise ValueError('no update subscriptions configured')
        if limit < 1:
            raise ValueError('limit must be at least 1')

        loop = asyncio.get_running_loop()
        after_sequence = (
            self._updates.oldest_cursor if cursor is None else max(cursor, 0)
        )
        deadline = loop.time() + timeout
        subscriptions = {
            chat_id: {
                'event_types': set(item.get('event_types') or []),
                'topic_ids': set(item.get('topic_ids') or []),
            }
            for chat_id, item in self._subscriptions.items()
        }
        cursor_expired = (
            cursor is not None and after_sequence < self._updates.oldest_cursor
        )

        while True:
            matches = self._updates.matching(
                subscriptions,
                after_sequence,
                limit,
            )
            if matches:
                return (
                    [update for _, update in matches],
                    matches[-1][0],
                    False,
                    cursor_expired,
                )

            remaining = deadline - loop.time()
            if remaining <= 0:
                return [], self._updates.next_sequence, True, cursor_expired

            waiter = loop.create_future()
            self._updates.waiters.add(waiter)
            try:
                await asyncio.wait_for(waiter, timeout=remaining)
            except asyncio.TimeoutError:
                return [], self._updates.next_sequence, True, cursor_expired
            finally:
                self._updates.waiters.discard(waiter)

    def has_more_updates(self, cursor: int) -> bool:
        return bool(self._updates.matching(self._subscriptions, max(cursor, 0), 1))

    async def request_message_transcript(self, chat_id: int, message_id: int) -> dict:
        """Start asynchronous TDLib speech recognition for one message."""
        if chat_id not in self._subscribed_chat_ids:
            raise ValueError(
                f'chat {chat_id} is not subscribed; call ' 'subscribe_for_updates first'
            )

        request_key = (chat_id, message_id)
        original_message = self._transcription_requests.get(request_key)
        if original_message is not None:
            return {
                'status': 'pending',
                'chat_id': chat_id,
                'message_id': message_id,
                'original_message': original_message,
            }

        message = await self.call('get_message', message_id, chat_id)
        content = message.get('content') or {}
        if content.get('@type') not in {'messageVoiceNote', 'messageVideoNote'}:
            raise ValueError(
                'speech recognition is supported only for voice and video notes'
            )

        original_message = _transcription_message_metadata(message, chat_id)
        existing_result = _speech_recognition_result(content)
        if existing_result is not None:
            response = {
                'chat_id': chat_id,
                'message_id': message_id,
                'original_message': original_message,
                **existing_result,
            }
            return response

        properties = await self.call(
            'get_message_properties', chat_id=chat_id, message_id=message_id
        )
        if not properties.get('can_recognize_speech', False):
            raise ValueError('TDLib does not allow speech recognition for this message')

        self._transcription_requests[request_key] = original_message
        self._state.add_transcription_request(chat_id, message_id, original_message)
        try:
            await self.call('recognize_speech', chat_id, message_id)
        except Exception:
            self._transcription_requests.pop(request_key, None)
            self._state.delete_transcription_request(chat_id, message_id)
            raise
        return {
            'status': 'pending',
            'chat_id': chat_id,
            'message_id': message_id,
            'original_message': original_message,
        }

    async def commit_updates(self, cursor: int) -> dict:
        removed_sequences = self._updates.commit(cursor)
        self._state.delete_updates(removed_sequences)
        return {
            'committed_through': cursor,
            'removed_count': len(removed_sequences),
            **self.update_subscription(),
        }

    async def send_message(self, *args: Any, **kwargs: Any) -> dict:
        result = await self.call('send_message', *args, **kwargs)
        message_id = result.get('id')
        if message_id is not None:
            self._remember_sent_message(message_id)
        return result

    async def forward_messages(self, *args: Any, **kwargs: Any) -> dict:
        result = await self.call('forward_messages', *args, **kwargs)
        for message in result.get('messages') or []:
            if message and message.get('id') is not None:
                self._remember_sent_message(message['id'])
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
        self.client = None
        self._mcp_loop = None
