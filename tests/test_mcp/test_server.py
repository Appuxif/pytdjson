import asyncio
import json
import tempfile
from unittest import TestCase

from mcp.server.mcpserver.exceptions import ToolError

from telegram.mcp.config import load_settings
from telegram.mcp.server import TELEGRAM_MESSAGE_DISCLAIMER, create_server


def awaitable_call(server, name, arguments):
    return asyncio.run(server.call_tool(name, arguments))


class RuntimeStub:
    def __init__(self):
        self.calls = []
        self.subscribed_chat_ids = set()
        self.poll_calls = []
        self.subscription_kwargs = []

    async def start(self):
        pass

    async def stop(self):
        pass

    async def subscribe_for_updates(self, chat_ids, **kwargs):
        self.subscription_kwargs.append(kwargs)
        added = chat_ids - self.subscribed_chat_ids
        self.subscribed_chat_ids.update(chat_ids)
        return {
            'subscribed_chat_ids': sorted(self.subscribed_chat_ids),
            'added_chat_ids': sorted(added),
            'subscriptions': [],
        }

    async def unsubscribe_from_updates(self, chat_ids):
        removed = chat_ids & self.subscribed_chat_ids
        self.subscribed_chat_ids.difference_update(chat_ids)
        return {
            'subscribed_chat_ids': sorted(self.subscribed_chat_ids),
            'removed_chat_ids': sorted(removed),
            'subscriptions': [],
        }

    def update_subscription(self):
        return {
            'subscribed_chat_ids': sorted(self.subscribed_chat_ids),
            'buffer_size': 0,
            'buffer_limit': 2000,
            'oldest_cursor': 0,
            'next_cursor': 0,
            'dropped_count': 0,
            'subscriptions': [],
        }

    def has_more_updates(self, cursor):
        return False

    async def poll_updates(self, timeout, limit=1, cursor=None):
        self.poll_calls.append((timeout, limit, cursor))
        return (
            [
                {
                    '@type': 'updateNewMessage',
                    'message': {
                        'id': 77,
                        'chat_id': 10,
                        'date': 123,
                        'is_outgoing': False,
                        'content': {
                            '@type': 'messageText',
                            'text': {'text': 'incoming'},
                        },
                    },
                }
            ],
            5,
            False,
            False,
        )

    async def mark_messages_as_read(self, chat_id, message_ids):
        self.calls.append(
            ('view_messages', (chat_id, message_ids), {'force_read': True})
        )
        return {
            'chat_id': chat_id,
            'marked_message_ids': list(dict.fromkeys(message_ids)),
            'marked_count': len(set(message_ids)),
        }

    async def commit_updates(self, cursor, mark_messages_as_read=True):
        return {
            'committed_through': cursor,
            'removed_count': 1,
            'marked_as_read': mark_messages_as_read,
            'marked_message_count': 1 if mark_messages_as_read else 0,
            'marked_chat_ids': [10] if mark_messages_as_read else [],
            **self.update_subscription(),
        }

    async def send_message(self, *args, **kwargs):
        return await self.call('send_message', *args, **kwargs)

    async def forward_messages(self, *args, **kwargs):
        return await self.call('forward_messages', *args, **kwargs)

    async def add_message_reaction(self, *args, **kwargs):
        return await self.call('add_message_reaction', *args, **kwargs)

    async def remove_message_reaction(self, *args, **kwargs):
        return await self.call('remove_message_reaction', *args, **kwargs)

    async def get_message_available_reactions(self, *args, **kwargs):
        return await self.call('get_message_available_reactions', *args, **kwargs)

    async def get_message_added_reactions(self, *args, **kwargs):
        return await self.call('get_message_added_reactions', *args, **kwargs)

    async def request_message_transcript(self, chat_id, message_id):
        return {
            'status': 'pending',
            'chat_id': chat_id,
            'message_id': message_id,
            'original_message': {
                'id': message_id,
                'chat_id': chat_id,
                'content': {'@type': 'messageVoiceNote'},
            },
        }

    async def call(self, method, *args, **kwargs):
        self.calls.append((method, args, kwargs))
        if method == 'get_me':
            return {
                'id': 42,
                'first_name': 'Test',
                'last_name': '',
                'usernames': {'active_usernames': ['test_user']},
                'type': {'@type': 'userTypeRegular'},
            }
        if method == 'get_user':
            return {
                'id': args[0],
                'first_name': f'User {args[0]}',
                'last_name': '',
                'usernames': {'active_usernames': [f'user_{args[0]}']},
                'type': {'@type': 'userTypeRegular'},
            }
        if method == 'get_chats':
            return {'total_count': 2, 'chat_ids': [10, 20]}
        if method == 'search_chats':
            return {'total_count': 1, 'chat_ids': [10]}
        if method == 'search_chat_messages':
            return {
                'total_count': 1,
                'messages': [
                    {
                        'id': 77,
                        'chat_id': 10,
                        'sender_id': {
                            '@type': 'messageSenderUser',
                            'user_id': 3,
                        },
                        'content': {
                            '@type': 'messageText',
                            'text': {'text': 'found'},
                        },
                    }
                ],
                'next_from_message_id': 66,
            }
        if method == 'search_messages':
            return {
                'total_count': 1,
                'messages': [],
                'next_offset': '',
            }
        if method == 'get_message':
            message = {
                'id': args[0],
                'chat_id': args[1],
                'sender_id': {
                    '@type': 'messageSenderUser',
                    'user_id': 3,
                },
                'content': {
                    '@type': 'messageText',
                    'text': {'text': 'target'},
                },
            }
            if args[0] == 88:
                message['topic_id'] = {
                    '@type': 'messageTopicForum',
                    'forum_topic_id': 7,
                }
            return message
        if method == 'get_chat_history':
            history_items = [
                {
                    'id': item_id,
                    'chat_id': args[0],
                    'sender_id': {
                        '@type': 'messageSenderUser',
                        'user_id': 3,
                    },
                    'content': {
                        '@type': 'messageText',
                        'text': {'text': 'context'},
                    },
                }
                for item_id in (77, 76, 78)
            ]
            return {
                'total_count': 2,
                'messages': history_items,
            }
        if method == 'get_forum_topic_history':
            return {
                'total_count': 3,
                'messages': [
                    {
                        'id': item_id,
                        'chat_id': args[0],
                        'topic_id': {
                            '@type': 'messageTopicForum',
                            'forum_topic_id': args[1],
                        },
                        'content': {
                            '@type': 'messageText',
                            'text': {'text': 'forum context'},
                        },
                    }
                    for item_id in (88, 87, 89)
                ],
            }
        if method == 'get_file':
            return {
                'id': 4,
                'size': 10,
                'expected_size': 10,
                'local': {'path': '/tmp/file', 'is_downloading_completed': True},
                'remote': {'id': 'remote-4'},
            }
        if method == 'download_file':
            return {
                'id': args[0],
                'size': 10,
                'local': {'path': '/tmp/file', 'is_downloading_completed': True},
                'remote': {},
            }
        if method == 'get_chat':
            return {
                'id': args[0],
                'title': f'Chat {args[0]}',
                'type': {'@type': 'chatTypePrivate'},
                'unread_count': 0,
            }
        if method == 'get_forum_topics':
            return {
                'total_count': 1,
                'topics': [],
                'next_offset_date': 0,
                'next_offset_message_id': 0,
                'next_offset_forum_topic_id': 0,
            }
        if method == 'send_message':
            return {
                'id': 99,
                'chat_id': args[0],
                'sender_id': {'@type': 'messageSenderUser', 'user_id': 42},
                'date': 123,
                'edit_date': 0,
                'is_outgoing': True,
                'content': {
                    '@type': 'messageText',
                    'text': {'text': kwargs['text']},
                },
            }
        if method == 'forward_messages':
            return {
                '@type': 'messages',
                'messages': [
                    {
                        'id': 101,
                        'chat_id': args[0],
                        'date': 123,
                        'is_outgoing': True,
                        'content': {
                            '@type': 'messageText',
                            'text': {'text': 'forwarded'},
                        },
                    },
                    None,
                ],
            }
        if method == 'add_message_reaction':
            return {'@type': 'ok'}
        if method == 'remove_message_reaction':
            return {'@type': 'ok'}
        if method == 'get_message_available_reactions':
            return {
                '@type': 'availableReactions',
                'top_reactions': [
                    {
                        'type': {
                            '@type': 'reactionTypeEmoji',
                            'emoji': '👍',
                        },
                        'needs_premium': False,
                    }
                ],
                'recent_reactions': [],
                'popular_reactions': [],
                'allow_custom_emoji': True,
                'are_tags': False,
                'unavailability_reason': None,
            }
        if method == 'get_message_added_reactions':
            return {
                '@type': 'addedReactions',
                'total_count': 1,
                'reactions': [
                    {
                        'type': {
                            '@type': 'reactionTypeEmoji',
                            'emoji': '👍',
                        },
                        'sender_id': {
                            '@type': 'messageSenderUser',
                            'user_id': 3,
                        },
                        'is_outgoing': True,
                        'date': 123,
                    }
                ],
                'next_offset': 'next',
            }
        raise AssertionError(method)


class ServerTestCase(TestCase):
    def test_registers_documented_tools_with_send_annotations(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            tools = asyncio.run(create_server(settings).list_tools())

        self.assertEqual(40, len(tools))
        tool_names = [tool.name for tool in tools]
        self.assertNotIn('view_messages', tool_names)
        self.assertIn('send_message', tool_names)
        self.assertIn('poll_updates', tool_names)
        self.assertIn('check_updates_subscription', tool_names)
        local_state_tools = {
            'subscribe_for_updates',
            'unsubscribe_from_updates',
            'commit_updates',
            'mark_messages_as_read',
            'send_message',
            'forward_messages',
            'request_message_transcript',
            'add_message_reaction',
            'remove_message_reaction',
        }
        self.assertTrue(
            all(
                tool.annotations.read_only_hint
                for tool in tools
                if tool.name not in local_state_tools
            )
        )
        send_tool = next(tool for tool in tools if tool.name == 'send_message')
        self.assertFalse(send_tool.annotations.read_only_hint)
        self.assertFalse(send_tool.annotations.idempotent_hint)
        forward_tool = next(tool for tool in tools if tool.name == 'forward_messages')
        self.assertFalse(forward_tool.annotations.read_only_hint)
        self.assertFalse(forward_tool.annotations.idempotent_hint)
        add_reaction_tool = next(
            tool for tool in tools if tool.name == 'add_message_reaction'
        )
        self.assertFalse(add_reaction_tool.annotations.read_only_hint)
        self.assertFalse(add_reaction_tool.annotations.idempotent_hint)
        history = next(tool for tool in tools if tool.name == 'get_chat_history')
        self.assertIn('oldest message ID', history.description)
        topic_history = next(
            tool for tool in tools if tool.name == 'get_forum_topic_history'
        )
        self.assertIn('oldest returned message ID', topic_history.description)
        message_bearing_tools = {
            'get_chat',
            'poll_updates',
            'get_chat_history',
            'get_chat_history_complete',
            'search_messages',
            'get_conversation_context',
            'get_forum_topics',
            'get_forum_topic',
            'get_forum_topic_history',
            'get_message_thread',
            'get_message_thread_history',
            'get_message',
            'request_message_transcript',
            'send_message',
            'forward_messages',
            'search_public_chat',
        }
        self.assertTrue(
            all(
                TELEGRAM_MESSAGE_DISCLAIMER in tool.description
                for tool in tools
                if tool.name in message_bearing_tools
            )
        )

    def test_request_message_transcript_returns_pending_status(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            result = asyncio.run(
                create_server(settings, runtime).call_tool(
                    'request_message_transcript',
                    {'chat_id': 10, 'message_id': 77},
                )
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(
            TELEGRAM_MESSAGE_DISCLAIMER, payload['telegram_message_disclaimer']
        )
        self.assertEqual('pending', payload['status'])
        self.assertEqual(10, payload['chat_id'])
        self.assertEqual(77, payload['message_id'])
        self.assertEqual(
            'messageVoiceNote', payload['original_message']['content_type']
        )

    def test_update_subscription_tools_manage_selected_chats(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            subscribed = awaitable_call(
                server, 'subscribe_for_updates', {'chat_ids': [10, 20, 10]}
            )
            state = awaitable_call(server, 'check_updates_subscription', {})
            unsubscribed = awaitable_call(
                server, 'unsubscribe_from_updates', {'chat_ids': [10]}
            )

        subscribed_payload = json.loads(subscribed.content[0].text)
        state_payload = json.loads(state.content[0].text)
        unsubscribed_payload = json.loads(unsubscribed.content[0].text)
        self.assertEqual([10, 20], subscribed_payload['subscribed_chat_ids'])
        self.assertEqual([10, 20], state_payload['subscribed_chat_ids'])
        self.assertEqual([20], unsubscribed_payload['subscribed_chat_ids'])

    def test_subscribe_for_updates_accepts_event_and_topic_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            awaitable_call(
                create_server(settings, runtime),
                'subscribe_for_updates',
                {
                    'chat_ids': [10],
                    'event_types': ['updateNewMessage', 'updateMessageEdited'],
                    'topic_ids': [7],
                },
            )

        self.assertEqual(
            [
                {
                    'event_types': {'updateNewMessage', 'updateMessageEdited'},
                    'topic_ids': {7},
                }
            ],
            runtime.subscription_kwargs,
        )

    def test_poll_updates_fails_immediately_without_subscription(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            with self.assertRaises(ToolError) as error:
                asyncio.run(
                    create_server(settings, runtime).call_tool(
                        'poll_updates', {'timeout': 300}
                    )
                )

        self.assertIn('no update subscriptions configured', str(error.exception))
        self.assertEqual([], runtime.poll_calls)

    def test_poll_and_commit_updates_use_one_event_and_cursor(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            awaitable_call(server, 'subscribe_for_updates', {'chat_ids': [10]})
            polled = awaitable_call(
                server,
                'poll_updates',
                {'timeout': 3, 'limit': 1, 'cursor': 2},
            )
            committed = awaitable_call(server, 'commit_updates', {'cursor': 5})

        payload = json.loads(polled.content[0].text)
        self.assertEqual(
            TELEGRAM_MESSAGE_DISCLAIMER, payload['telegram_message_disclaimer']
        )
        self.assertEqual(77, payload['update']['message']['id'])
        self.assertEqual([77], [item['message']['id'] for item in payload['updates']])
        self.assertEqual(5, payload['next_cursor'])
        self.assertFalse(payload['timed_out'])
        self.assertEqual([(3, 1, 2)], runtime.poll_calls)
        committed_payload = json.loads(committed.content[0].text)
        self.assertEqual(1, committed_payload['removed_count'])
        self.assertTrue(committed_payload['marked_as_read'])

    def test_mark_messages_as_read_deduplicates_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            result = awaitable_call(
                create_server(settings, runtime),
                'mark_messages_as_read',
                {'chat_id': 10, 'message_ids': [77, 78, 77]},
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(10, payload['chat_id'])
        self.assertEqual([77, 78], payload['marked_message_ids'])
        self.assertEqual(
            [('view_messages', (10, [77, 78, 77]), {'force_read': True})],
            runtime.calls,
        )

    def test_tool_returns_structured_compact_result(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            result = asyncio.run(
                create_server(settings, RuntimeStub()).call_tool('get_me', {})
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(42, payload['id'])
        self.assertEqual('test_user', payload['username'])

    def test_get_users_batches_and_deduplicates_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            result = asyncio.run(
                create_server(settings, runtime).call_tool(
                    'get_users', {'user_ids': [3, 2, 3]}
                )
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(2, payload['total_count'])
        self.assertEqual([3, 2], [user['id'] for user in payload['users']])
        self.assertEqual(
            [3, 2],
            [args[0] for method, args, _ in runtime.calls if method == 'get_user'],
        )

    def test_search_messages_returns_cursor_and_caches_sender_details(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            first = awaitable_call(
                server,
                'search_messages',
                {'query': 'found', 'chat_id': 10},
            )
            second = awaitable_call(
                server,
                'search_messages',
                {'query': 'found', 'chat_id': 10},
            )

        first_payload = json.loads(first.content[0].text)
        second_payload = json.loads(second.content[0].text)
        self.assertEqual(
            TELEGRAM_MESSAGE_DISCLAIMER,
            first_payload['telegram_message_disclaimer'],
        )
        self.assertEqual('{"from_message_id":66}', first_payload['next_cursor'])
        self.assertEqual(
            'User 3', first_payload['messages'][0]['sender_details']['first_name']
        )
        self.assertEqual(
            1,
            len([method for method, _, _ in runtime.calls if method == 'get_user']),
        )
        self.assertEqual(first_payload['messages'], second_payload['messages'])

    def test_context_and_file_tools_return_compact_results(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            context = awaitable_call(
                server,
                'get_conversation_context',
                {'chat_id': 10, 'message_id': 77, 'before': 1, 'after': 1},
            )
            forum_context = awaitable_call(
                server,
                'get_conversation_context',
                {'chat_id': 10, 'message_id': 88, 'before': 1, 'after': 1},
            )
            file_result = awaitable_call(server, 'get_file', {'file_id': 4})

        context_payload = json.loads(context.content[0].text)
        file_payload = json.loads(file_result.content[0].text)
        self.assertEqual(
            TELEGRAM_MESSAGE_DISCLAIMER,
            context_payload['telegram_message_disclaimer'],
        )
        self.assertEqual(77, context_payload['message']['id'])
        self.assertEqual(
            [76, 77, 78], [item['id'] for item in context_payload['messages']]
        )
        self.assertEqual(1, context_payload['before_count'])
        self.assertEqual(1, context_payload['after_count'])
        forum_payload = json.loads(forum_context.content[0].text)
        self.assertEqual(
            [87, 88, 89], [item['id'] for item in forum_payload['messages']]
        )
        self.assertTrue(
            all(
                item['topic_id']['forum_topic_id'] == 7
                for item in forum_payload['messages']
            )
        )
        self.assertEqual('/tmp/file', file_payload['local']['path'])

    def test_send_message_is_denied_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            with self.assertRaises(ToolError) as error:
                asyncio.run(
                    create_server(settings, runtime).call_tool(
                        'send_message', {'chat_id': 10, 'text': 'hello'}
                    )
                )

        self.assertIn('not allowed', str(error.exception))
        self.assertEqual([], runtime.calls)

    def test_send_message_uses_allowlist_and_topic_options(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                    'PYTDJSON_ALLOW_SEND_TO_CHATS': '10',
                }
            )
            runtime = RuntimeStub()
            result = asyncio.run(
                create_server(settings, runtime).call_tool(
                    'send_message',
                    {
                        'chat_id': 10,
                        'text': 'hello',
                        'forum_topic_id': 84427,
                        'reply_to_message_id': 99,
                    },
                )
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(
            TELEGRAM_MESSAGE_DISCLAIMER, payload['telegram_message_disclaimer']
        )
        self.assertEqual(99, payload['id'])
        self.assertEqual(
            (
                'send_message',
                (10,),
                {
                    'text': 'hello',
                    'message_thread_id': None,
                    'forum_topic_id': 84427,
                    'reply_to_message_id': 99,
                },
            ),
            runtime.calls[-1],
        )

    def test_reaction_tools_use_allowlist_and_tdlib_values(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                    'PYTDJSON_ALLOW_SEND_TO_CHATS': '10',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            added = awaitable_call(
                server,
                'add_message_reaction',
                {
                    'chat_id': 10,
                    'message_id': 77,
                    'reaction_type': 'emoji',
                    'value': '👍',
                    'is_big': True,
                    'update_recent_reactions': True,
                },
            )
            removed = awaitable_call(
                server,
                'remove_message_reaction',
                {
                    'chat_id': 10,
                    'message_id': 77,
                    'reaction_type': 'custom_emoji',
                    'value': '123456789',
                },
            )

        added_payload = json.loads(added.content[0].text)
        removed_payload = json.loads(removed.content[0].text)
        self.assertTrue(added_payload['ok'])
        self.assertEqual('add', added_payload['operation'])
        self.assertTrue(removed_payload['ok'])
        self.assertEqual(
            (
                'add_message_reaction',
                (10, 77, 'reactionTypeEmoji', '👍'),
                {'is_big': True, 'update_recent_reactions': True},
            ),
            runtime.calls[-2],
        )
        self.assertEqual(
            (
                'remove_message_reaction',
                (10, 77, 'reactionTypeCustomEmoji', 123456789),
                {},
            ),
            runtime.calls[-1],
        )

    def test_reactions_are_denied_without_target_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            with self.assertRaises(ToolError) as error:
                awaitable_call(
                    create_server(settings, runtime),
                    'add_message_reaction',
                    {
                        'chat_id': 10,
                        'message_id': 77,
                        'reaction_type': 'emoji',
                        'value': '👍',
                    },
                )

        self.assertIn('not allowed', str(error.exception))
        self.assertEqual([], runtime.calls)

    def test_reaction_read_tools_do_not_require_send_permission(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            available = awaitable_call(
                server,
                'get_message_available_reactions',
                {'chat_id': 10, 'message_id': 77},
            )
            added = awaitable_call(
                server,
                'get_message_added_reactions',
                {
                    'chat_id': 10,
                    'message_id': 77,
                    'reaction_type': 'emoji',
                    'value': '👍',
                    'offset': 'next-page',
                    'limit': 25,
                },
            )

        available_payload = json.loads(available.content[0].text)
        added_payload = json.loads(added.content[0].text)
        self.assertEqual(
            '👍', available_payload['top_reactions'][0]['reaction']['emoji']
        )
        self.assertEqual('next', added_payload['next_offset'])
        self.assertEqual(
            (
                'get_message_added_reactions',
                (10, 77),
                {
                    'reaction_type': 'reactionTypeEmoji',
                    'value': '👍',
                    'offset': 'next-page',
                    'limit': 25,
                },
            ),
            runtime.calls[-1],
        )

    def test_reactions_reject_paid_and_malformed_custom_values(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                    'PYTDJSON_ALLOW_SEND_TO_CHATS': '10',
                }
            )
            runtime = RuntimeStub()
            server = create_server(settings, runtime)
            for value in (
                {'reaction_type': 'paid', 'value': '1'},
                {'reaction_type': 'custom_emoji', 'value': 'not-an-id'},
            ):
                with self.assertRaises(ToolError):
                    awaitable_call(
                        server,
                        'add_message_reaction',
                        {'chat_id': 10, 'message_id': 77, **value},
                    )

        self.assertEqual([], runtime.calls)

    def test_forward_messages_is_denied_when_destination_is_not_allowlisted(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            runtime = RuntimeStub()
            with self.assertRaises(ToolError) as error:
                asyncio.run(
                    create_server(settings, runtime).call_tool(
                        'forward_messages',
                        {
                            'from_chat_id': 20,
                            'message_ids': [1],
                            'to_chat_id': 10,
                            'send_copy': True,
                        },
                    )
                )

        self.assertIn('not allowed', str(error.exception))
        self.assertEqual([], runtime.calls)

    def test_forward_messages_uses_allowlist_topic_and_reports_partial_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                    'PYTDJSON_ALLOW_SEND_TO_CHATS': '10',
                }
            )
            runtime = RuntimeStub()
            result = asyncio.run(
                create_server(settings, runtime).call_tool(
                    'forward_messages',
                    {
                        'from_chat_id': 20,
                        'message_ids': [1, 2],
                        'to_chat_id': 10,
                        'send_copy': True,
                        'forum_topic_id': 7,
                        'remove_caption': True,
                    },
                )
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(
            [101, None], [item['id'] if item else None for item in payload['messages']]
        )
        self.assertEqual([2], payload['failed_message_ids'])
        self.assertEqual(1, payload['forwarded_count'])
        self.assertEqual(1, payload['failed_count'])
        self.assertEqual(
            (
                'forward_messages',
                (10, 20, [1, 2]),
                {
                    'forum_topic_id': 7,
                    'send_copy': True,
                    'remove_caption': True,
                },
            ),
            runtime.calls[-1],
        )

    def test_forward_messages_rejects_non_increasing_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                    'PYTDJSON_ALLOW_SEND_TO_CHATS': '10',
                }
            )
            runtime = RuntimeStub()
            with self.assertRaises(ToolError) as error:
                asyncio.run(
                    create_server(settings, runtime).call_tool(
                        'forward_messages',
                        {
                            'from_chat_id': 20,
                            'message_ids': [2, 1],
                            'to_chat_id': 10,
                            'send_copy': True,
                        },
                    )
                )

        self.assertIn('strictly increasing', str(error.exception))
        self.assertEqual([], runtime.calls)

    def test_forward_messages_requires_explicit_send_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                    'PYTDJSON_ALLOW_SEND_TO_CHATS': '10',
                }
            )
            runtime = RuntimeStub()
            with self.assertRaises(ToolError):
                asyncio.run(
                    create_server(settings, runtime).call_tool(
                        'forward_messages',
                        {
                            'from_chat_id': 20,
                            'message_ids': [1],
                            'to_chat_id': 10,
                        },
                    )
                )

        self.assertEqual([], runtime.calls)

    def test_get_chats_returns_compact_chat_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            result = asyncio.run(
                create_server(settings, RuntimeStub()).call_tool('get_chats', {})
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(2, payload['total_count'])
        self.assertEqual(
            [
                {
                    'id': 10,
                    'title': 'Chat 10',
                    'type': 'chatTypePrivate',
                    'is_channel': None,
                    'unread_count': 0,
                },
                {
                    'id': 20,
                    'title': 'Chat 20',
                    'type': 'chatTypePrivate',
                    'is_channel': None,
                    'unread_count': 0,
                },
            ],
            payload['chats'],
        )

    def test_get_forum_topics_returns_compact_topic_list(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': directory,
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )
            result = asyncio.run(
                create_server(settings, RuntimeStub()).call_tool(
                    'get_forum_topics', {'chat_id': 1}
                )
            )

        payload = json.loads(result.content[0].text)
        self.assertEqual(1, payload['total_count'])
        self.assertEqual(
            {'date': 0, 'message_id': 0, 'forum_topic_id': 0},
            payload['next_offset'],
        )
