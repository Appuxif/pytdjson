from dataclasses import dataclass

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.files import AnimationFile, AudioFile
from telegram.types.text import FormattedText

__all__ = (
    'MessageContentBase',
    'MessageContentBuilder',
    'MessageAnimation',
    'MessageAudio',
    'MessageContact',
    'MessageContent',
    'MessageDocument',
    'MessageInvoice',
    'MessageLocation',
    'MessagePhoto',
    'MessagePoll',
    'MessageText',
    'MessageUnsupported',
    'MessageVenue',
    'MessageVideo',
    'MessageVideoNote',
    'MessageVoiceNote',
)


@dataclass
class MessageContentBase(RawDataclass):
    """Базовый класс контента сообщения"""


@dataclass
class MessageText(MessageContentBase):
    """Текстовое сообщение"""

    text: FormattedText = None

    def _assign_raw(self):
        self.text = FormattedText(self.raw['text'])


@dataclass
class MessageAnimation(MessageContentBase):
    """Анимация"""

    animation: AnimationFile = None
    caption: FormattedText = None

    def _assign_raw(self):
        self.animation = AnimationFile(self.raw['animation'])
        self.caption = FormattedText(self.raw['caption'])


@dataclass
class MessageAudio(MessageContentBase):
    """Аудио"""

    audio: AudioFile = None
    caption: FormattedText = None

    def _assign_raw(self):
        self.audio = AudioFile(self.raw['audio'])
        self.caption = FormattedText(self.raw['caption'])


@dataclass
class MessageDocument(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_document.html"""


@dataclass
class MessageInvoice(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_invoice.html"""


@dataclass
class MessageLocation(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_location.html"""


@dataclass
class MessageContact(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_contact.html"""


@dataclass
class MessagePhoto(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_photo.html"""


@dataclass
class MessagePoll(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_poll.html"""


@dataclass
class MessageUnsupported(MessageContentBase):
    """Сообщение не поддерживается"""


@dataclass
class MessageVenue(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_venue.html"""


@dataclass
class MessageVideo(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_video.html"""


@dataclass
class MessageVideoNote(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_video_note.html"""


@dataclass
class MessageVoiceNote(MessageContentBase):
    """TODO: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1message_voice_note.html"""


class MessageContentBuilder(ObjectBuilder):
    """Билдер, возвращает один из MessageContent"""

    def __init__(self):
        super().__init__()
        self.mapping = {}
        for cls in MessageContentBase.__subclasses__():
            key = cls.__name__
            key = key[0].lower() + key[1:]
            self.mapping[key] = cls


MessageContent = MessageContentBuilder()
