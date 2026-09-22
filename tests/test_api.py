from unittest import TestCase

from telegram.api import API


class ClientStub:
    def send_data(self, query, request_id=None, timeout=None):
        self.query = query
        self.request_id = request_id
        self.timeout = timeout
        return query


class ApiTestCase(TestCase):
    def setUp(self):
        self.client = ClientStub()
        self.api = API(self.client)

    def test_get_message_link_uses_tdlib_1_8_67_defaults(self):
        self.api.get_message_link(1, 2)

        self.assertEqual(
            {
                '@type': 'getMessageLink',
                'chat_id': 1,
                'message_id': 2,
                'media_timestamp': 0,
                'checklist_task_id': 0,
                'poll_option_id': '',
                'for_album': False,
                'in_message_thread': False,
            },
            self.client.query,
        )

    def test_forum_topics_uses_tdlib_pagination_fields(self):
        self.api.get_forum_topics(
            1,
            query='residence',
            offset_date=10,
            offset_message_id=20,
            offset_forum_topic_id=30,
            limit=40,
        )

        self.assertEqual(
            {
                '@type': 'getForumTopics',
                'chat_id': 1,
                'query': 'residence',
                'offset_date': 10,
                'offset_message_id': 20,
                'offset_forum_topic_id': 30,
                'limit': 40,
            },
            self.client.query,
        )

    def test_forum_topic_history_uses_topic_and_message_pagination(self):
        self.api.get_forum_topic_history(
            1,
            2,
            limit=40,
            from_message_id=30,
            offset=-4,
        )

        self.assertEqual(
            {
                '@type': 'getForumTopicHistory',
                'chat_id': 1,
                'forum_topic_id': 2,
                'from_message_id': 30,
                'offset': -4,
                'limit': 40,
            },
            self.client.query,
        )

    def test_forum_topic_and_message_thread_metadata_requests(self):
        self.api.get_forum_topic(1, 2)
        self.assertEqual(
            {
                '@type': 'getForumTopic',
                'chat_id': 1,
                'forum_topic_id': 2,
            },
            self.client.query,
        )

        self.api.get_message_thread(1, 2)
        self.assertEqual(
            {
                '@type': 'getMessageThread',
                'chat_id': 1,
                'message_id': 2,
            },
            self.client.query,
        )

    def test_message_thread_history_uses_root_message_and_pagination(self):
        self.api.get_message_thread_history(
            1,
            2,
            limit=40,
            from_message_id=30,
            offset=-4,
        )

        self.assertEqual(
            {
                '@type': 'getMessageThreadHistory',
                'chat_id': 1,
                'message_id': 2,
                'from_message_id': 30,
                'offset': -4,
                'limit': 40,
            },
            self.client.query,
        )

    def test_send_message_uses_forum_topic(self):
        self.api.send_message(
            1,
            'hello',
            forum_topic_id=84427,
            reply_to_message_id=99,
        )

        self.assertEqual(
            {
                '@type': 'sendMessage',
                'chat_id': 1,
                'topic_id': {
                    '@type': 'messageTopicForum',
                    'forum_topic_id': 84427,
                },
                'reply_to': {
                    '@type': 'inputMessageReplyToMessage',
                    'checklist_task_id': 0,
                    'poll_option_id': '',
                    'message_id': 99,
                    'quote': None,
                },
                'input_message_content': {
                    '@type': 'inputMessageText',
                    'text': {'@type': 'formattedText', 'text': 'hello'},
                    'link_preview_options': {
                        '@type': 'linkPreviewOptions',
                        'is_disabled': True,
                    },
                    'clear_draft': True,
                },
                'options': {},
            },
            self.client.query,
        )
