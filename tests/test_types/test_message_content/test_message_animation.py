from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

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
        'animation': 'fake-animation-file',
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


@patch('telegram.types.files.File', return_value='fake-animation-file')
class MessageAnimationTestCase(TestCase):
    """
    Тест кейс для объекта MessageAnimation
    """

    def test(self, *args):
        """"""
        content_dict = deepcopy(content_message_animation)

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessageAnimation)
        self.assertEqual(content.animation.duration, 10)
        self.assertEqual(content.animation.width, 20)
        self.assertEqual(content.animation.height, 30)
        self.assertEqual(content.animation.file_name, 'file_name')
        self.assertEqual(content.animation.animation, 'fake-animation-file')
