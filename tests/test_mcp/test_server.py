import asyncio
import json
import tempfile
from unittest import TestCase

from mcp.server.mcpserver.exceptions import ToolError

from telegram.mcp.config import load_settings
from telegram.mcp.server import create_server


class RuntimeStub:
    def __init__(self):
        self.calls = []

    async def start(self):
        pass

    async def stop(self):
        pass

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

        self.assertEqual(22, len(tools))
        tool_names = [tool.name for tool in tools]
        self.assertNotIn('view_messages', tool_names)
        self.assertIn('send_message', tool_names)
        self.assertTrue(
            all(
                tool.annotations.read_only_hint
                for tool in tools
                if tool.name != 'send_message'
            )
        )
        send_tool = next(tool for tool in tools if tool.name == 'send_message')
        self.assertFalse(send_tool.annotations.read_only_hint)
        self.assertFalse(send_tool.annotations.idempotent_hint)
        history = next(tool for tool in tools if tool.name == 'get_chat_history')
        self.assertIn('oldest message ID', history.description)
        topic_history = next(
            tool for tool in tools if tool.name == 'get_forum_topic_history'
        )
        self.assertIn('oldest returned message ID', topic_history.description)

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
