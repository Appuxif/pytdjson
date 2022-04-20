from copy import deepcopy
from unittest import TestCase

from telegram.types.files import File
from telegram.types.message_content import MessageAudio, MessageContent

content_message_audio = {
    '@type': 'messageAudio',
    'audio': {
        'duration': 10,
        'title': 'title',
        'performer': 'performer',
        'file_name': 'file_name',
        'mime_type': 'image/gif',
        'album_cover_minithumbnail': 'not-interested',
        'album_cover_thumbnail': 'not-interested',
        'audio': {
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


class MessageAudioTestCase(TestCase):
    """
    Тест кейс для объекта MessageAudio
    """

    def test(self, *args):
        """Проверка MessageAudio"""
        content_dict = deepcopy(content_message_audio)

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessageAudio)
        self.assertEqual(content.audio.duration, 10)
        self.assertEqual(content.audio.title, 'title')
        self.assertEqual(content.audio.file_name, 'file_name')
        self.assertIsInstance(content.audio.audio, File)
        self.assertEqual(10, content.audio.audio.id)
        self.assertEqual(100, content.audio.audio.size)
        self.assertIsNone(content.audio.audio.expected_size)
        self.assertEqual('test-path', content.audio.audio.local_path)
