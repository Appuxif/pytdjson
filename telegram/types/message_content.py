from dataclasses import dataclass

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.common import Contact, Location, Venue
from telegram.types.files import AnimationFile, AudioFile, DocumentFile, PhotoFile
from telegram.types.poll import Poll
from telegram.types.text import FormattedText


@dataclass
class MessageContentBase(RawDataclass):
    """Базовый класс контента сообщения"""


@dataclass
class MessageText(MessageContentBase):
    """Текстовое сообщение"""

    text: FormattedText = None


@dataclass
class MessageAnimation(MessageContentBase):
    """Анимация"""

    animation: AnimationFile = None
    caption: FormattedText = None


@dataclass
class MessageAudio(MessageContentBase):
    """Аудио"""

    audio: AudioFile = None
    caption: FormattedText = None


@dataclass
class MessageDocument(MessageContentBase):
    """Документ"""

    document: DocumentFile = None
    caption: FormattedText = None


@dataclass
class MessageInvoice(MessageContentBase):
    """Чек"""

    title: str = None
    description: str = None
    # photo
    currency: str = None
    total_amount: int = None
    start_parameter: str = None
    is_test: bool = None
    need_shipping_address: bool = None
    receipt_message_id: int = None


@dataclass
class MessageLocation(MessageContentBase):
    """Локация"""

    location: Location = None
    live_period: int = None
    expires_in: int = None
    heading: int = None
    proximity_alert_radius: int = None


@dataclass
class MessageContact(MessageContentBase):
    """Контакт"""

    contact = Contact


@dataclass
class MessagePhoto(MessageContentBase):
    """Фото"""

    photo: PhotoFile = None
    caption: FormattedText = None
    is_secret: bool = None


@dataclass
class MessagePoll(MessageContentBase):
    """Опрос"""

    poll: Poll = None


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
