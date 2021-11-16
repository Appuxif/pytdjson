from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from telegram.types.message import Message, MessageForwardInfo, MessageSenderType

message1 = {
    '@type': 'message',
    'id': 166121701376,
    'sender': {'@type': 'messageSenderUser', 'user_id': 1394101816},
    'chat_id': -1001236427904,
    'is_outgoing': False,
    'is_pinned': False,
    'can_be_edited': False,
    'can_be_forwarded': True,
    'can_be_deleted_only_for_self': False,
    'can_be_deleted_for_all_users': False,
    'can_get_statistics': False,
    'can_get_message_thread': True,
    'is_channel_post': False,
    'contains_unread_mention': False,
    'date': 1636692739,
    'edit_date': 0,
    'interaction_info': {
        '@type': 'messageInteractionInfo',
        'view_count': 0,
        'forward_count': 0,
        'reply_info': {
            '@type': 'messageReplyInfo',
            'reply_count': 0,
            'recent_repliers': [],
            'last_read_inbox_message_id': 0,
            'last_read_outbox_message_id': 0,
            'last_message_id': 0,
        },
    },
    'reply_in_chat_id': 0,
    'reply_to_message_id': 0,
    'message_thread_id': 166121701376,
    'ttl': 0,
    'ttl_expires_in': 0.0,
    'via_bot_user_id': 0,
    'author_signature': '',
    'media_album_id': '0',
    'restriction_reason': '',
    'content': 'fake_message_content',
}
message2 = {
    **message1,
    'forward_info': {
        'origin': {},
        'date': 1636692739,
        'from_chat_id': 1,
        'from_message_id': 2,
    },
}


patch_build_message_content = patch(
    target='telegram.types.message.build_message_content',
    return_value='fake_message_content',
)


@patch_build_message_content
class MessageTestCase(TestCase):
    """
    Тест кейс для объекта Message
    """

    def test_message(self, *args):
        """Построение Message"""
        message_dict = deepcopy(message1)

        message = Message(message_dict)

        self.assertEqual(166121701376, message.id)
        self.assertEqual(-1001236427904, message.chat_id)
        self.assertEqual(MessageSenderType.USER, message.sender.type)
        self.assertEqual(1394101816, message.sender.id)
        self.assertFalse(message.is_outgoing)
        self.assertIsInstance(message.raw, dict)
        self.assertIsInstance(message.raw['interaction_info'], dict)
        self.assertEqual(message.content, 'fake_message_content')

    def test_message_with_forward_info(self, *args):
        """Построение Message с ForwardInfo"""
        message_dict = deepcopy(message2)

        message = Message(message_dict)

        self.assertIsInstance(message.forward_info, MessageForwardInfo)
        self.assertIsInstance(message.forward_info.raw, dict)
        self.assertIsInstance(message.forward_info.raw['origin'], dict)
        self.assertEqual(1636692739, message.forward_info.date)
        self.assertEqual(1, message.forward_info.from_chat_id)
        self.assertEqual(2, message.forward_info.from_message_id)
