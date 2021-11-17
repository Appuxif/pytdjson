from copy import deepcopy
from unittest import TestCase

from telegram.types.message_content import MessageContent, MessageText
from telegram.types.text import FormattedText, TextEntity, TextEntityType

content_message_text = {
    '@type': 'messageText',
    'text': {
        'text': '+79999999999',
        'entities': [
            {
                'offset': 0,
                'length': 12,
                'type': {'@type': 'textEntityTypePhoneNumber'},
            },
        ],
    },
}


class MessageTextTestCase(TestCase):
    """
    Тест кейс для объекта MessageText
    """

    def test_no_entities(self):
        """Форматирования нет"""

        content_dict = deepcopy(content_message_text)
        content_dict['text']['entities'] = []

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessageText)
        self.assertIsInstance(content.text, FormattedText)
        self.assertIsInstance(content.text.entities, list)
        self.assertEqual(content.text.text, '+79999999999')
        self.assertListEqual(content.text.entities, [])

    def test_phone_number_entities(self):
        """Номер телефона в форматировании"""

        content_dict = deepcopy(content_message_text)

        content = MessageContent(content_dict)

        self.assertEqual(content.text.text, '+79999999999')
        entity = content.text.entities[0]
        self.assertIsInstance(entity, TextEntity)
        self.assertEqual(entity.type, TextEntityType.PHONE_NUMBER)
        self.assertEqual(entity.offset, 0)
        self.assertEqual(entity.length, 12)
        self.assertIsNone(entity.user_id)
        self.assertIsNone(entity.language)
        self.assertIsNone(entity.url)

    def test_mention_name_entities(self):
        """Упоминание пользователя в форматировании"""

        content_dict = deepcopy(content_message_text)
        content_dict['text']['entities'][0]['type'] = {  # noqa
            '@type': 'textEntityTypeMentionName',
            'user_id': 123123,
        }

        content = MessageContent(content_dict)

        self.assertEqual(content.text.text, '+79999999999')
        entity = content.text.entities[0]
        self.assertIsInstance(entity, TextEntity)
        self.assertEqual(entity.type, TextEntityType.MENTION_NAME)
        self.assertEqual(entity.user_id, 123123)
        self.assertIsNone(entity.language)
        self.assertIsNone(entity.url)
