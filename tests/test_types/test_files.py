from copy import deepcopy
from unittest import TestCase

from telegram.types.files import File

file_dict_base = {
    '@type': 'file',
    'id': 1,
    'size': 0,
    'expected_size': 100,
    'local': {
        'path': 'local-path',
        'can_be_downloaded': True,
        'can_be_deleted': True,
    },
    'remote': {
        'id': 2,
        'unique_id': 3,
        'uploaded_size': 0,
    },
}


class FileTestCase(TestCase):
    """
    Тест кейс для объекта File
    """

    def test_file(self):
        """Форматирования нет"""

        file_dict = deepcopy(file_dict_base)

        file = File(file_dict)

        self.assertIsInstance(file, File)
        self.assertEqual(file.id, 1)
        self.assertEqual(file.size, 0)
        self.assertEqual(file.expected_size, 100)
        self.assertEqual(file.remote_id, 2)
        self.assertEqual(file.remote_unique_id, 3)
        self.assertEqual(file.local_path, 'local-path')
