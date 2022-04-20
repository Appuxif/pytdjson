from unittest import TestCase
from unittest.mock import patch

from telegram.types.base import RawDataclass
from telegram.types.chat import ChatType
from telegram.types.files import File
from telegram.types.message import MessageSenderType
from telegram.types.update import (
    AuthorizationState,
    Update,
    UpdateAuthorizationState,
    UpdateFile,
    UpdateNewChat,
    UpdateNewMessage,
    UpdateSupergroup,
    UpdateUser,
    UpdateUserFullInfo,
)
from telegram.types.user import UserType


class UpdateTestCase(TestCase):
    """
    Тест кейс для объекта Update
    """

    def test_not_valid_update(self):
        """Неизвестный объект возвращает RawDataclass"""
        update_dict = {'@type': 'notValidUpdate'}

        update = Update(update_dict)

        self.assertIsInstance(update, RawDataclass)
        self.assertDictEqual(update.raw, update_dict)

    @patch('telegram.types.update.Message', return_value='fake_message_obj')
    def test_update_new_message(self, *args):
        """Обновление updateNewMessage"""
        update_dict = {
            '@type': 'updateNewMessage',
            'message': {'@type': 'fake_message_obj'},
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateNewMessage)
        self.assertEqual('fake_message_obj', update.message.raw['@type'])
        self.assertIsNone(update.message.id)

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

    def test_update_new_chat(self):
        """Обновление updateNewChat"""

        update_dict = {
            '@type': 'updateNewChat',
            'chat': {
                '@type': 'fake_chat_obj',
                'type': {'@type': 'chatTypePrivate', 'user_id': 1},
                'permissions': {
                    '@type': 'chatPermissions',
                    'can_send_messages': True,
                },
            },
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateNewChat)
        self.assertEqual('fake_chat_obj', update.chat.raw['@type'])
        self.assertEqual(ChatType.PRIVATE, update.chat.type)
        self.assertEqual(1, update.chat.user_id)
        self.assertTrue(update.chat.permissions.can_send_messages)
        self.assertIsNone(update.chat.id)

    def test_update_new_chat_with_photo(self):
        """Обновление updateNewChat с фото"""

        update_dict = {
            '@type': 'updateNewChat',
            'chat': {
                '@type': 'fake_chat_obj',
                'type': {'@type': 'chatTypePrivate', 'user_id': 1},
                'permissions': {
                    '@type': 'chatPermissions',
                    'can_send_messages': True,
                },
                'photo': {
                    '@type': 'chatPhotoInfo',
                    'small': {
                        'local': {'path': 'testpath'},
                        'remote': {'id': 'remote-id', 'unique_id': 'remote-unique-id'},
                    },
                },
            },
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateNewChat)
        self.assertIsNone(update.chat.photo.big)
        self.assertEqual('testpath', update.chat.photo.small.local_path)
        self.assertEqual('remote-id', update.chat.photo.small.remote_id)
        self.assertEqual('remote-unique-id', update.chat.photo.small.remote_unique_id)

    def test_update_new_chat_with_message_sender(self):
        """Обновление updateNewChat с отправителем"""

        update_dict = {
            '@type': 'updateNewChat',
            'chat': {
                '@type': 'fake_chat_obj',
                'type': {'@type': 'chatTypePrivate', 'user_id': 1},
                'permissions': {
                    '@type': 'chatPermissions',
                    'can_send_messages': True,
                },
                'message_sender_id': {
                    '@type': 'messageSenderUser',
                    'user_id': 1,
                },
            },
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateNewChat)
        self.assertEqual(MessageSenderType.USER, update.chat.message_sender.type)
        self.assertEqual(1, update.chat.message_sender.id)

    def test_update_user(self):
        """Обновление updateUser"""

        update_dict = {
            '@type': 'updateUser',
            'user': {
                '@type': 'user',
                'id': 1,
                'have_access': True,
                'is_fake': False,
                'type': {'@type': 'userTypeRegular'},
            },
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateUser)
        self.assertEqual(1, update.user.id)
        self.assertIsNone(update.user.first_name)
        self.assertEqual(UserType.REGULAR, update.user.type)
        self.assertTrue(update.user.have_access)
        self.assertFalse(update.user.is_fake)

    def test_update_user_full_info(self):
        """Обновление updateUserFullInfo"""

        update_dict = {
            '@type': 'updateUserFullInfo',
            'user_id': 1,
            'user_full_info': {
                '@type': 'userFullInfo',
                'is_blocked': True,
                'bio': 'test-bio',
            },
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateUserFullInfo)
        self.assertEqual(1, update.user_id)
        self.assertTrue(update.user_full_info.is_blocked)
        self.assertEqual('test-bio', update.user_full_info.bio)

    def test_update_supergroup(self):
        """Обновление updateSupergroup"""

        update_dict = {
            '@type': 'updateSupergroup',
            'supergroup': {
                '@type': 'supergroup',
                'id': 1,
                'username': 'test-username',
            },
        }

        update = Update(update_dict)

        self.assertIsInstance(update, UpdateSupergroup)
        self.assertEqual(1, update.supergroup.id)
        self.assertEqual('test-username', update.supergroup.username)
