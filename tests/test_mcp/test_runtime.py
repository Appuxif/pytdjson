import asyncio
import threading
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from telegram.mcp.runtime import TelegramRuntime, _UpdateBuffer, _create_mcp_client


class LoopStub:
    def call_soon_threadsafe(self, callback):
        callback()


class ClientStub:
    def __init__(self):
        self.is_enabled = False
        self._loop = LoopStub()
        self.login_thread = None
        self._stopped = threading.Event()
        self.update_handlers = []

    def add_update_handler(self, handler_type, handler):
        self.update_handlers.append((handler_type, handler))

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
        self.assertEqual(['*'], [item[0] for item in client.update_handlers])

    def test_updates_require_subscription_and_commit_in_fifo_order(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            runtime._record_update(
                {'@type': 'updateNewMessage', 'message': {'chat_id': 20}}
            )
            runtime._record_update(
                {'@type': 'updateNewMessage', 'message': {'chat_id': 10}}
            )

            updates, cursor, timed_out, cursor_expired = await runtime.poll_updates(
                timeout=0.01,
                limit=1,
            )
            committed = await runtime.commit_updates(cursor)
            return updates, cursor, timed_out, cursor_expired, committed

        updates, cursor, timed_out, cursor_expired, committed = asyncio.run(exercise())

        self.assertEqual(10, updates[0]['message']['chat_id'])
        self.assertEqual(1, cursor)
        self.assertFalse(timed_out)
        self.assertFalse(cursor_expired)
        self.assertEqual(1, committed['removed_count'])
        self.assertEqual(0, committed['buffer_size'])

    def test_only_new_messages_are_buffered_and_sent_ids_are_ignored(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            runtime._remember_sent_message(2)
            self.assertEqual(2000, runtime._updates.events.maxlen)
            runtime._record_update({'@type': 'updateChatLastMessage', 'chat_id': 10})
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {'id': 1, 'chat_id': 10, 'is_outgoing': True},
                }
            )
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {'id': 2, 'chat_id': 10, 'is_outgoing': True},
                }
            )
            return await runtime.poll_updates(timeout=0.01, limit=1)

        updates, _, timed_out, _ = asyncio.run(exercise())

        self.assertEqual(1, updates[0]['message']['id'])
        self.assertFalse(timed_out)

    def test_update_buffer_is_bounded(self):
        buffer = _UpdateBuffer(maxlen=2)
        for chat_id in (10, 20, 30):
            buffer.add({'chat_id': chat_id})

        self.assertEqual(2, buffer.size)
        self.assertEqual(1, buffer.oldest_cursor)
        self.assertEqual(3, buffer.next_sequence)

    def test_poll_updates_times_out_without_a_matching_event(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            return await runtime.poll_updates(timeout=0.01, limit=1)

        updates, cursor, timed_out, cursor_expired = asyncio.run(exercise())

        self.assertEqual([], updates)
        self.assertEqual(0, cursor)
        self.assertTrue(timed_out)
        self.assertFalse(cursor_expired)

    def test_poll_updates_returns_a_bounded_batch(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            for message_id in (1, 2, 3):
                runtime._record_update(
                    {
                        '@type': 'updateNewMessage',
                        'message': {'id': message_id, 'chat_id': 10},
                    }
                )
            first = await runtime.poll_updates(timeout=0.01, limit=2)
            second = await runtime.poll_updates(
                timeout=0.01,
                limit=2,
                cursor=first[1],
            )
            return first, second

        first, second = asyncio.run(exercise())

        self.assertEqual([1, 2], [item['message']['id'] for item in first[0]])
        self.assertEqual(2, first[1])
        self.assertEqual([3], [item['message']['id'] for item in second[0]])
        self.assertEqual(3, second[1])

    def test_state_is_restored_from_the_client_data_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = SimpleNamespace(files_directory=directory)
            first = TelegramRuntime(settings)

            async def populate():
                await first.subscribe_for_updates(frozenset({10}))
                first._record_update(
                    {
                        '@type': 'updateNewMessage',
                        'message': {'id': 1, 'chat_id': 10},
                    }
                )
                first._remember_sent_message(2)

            asyncio.run(populate())

            restored = TelegramRuntime(settings)
            state = restored.update_subscription()
            updates, cursor, timed_out, _ = asyncio.run(
                restored.poll_updates(timeout=0.01, limit=1)
            )

        self.assertEqual([10], state['subscribed_chat_ids'])
        self.assertEqual(1, state['buffer_size'])
        self.assertEqual(1, state['next_cursor'])
        self.assertEqual(1, updates[0]['message']['id'])
        self.assertEqual(1, cursor)
        self.assertFalse(timed_out)
