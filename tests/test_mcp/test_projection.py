from unittest import TestCase

from telegram.mcp import projection


class ProjectionTestCase(TestCase):
    def test_message_keeps_only_compact_content(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'sender_id': {'@type': 'messageSenderUser', 'user_id': 3},
                'date': 4,
                'content': {
                    '@type': 'messageText',
                    'text': {'text': 'hello', 'entities': [{'ignored': True}]},
                },
                'reply_markup': {'secret': 'not returned'},
            }
        )

        self.assertEqual('hello', result['text'])
        self.assertEqual({'type': 'messageSenderUser', 'user_id': 3}, result['sender'])
        self.assertNotIn('reply_markup', result)
