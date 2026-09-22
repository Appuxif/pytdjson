import asyncio
import threading
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from telegram.mcp.runtime import (
    TelegramRuntime,
    _UpdateBuffer,
    _create_mcp_client,
)


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
                {
                    '@type': 'updateNewMessage',
                    'message': {'id': 1, 'chat_id': 10, 'is_outgoing': False},
                }
            )

            calls = []

            async def call(method, *args, **kwargs):
                calls.append((method, args, kwargs))
                return {'@type': 'ok'}

            runtime.call = call

            updates, cursor, timed_out, cursor_expired = await runtime.poll_updates(
                timeout=0.01,
                limit=1,
            )
            committed = await runtime.commit_updates(cursor)
            return updates, cursor, timed_out, cursor_expired, committed, calls

        updates, cursor, timed_out, cursor_expired, committed, calls = asyncio.run(
            exercise()
        )

        self.assertEqual(10, updates[0]['message']['chat_id'])
        self.assertEqual(1, cursor)
        self.assertFalse(timed_out)
        self.assertFalse(cursor_expired)
        self.assertEqual(1, committed['removed_count'])
        self.assertEqual(0, committed['buffer_size'])
        self.assertEqual(1, committed['marked_message_count'])
        self.assertEqual([('view_messages', (10, [1]), {'force_read': True})], calls)

    def test_mark_messages_as_read_ignores_outgoing_and_non_message_updates(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {'id': 1, 'chat_id': 10, 'is_outgoing': False},
                }
            )
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {'id': 2, 'chat_id': 10, 'is_outgoing': True},
                }
            )
            runtime._updates.add(
                {
                    '@type': 'mcpMessageTranscription',
                    'chat_id': 10,
                    'message_id': 3,
                }
            )
            calls = []

            async def call(method, *args, **kwargs):
                calls.append((method, args, kwargs))
                return {'@type': 'ok'}

            runtime.call = call
            return await runtime.commit_updates(3), calls

        committed, calls = asyncio.run(exercise())

        self.assertEqual(3, committed['removed_count'])
        self.assertEqual(1, committed['marked_message_count'])
        self.assertEqual([('view_messages', (10, [1]), {'force_read': True})], calls)

    def test_only_new_messages_are_buffered_and_sent_ids_are_ignored(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            runtime._remember_sent_message(10, 2)
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

    def test_forwarded_message_ids_are_ignored_in_update_buffer(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            runtime.call = AsyncMock(
                return_value={
                    '@type': 'messages',
                    'messages': [
                        {'id': 101, 'chat_id': 10},
                        None,
                    ],
                }
            )
            result = await runtime.forward_messages(
                10,
                20,
                [1, 2],
                send_copy=True,
            )
            return result, runtime.call.await_args, runtime._ignored_message_ids

        result, call, ignored_ids = asyncio.run(exercise())

        self.assertEqual(2, len(result['messages']))
        self.assertEqual((10, 20, [1, 2]), call.args[1:])
        self.assertEqual({'send_copy': True}, call.kwargs)
        self.assertEqual({(10, 101)}, ignored_ids)

    def test_update_buffer_is_bounded(self):
        buffer = _UpdateBuffer(maxlen=2)
        for chat_id in (10, 20, 30):
            buffer.add({'chat_id': chat_id})

        self.assertEqual(2, buffer.size)
        self.assertEqual(1, buffer.oldest_cursor)
        self.assertEqual(3, buffer.next_sequence)
        self.assertEqual(1, buffer.dropped_count)

    def test_subscription_filters_event_types_and_topics(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(
                frozenset({10}),
                event_types={'updateNewMessage'},
                topic_ids={7},
            )
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {
                        'id': 1,
                        'chat_id': 10,
                        'topic_id': {'@type': 'messageTopicForum', 'forum_topic_id': 7},
                    },
                }
            )
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {
                        'id': 2,
                        'chat_id': 10,
                        'topic_id': {'@type': 'messageTopicForum', 'forum_topic_id': 8},
                    },
                }
            )
            runtime._record_update(
                {
                    '@type': 'updateNewMessage',
                    'message': {
                        'id': 3,
                        'chat_id': 10,
                        'topic_id': {'@type': 'messageTopicForum', 'forum_topic_id': 7},
                    },
                }
            )
            return await runtime.poll_updates(timeout=0.01, limit=2)

        updates, _, timed_out, _ = asyncio.run(exercise())
        self.assertEqual([1, 3], [item['message']['id'] for item in updates])
        self.assertFalse(timed_out)

    def test_reaction_updates_require_an_explicit_event_subscription(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(
                frozenset({10}),
                event_types={'updateMessageInteractionInfo', 'updateMessageReaction'},
            )
            runtime._record_update(
                {
                    '@type': 'updateMessageInteractionInfo',
                    'chat_id': 10,
                    'message_id': 1,
                    'interaction_info': {},
                }
            )
            runtime._record_update(
                {
                    '@type': 'updateMessageReaction',
                    'chat_id': 10,
                    'message_id': 1,
                    'new_reaction_types': [],
                }
            )
            return await runtime.poll_updates(timeout=0.01, limit=2)

        updates, _, timed_out, _ = asyncio.run(exercise())
        self.assertEqual(
            ['updateMessageInteractionInfo', 'updateMessageReaction'],
            [item['@type'] for item in updates],
        )
        self.assertFalse(timed_out)

    def test_default_subscription_does_not_collect_reaction_updates(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            runtime._record_update(
                {
                    '@type': 'updateMessageInteractionInfo',
                    'chat_id': 10,
                    'message_id': 1,
                    'interaction_info': {},
                }
            )
            return await runtime.poll_updates(timeout=0.01, limit=1)

        updates, _, timed_out, _ = asyncio.run(exercise())
        self.assertEqual([], updates)
        self.assertTrue(timed_out)

    def test_dropped_updates_are_reported_and_persisted(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            runtime._updates = _UpdateBuffer(maxlen=2)
            await runtime.subscribe_for_updates(frozenset({10}))
            for message_id in (1, 2, 3):
                runtime._record_update(
                    {
                        '@type': 'updateNewMessage',
                        'message': {'id': message_id, 'chat_id': 10},
                    }
                )
            return runtime.update_subscription(), await runtime.poll_updates(
                timeout=0.01, limit=1, cursor=0
            )

        state, result = asyncio.run(exercise())
        self.assertEqual(1, state['dropped_count'])
        self.assertTrue(result[3])
        self.assertEqual(1, state['oldest_cursor'])

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

    def test_transcription_result_is_delivered_as_an_async_poll_update(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))

            async def call(method, *args, **kwargs):
                if method == 'get_message':
                    return {
                        'id': 55,
                        'chat_id': 10,
                        'sender_id': {
                            '@type': 'messageSenderUser',
                            'user_id': 20,
                        },
                        'content': {
                            '@type': 'messageVoiceNote',
                            'voice_note': {
                                'duration': 4,
                                'speech_recognition_result': None,
                            },
                        },
                    }
                if method == 'get_message_properties':
                    return {'can_recognize_speech': True}
                if method == 'recognize_speech':
                    return {'@type': 'ok'}
                raise AssertionError(method)

            runtime.call = call
            request = await runtime.request_message_transcript(10, 55)

            runtime._record_update(
                {
                    '@type': 'updateMessageContent',
                    'chat_id': 10,
                    'message_id': 55,
                    'new_content': {
                        '@type': 'messageVoiceNote',
                        'voice_note': {
                            'speech_recognition_result': {
                                '@type': 'speechRecognitionResultPending',
                                'partial_text': 'partial',
                            }
                        },
                    },
                }
            )
            runtime._record_update(
                {
                    '@type': 'updateMessageContent',
                    'chat_id': 10,
                    'message_id': 55,
                    'new_content': {
                        '@type': 'messageVoiceNote',
                        'voice_note': {
                            'speech_recognition_result': {
                                '@type': 'speechRecognitionResultText',
                                'text': 'hello from voice',
                            }
                        },
                    },
                }
            )
            updates, cursor, timed_out, _ = await runtime.poll_updates(
                timeout=0.01, limit=1
            )
            return request, updates, cursor, timed_out, runtime.update_subscription()

        request, updates, cursor, timed_out, state = asyncio.run(exercise())

        self.assertEqual('pending', request['status'])
        self.assertEqual([], state['pending_transcriptions'])
        self.assertEqual('mcpMessageTranscription', updates[0]['@type'])
        self.assertEqual('completed', updates[0]['status'])
        self.assertEqual('hello from voice', updates[0]['text'])
        self.assertEqual(55, updates[0]['original_message']['id'])
        self.assertEqual(1, cursor)
        self.assertFalse(timed_out)

    def test_unrequested_message_content_updates_are_ignored(self):
        async def exercise():
            runtime = TelegramRuntime(SimpleNamespace())
            await runtime.subscribe_for_updates(frozenset({10}))
            runtime._record_update(
                {
                    '@type': 'updateMessageContent',
                    'chat_id': 10,
                    'message_id': 55,
                    'new_content': {
                        '@type': 'messageVoiceNote',
                        'voice_note': {
                            'speech_recognition_result': {
                                '@type': 'speechRecognitionResultText',
                                'text': 'unrequested',
                            }
                        },
                    },
                }
            )
            return await runtime.poll_updates(timeout=0.01, limit=1)

        updates, _, timed_out, _ = asyncio.run(exercise())

        self.assertEqual([], updates)
        self.assertTrue(timed_out)

    def test_pending_transcription_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = SimpleNamespace(files_directory=directory)
            first = TelegramRuntime(settings)

            async def call(method, *args, **kwargs):
                if method == 'get_message':
                    return {
                        'id': 55,
                        'chat_id': 10,
                        'content': {
                            '@type': 'messageVideoNote',
                            'video_note': {
                                'speech_recognition_result': None,
                            },
                        },
                    }
                if method == 'get_message_properties':
                    return {'can_recognize_speech': True}
                if method == 'recognize_speech':
                    return {'@type': 'ok'}
                raise AssertionError(method)

            async def populate():
                await first.subscribe_for_updates(frozenset({10}))
                first.call = call
                return await first.request_message_transcript(10, 55)

            request = asyncio.run(populate())
            restored = TelegramRuntime(settings)
            state = restored.update_subscription()

        self.assertEqual('pending', request['status'])
        self.assertEqual(
            [{'chat_id': 10, 'message_id': 55}],
            state['pending_transcriptions'],
        )

    def test_subscription_filters_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = SimpleNamespace(files_directory=directory)
            first = TelegramRuntime(settings)

            async def populate():
                await first.subscribe_for_updates(
                    frozenset({10}),
                    event_types={'updateMessageEdited'},
                    topic_ids={7},
                )

            asyncio.run(populate())
            restored = TelegramRuntime(settings)
            state = restored.update_subscription()

        self.assertEqual(
            [
                {
                    'chat_id': 10,
                    'event_types': ['updateMessageEdited'],
                    'topic_ids': [7],
                }
            ],
            state['subscriptions'],
        )

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
                first._remember_sent_message(10, 2)

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
