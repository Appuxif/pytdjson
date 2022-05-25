from dataclasses import dataclass

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.files import AnimationFile, AudioFile, DocumentFile
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
    start_parameter: int = None
    is_test: bool = None
    need_shipping_address: bool = None
    receipt_message_id: int = None


@dataclass
class MessageLocation(MessageContentBase):
    """Локация"""

    @dataclass
    class Location(RawDataclass):
        latitude: float = None
        longitude: float = None
        horizontal_accuracy: float = None

    location: Location = None
    live_period: int = None
    expires_in: int = None
    heading: int = None
    proximity_alert_radius: int = None


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
