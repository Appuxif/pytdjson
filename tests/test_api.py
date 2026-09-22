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

    def test_search_chats_uses_local_or_server_method(self):
        self.api.search_chats('Darina', limit=7)
        self.assertEqual(
            {
                '@type': 'searchChats',
                'query': 'Darina',
                'type_filter': None,
                'limit': 7,
            },
            self.client.query,
        )

        self.api.search_chats('Darina', limit=7, on_server=True)
        self.assertEqual('searchChatsOnServer', self.client.query['@type'])

    def test_search_messages_builds_chat_and_global_requests(self):
        self.api.search_chat_messages(
            1,
            query='hello',
            topic_id=9,
            sender_id=3,
            from_message_id=8,
            limit=20,
            filter_type='searchMessagesFilterVoiceNote',
        )
        self.assertEqual(
            {
                '@type': 'searchChatMessages',
                'chat_id': 1,
                'topic_id': {
                    '@type': 'messageTopicForum',
                    'forum_topic_id': 9,
                },
                'query': 'hello',
                'sender_id': {
                    '@type': 'messageSenderUser',
                    'user_id': 3,
                },
                'from_message_id': 8,
                'offset': 0,
                'limit': 20,
                'filter': {'@type': 'searchMessagesFilterVoiceNote'},
            },
            self.client.query,
        )

        self.api.search_messages('hello', offset='next', chat_list=None)
        self.assertEqual(
            {
                '@type': 'searchMessages',
                'chat_list': None,
                'query': 'hello',
                'offset': 'next',
                'limit': 100,
                'filter': None,
                'chat_type_filter': None,
                'min_date': 0,
                'max_date': 0,
            },
            self.client.query,
        )

    def test_file_methods_use_tdlib_file_requests(self):
        self.api.get_file(4)
        self.assertEqual({'@type': 'getFile', 'file_id': 4}, self.client.query)
        self.api.download_file(4, priority=8, synchronous=True)
        self.assertEqual(
            {
                '@type': 'downloadFile',
                'file_id': 4,
                'priority': 8,
                'offset': 0,
                'limit': 0,
                'synchronous': True,
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

    def test_speech_recognition_uses_tdlib_methods(self):
        self.api.get_message_properties(1, 2)
        self.assertEqual(
            {
                '@type': 'getMessageProperties',
                'chat_id': 1,
                'message_id': 2,
            },
            self.client.query,
        )

        self.api.recognize_speech(1, 2)
        self.assertEqual(
            {
                '@type': 'recognizeSpeech',
                'chat_id': 1,
                'message_id': 2,
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

    def test_forward_messages_uses_forum_topic_and_preserves_options(self):
        self.api.forward_messages(
            1,
            2,
            [10, 11],
            disable_notification=True,
            send_copy=True,
            remove_caption=True,
            forum_topic_id=84427,
        )

        self.assertEqual(
            {
                '@type': 'forwardMessages',
                'chat_id': 1,
                'topic_id': {
                    '@type': 'messageTopicForum',
                    'forum_topic_id': 84427,
                },
                'from_chat_id': 2,
                'message_ids': [10, 11],
                'options': {
                    'disable_notification': True,
                    'type': 'messageSendOptions',
                },
                'send_copy': True,
                'remove_caption': True,
            },
            self.client.query,
        )

    def test_forward_messages_rejects_non_forum_thread_and_invalid_ids(self):
        with self.assertRaisesRegex(ValueError, 'message_thread_id'):
            self.api.forward_messages(1, 2, [10], message_thread_id=7)

        with self.assertRaisesRegex(ValueError, 'strictly increasing'):
            self.api.forward_messages(1, 2, [10, 10])

    def test_forward_messages_without_forum_topic_uses_no_topic(self):
        self.api.forward_messages(1, 2, [10], send_copy=False)

        self.assertEqual(
            {
                '@type': 'forwardMessages',
                'chat_id': 1,
                'topic_id': None,
                'from_chat_id': 2,
                'message_ids': [10],
                'options': {},
                'send_copy': False,
                'remove_caption': False,
            },
            self.client.query,
        )
