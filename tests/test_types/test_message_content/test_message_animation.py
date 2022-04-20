from copy import deepcopy
from unittest import TestCase

from telegram.types.files import File
from telegram.types.message_content import MessageAnimation, MessageContent

content_message_animation = {
    '@type': 'messageAnimation',
    'animation': {
        'duration': 10,
        'width': 20,
        'height': 30,
        'file_name': 'file_name',
        'mime_type': 'image/gif',
        'has_stickers': True,
        'minithumbnail': 'not-interested',
        'thumbnail': 'not-interested',
        'animation': {
            'id': 10,
            'size': 100,
            'local': {'path': 'test-path'},
            'remote': {'id': 'test-id', 'unique_id': 'test-unique-id'},
        },
    },
    'caption': {
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


class MessageAnimationTestCase(TestCase):
    """
    Тест кейс для объекта MessageAnimation
    """

    def test(self):
        """Проверка MessageAnimation"""
        content_dict = deepcopy(content_message_animation)

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessageAnimation)
        self.assertEqual(content.animation.duration, 10)
        self.assertEqual(content.animation.width, 20)
        self.assertEqual(content.animation.height, 30)
        self.assertEqual(content.animation.file_name, 'file_name')
        self.assertIsInstance(content.animation.animation, File)
        self.assertEqual(10, content.animation.animation.id)
        self.assertEqual(100, content.animation.animation.size)
        self.assertIsNone(content.animation.animation.expected_size)
        self.assertEqual('test-path', content.animation.animation.local_path)
