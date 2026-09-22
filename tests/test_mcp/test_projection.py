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

    def test_message_preserves_topic_and_reply_metadata(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'sender_id': {'@type': 'messageSenderUser', 'user_id': 3},
                'topic_id': {
                    '@type': 'messageTopicForum',
                    'forum_topic_id': 7,
                },
                'reply_to': {
                    '@type': 'messageReplyToMessage',
                    'chat_id': 1,
                    'message_id': 6,
                },
                'content': {'@type': 'messageText', 'text': {'text': 'hello'}},
            }
        )

        self.assertEqual(
            {'type': 'messageTopicForum', 'forum_topic_id': 7},
            result['topic_id'],
        )
        self.assertEqual(
            {'type': 'messageReplyToMessage', 'chat_id': 1, 'message_id': 6},
            result['reply_to'],
        )

    def test_message_exposes_sticker_as_emoji_without_file_data(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'content': {
                    '@type': 'messageSticker',
                    'is_premium': True,
                    'sticker': {
                        'id': 123,
                        'set_id': 456,
                        'emoji': '😂',
                        'sticker': {'id': 789},
                    },
                },
            }
        )

        self.assertEqual('😂', result['text'])
        self.assertEqual('😂', result['sticker_emoji'])
        self.assertEqual(123, result['sticker_id'])
        self.assertEqual(456, result['sticker_set_id'])
        self.assertTrue(result['sticker_is_premium'])
        self.assertNotIn('sticker', result)

    def test_forum_topics_projection_keeps_topic_identity_and_cursor(self):
        result = projection.forum_topics(
            {
                'total_count': 8,
                'topics': [
                    {
                        'info': {
                            'chat_id': 1,
                            'forum_topic_id': 7,
                            'name': 'Residence',
                            'icon': {'color': 12, 'custom_emoji_id': 0},
                            'creator_id': {
                                '@type': 'messageSenderUser',
                                'user_id': 3,
                            },
                            'is_general': False,
                            'is_closed': False,
                        },
                        'last_message': {
                            'id': 9,
                            'chat_id': 1,
                            'content': {
                                '@type': 'messageText',
                                'text': {'text': 'latest'},
                            },
                        },
                        'order': 10,
                        'is_pinned': True,
                        'unread_count': 2,
                    }
                ],
                'next_offset_date': 11,
                'next_offset_message_id': 12,
                'next_offset_forum_topic_id': 13,
            }
        )

        self.assertEqual(8, result['total_count'])
        self.assertEqual(7, result['topics'][0]['forum_topic_id'])
        self.assertEqual('Residence', result['topics'][0]['name'])
        self.assertEqual('latest', result['topics'][0]['last_message']['text'])
        self.assertEqual(
            {'date': 11, 'message_id': 12, 'forum_topic_id': 13},
            result['next_offset'],
        )

    def test_message_thread_projection_keeps_metadata_and_messages(self):
        result = projection.message_thread(
            {
                'chat_id': 1,
                'message_thread_id': 5,
                'reply_info': {
                    'reply_count': 2,
                    'recent_replier_ids': [
                        {'@type': 'messageSenderUser', 'user_id': 3}
                    ],
                    'last_message_id': 9,
                },
                'unread_message_count': 1,
                'messages': [
                    {
                        'id': 9,
                        'chat_id': 1,
                        'content': {
                            '@type': 'messageText',
                            'text': {'text': 'reply'},
                        },
                    }
                ],
            }
        )

        self.assertEqual(5, result['message_thread_id'])
        self.assertEqual(2, result['reply_info']['reply_count'])
        self.assertEqual('reply', result['messages'][0]['text'])
