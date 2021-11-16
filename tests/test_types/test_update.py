from unittest import TestCase
from unittest.mock import patch

from telegram.types.files import File
from telegram.types.update import (
    AuthorizationState,
    Update,
    UpdateAuthorizationState,
    UpdateFile,
    UpdateNewMessage,
)


class UpdateTestCase(TestCase):
    """
    Тест кейс для объекта Update
    """

    def test_not_valid_update(self):
        """Обновление не валидно"""
        update_dict = {'@type': 'notValidUpdate'}

        with self.assertRaises(KeyError):
            Update(update_dict)

    @patch('telegram.types.update.Message', return_value='fake_message_obj')
    def test_update_new_message(self, *args):
        """Обновление updateNewMessage"""
        update_dict = {'@type': 'updateNewMessage', 'message': 'fake_message_obj'}

        update = Update(update_dict)

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

        update = Update(update_dict)

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

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateFile)
        self.assertIsInstance(update.file, File)
        self.assertEqual(update.file.id, 1)
        self.assertEqual(update.file.size, 456)
        self.assertEqual(update.file.expected_size, 456)
        self.assertEqual(update.file.local_path, 'local-path')
        self.assertEqual(update.file.remote_id, 2)
        self.assertEqual(update.file.remote_unique_id, 3)
