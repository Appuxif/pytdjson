from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

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
        'audio': 'fake-audio-file',
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


@patch('telegram.types.files.File', return_value='fake-audio-file')
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
        self.assertEqual(content.audio.title, 10)
        self.assertEqual(content.audio.file_name, 'file_name')
        self.assertEqual(content.audio.audio, 'fake-audio-file')
