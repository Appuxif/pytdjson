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
