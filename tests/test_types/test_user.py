from copy import deepcopy
from unittest import TestCase

from telegram.types.user import User, UserStatus, UserType

user_base = {
    '@type': 'user',
    'id': 4111111123,
    'first_name': 'FirstName',
    'last_name': 'LastName',
    'username': 'username',
    'phone_number': '79231111111',
    'status': {'@type': 'userStatusOnline', 'expires': 1642749142},
    'profile_photo': {
        '@type': 'profilePhoto',
        'id': '5464864564486453705',
        'small': {
            '@type': 'file',
            'id': 777,
            'size': 0,
            'expected_size': 0,
            'local': {
                '@type': 'localFile',
                'path': '',
                'can_be_downloaded': True,
                'can_be_deleted': False,
                'is_downloading_active': False,
                'is_downloading_completed': False,
                'download_offset': 0,
                'downloaded_prefix_size': 0,
                'downloaded_size': 0,
            },
            'remote': {
                '@type': 'remoteFile',
                'id': 'AQADAgADqacxGxDbwRkACAIAAxDbwRkABEy3GnwiU0F6IgQ',
                'unique_id': 'AQADqacxGxDbwRkAAQ',
                'is_uploading_active': False,
                'is_uploading_completed': True,
                'uploaded_size': 0,
            },
        },
        'big': {
            '@type': 'file',
            'id': 777,
            'size': 0,
            'expected_size': 0,
            'local': {
                '@type': 'localFile',
                'path': '',
                'can_be_downloaded': True,
                'can_be_deleted': False,
                'is_downloading_active': False,
                'is_downloading_completed': False,
                'download_offset': 0,
                'downloaded_prefix_size': 0,
                'downloaded_size': 0,
            },
            'remote': {
                '@type': 'remoteFile',
                'id': 'AQADAgADqacxGxDbwRkACAMAAxDbwRkABEy3GnwiU0F6IgQ',
                'unique_id': 'AQADqacxGxDbwRkB',
                'is_uploading_active': False,
                'is_uploading_completed': True,
                'uploaded_size': 0,
            },
        },
        'minithumbnail': {
            '@type': 'minithumbnail',
            'width': 8,
            'height': 8,
            'data': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDACgcHiMeGSgjISMtKygwPGRBPDc3PHtYXUlkkYCZlo+AjIqgtObDoKrarYqMyP/L2u71////m8H////6/+b9//j/2wBDASstLTw1PHZBQXb4pYyl+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj/wAARCAAIAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwCbyoGbG5sY6g0UUVNyrH//2Q==',
        },
        'has_animation': False,
    },
    'is_contact': True,
    'is_mutual_contact': True,
    'is_verified': False,
    'is_support': False,
    'restriction_reason': '',
    'is_scam': False,
    'is_fake': False,
    'have_access': True,
    'type': {'@type': 'userTypeRegular'},
    'language_code': '',
}


class UserTestCase(TestCase):
    """
    Тест кейс для объекта User
    """

    def test_user(self) -> None:
        """Простой тест User"""
        user_dict = deepcopy(user_base)

        user = User(user_dict)

        self.assertEqual(4111111123, user.id)
        self.assertEqual('FirstName', user.first_name)
        self.assertEqual(UserStatus.ONLINE, user.status)
        self.assertEqual(UserType.REGULAR, user.type)
        self.assertEqual(5464864564486453705, user.profile_photo.id)
        self.assertEqual(777, user.profile_photo.small.id)
        self.assertTrue(user.is_contact)
