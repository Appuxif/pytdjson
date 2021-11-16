from unittest import TestCase
from unittest.mock import patch

from telegram.types.files import File
from telegram.types.update import (
    AuthorizationState,
    UpdateAuthorizationState,
    UpdateFile,
    UpdateNewMessage,
    build_update,
)


class MessageTypeTestCase(TestCase):
    """
    Тест кейс для объекта Message
    """

    def test_not_valid_update(self):
        """Обновление не валидно"""
        update_dict = {'@type': 'notValidUpdate'}

        with self.assertRaises(KeyError):
            build_update(update_dict)

    @patch('telegram.types.update.build_message', return_value='fake_message_obj')
    def test_update_new_message(self, *args):
        """Обновление updateNewMessage"""
        update_dict = {'@type': 'updateNewMessage', 'message': 'fake_message_obj'}

        update = build_update(update_dict)

        self.assertIsInstance(update, UpdateNewMessage)
        self.assertEqual('fake_message_obj', update.message)

    def test_update_authorization_state(self):
        """Обновление updateAuthorizationState"""
        update_dict = {
            '@type': 'updateAuthorizationState',
            'authorization_state': {
                '@type': 'authorizationStateClosed',
            },
        }

        update = build_update(update_dict)

        self.assertIsInstance(update, UpdateAuthorizationState)
        self.assertIsInstance(update.authorization_state, AuthorizationState)
        self.assertEqual(update.authorization_state, AuthorizationState.CLOSED)

    def test_update_file(self):
        """Обновление updateFile"""

        update_dict = {
            '@type': 'updateFile',
            'file': {
                'id': 1,
                'size': 456,
                'expected_size': 456,
                'local': {'path': 'local-path'},
                'remote': {'id': 2, 'unique_id': 3},
            },
        }

        update = build_update(update_dict)

        self.assertIsInstance(update, UpdateFile)
        self.assertIsInstance(update.file, File)
        self.assertEqual(update.file.id, 1)
        self.assertEqual(update.file.size, 456)
        self.assertEqual(update.file.expected_size, 456)
        self.assertEqual(update.file.local_path, 'local-path')
        self.assertEqual(update.file.remote_id, 2)
        self.assertEqual(update.file.remote_unique_id, 3)
