import asyncio
import json
import tempfile
from unittest import TestCase

from telegram.mcp.config import load_settings
from telegram.mcp.server import create_server


class RuntimeStub:
    async def start(self):
        pass

    async def stop(self):
        pass

    async def call(self, method, *args, **kwargs):
        if method == 'get_me':
            return {
                'id': 42,
                'first_name': 'Test',
                'last_name': '',
                'usernames': {'active_usernames': ['test_user']},
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
        raise AssertionError(method)


class ServerTestCase(TestCase):
    def test_registers_only_documented_read_only_tools(self):
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

        self.assertEqual(20, len(tools))
        self.assertNotIn('view_messages', [tool.name for tool in tools])
        self.assertTrue(all(tool.annotations.read_only_hint for tool in tools))
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
