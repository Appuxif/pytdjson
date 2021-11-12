from unittest import TestCase
from unittest.mock import patch

from telegram.types.update import UpdateNewMessage, build_update


@patch('telegram.types.update.build_message', return_value='fake_message_obj')
class MessageTypeTestCase(TestCase):
    """
    Тест кейс для объекта Message
    """

    def test_update_to_message(self, *args):
        """Преобразование обновления от телеграм в объект Message"""
        update_dict = {'@type': 'updateNewMessage', 'message': 'fake_message_obj'}

        update = build_update(update_dict)

        self.assertIsInstance(update, UpdateNewMessage)
        self.assertEqual('fake_message_obj', update.message)
