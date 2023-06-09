from dataclasses import dataclass

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.common import Contact, Location, Venue
from telegram.types.files import (
    AnimationFile,
    AudioFile,
    DocumentFile,
    PhotoFile,
    VideoFile,
    VideoNote,
    VoiceNote,
)
from telegram.types.poll import Poll
from telegram.types.text import FormattedText


@dataclass
class MessageContentBase(RawDataclass):
    """Базовый класс контента сообщения"""


@dataclass
class MessageText(MessageContentBase):
    """Текстовое сообщение"""

    text: FormattedText = None
    # web_page: webPage = None


@dataclass
class MessageAnimation(MessageContentBase):
    """Анимация"""

    animation: AnimationFile = None
    caption: FormattedText = None
    has_spoiler: bool = None
    is_secret: bool = None


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
    # photo: photo
    currency: str = None
    total_amount: int = None
    start_parameter: str = None
    is_test: bool = None
    need_shipping_address: bool = None
    receipt_message_id: int = None
    # extended_media: MessageExtendedMedia


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
    has_spoiler: bool = None
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
    """Место сбора"""

    venue: Venue = None


@dataclass
class MessageChatAddMembers(MessageContentBase):
    """Место сбора"""

    member_user_ids: list = None


@dataclass
class MessageVideo(MessageContentBase):
    """Сообщение-видео"""

    video: VideoFile = None
    caption: FormattedText = None
    is_secret: bool = False


@dataclass
class MessageVideoNote(MessageContentBase):
    """Видео-Заметка"""

    video_note: VideoNote = None
    is_viewed: bool = False
    is_secret: bool = False


@dataclass
class MessageVoiceNote(MessageContentBase):
    """Голосовое сообщение"""

    voice_note: VoiceNote = None
    caption: FormattedText = None
    is_listened: bool = False


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
