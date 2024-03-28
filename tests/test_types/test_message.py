from copy import deepcopy
from unittest import TestCase

from telegram.types.message import Message, MessageForwardInfo
from telegram.types.message_content import MessageText
from telegram.types.message_sender import MessageSenderType

message_base = {
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
    'content': {'@type': 'fake-message-content'},
}
message_with_forward_info = {
    **message_base,
    'forward_info': {
        'origin': {},
        'date': 1636692739,
        'from_chat_id': 1,
        'from_message_id': 2,
    },
}
message_sender_chat = {
    **message_base,
    'sender': {'@type': 'messageSenderChat', 'chat_id': 1394101816},
}


class MessageTestCase(TestCase):
    """
    Тест кейс для объекта Message
    """

    def test_message(self):
        """Построение Message"""
        message_dict = deepcopy(message_base)

        message = Message(message_dict)

        self.assertEqual(166121701376, message.id)
        self.assertEqual(-1001236427904, message.chat_id)
        self.assertFalse(message.is_outgoing)
        self.assertIsInstance(message.raw, dict)
        self.assertIsInstance(message.raw['interaction_info'], dict)
        self.assertEqual(message.content.raw['@type'], 'fake-message-content')

    def test_message_with_content(self):
        """Построение Message"""
        message_dict = deepcopy(message_base)
        message_dict['content'] = {
            '@type': 'messageText',
            'text': {
                '@type': 'formattedText',
                'text': 'test-text',
                'entities': [],
            },
        }

        message = Message(message_dict)

        self.assertIsInstance(message.content, MessageText)
        self.assertEqual('messageText', message.content.raw['@type'])
        self.assertEqual('test-text', message.content.text.text)
        self.assertListEqual([], message.content.text.entities)

    def test_message_with_forward_info(self):
        """Построение Message с ForwardInfo"""
        message_dict = deepcopy(message_with_forward_info)

        message = Message(message_dict)

        self.assertIsInstance(message.forward_info, MessageForwardInfo)
        self.assertIsInstance(message.forward_info.raw, dict)
        self.assertIsInstance(message.forward_info.raw['origin'], dict)
        self.assertEqual(1636692739, message.forward_info.date)
        self.assertEqual(1, message.forward_info.from_chat_id)
        self.assertEqual(2, message.forward_info.from_message_id)

    def test_message_sender_user(self):
        """Проверка messageSenderUser в Message"""
        message_dict = deepcopy(message_base)

        message = Message(message_dict)

        self.assertEqual(MessageSenderType.USER, message.sender.type)
        self.assertEqual(1394101816, message.sender.id)

    def test_message_sender_chat(self):
        """Проверка messageSenderChat в Message"""
        message_dict = deepcopy(message_sender_chat)

        message = Message(message_dict)

        self.assertEqual(MessageSenderType.CHAT, message.sender.type)
        self.assertEqual(1394101816, message.sender.id)

    def test_message_sender_backward_compatibility(self):
        """Проверка messageSenderChat в Message.
        С версий 1.8.х объект приходит в поле sender_id, вместо sender,
        но в итоговом классе должен быть sender, как и раньше
        """
        message_dict = deepcopy(message_sender_chat)
        message_dict['sender_id'] = message_dict.pop('sender')

        message = Message(message_dict)

        self.assertEqual(MessageSenderType.CHAT, message.sender.type)
        self.assertEqual(1394101816, message.sender.id)
