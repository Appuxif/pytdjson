from dataclasses import dataclass, field
from enum import Enum
from typing import List

from telegram.types.base import ObjectBuilder, RawDataclass, default_getter
from telegram.types.files import AnimationFile, AudioFile, DocumentFile, PhotoFile
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
    """Контакт"""

    @dataclass
    class Contact(RawDataclass):
        phone_number: str = None
        first_name: str = None
        last_name: str = None
        vcard: str = None
        user_id: int = None

    contact = Contact


@dataclass
class MessagePhoto(MessageContentBase):
    """Фото"""

    photo: PhotoFile = None
    caption: FormattedText = None
    is_secret: bool = None


@dataclass
class PollOption(RawDataclass):
    """Опция опроса"""

    text: str = None
    voter_count: int = None
    vote_percentage: int = None
    is_chosen: bool = None
    is_being_chosen: bool = None


class PollType(Enum):
    """Типы опросов"""

    QUIZ = 'pollTypeQuiz'
    REGULAR = 'pollTypeRegular'


@dataclass
class Poll(RawDataclass):
    """Опрос"""

    id: int = None
    question: str = None
    options: List[PollOption] = field(
        default=None,
        metadata={'getter': lambda options: [PollOption(opt) for opt in options]},
    )
    total_voter_count: int = None
    recent_voter_user_ids: List[int] = field(
        default=None,
        metadata={'getter': default_getter},
    )
    is_anonymous: bool = None
    type: PollType = field(
        default=None,
        metadata={'getter': lambda value: PollType(value['@type'])},
    )
    open_period: int = None
    close_date: int = None
    is_closed: bool = None

    # only pollTypeQuiz
    correct_option_id: int = None
    explanation: FormattedText = None

    # only pollTypeRegular
    allow_multiple_answers: bool = None

    def _assign_raw(self):
        if 'correct_option_id' in self.raw['type']:
            self.correct_option_id = self.raw['type']['correct_option_id']
            self.explanation = FormattedText(self.raw['type']['explanation'])
        if 'allow_multiple_answers' in self.raw['type']:
            self.allow_multiple_answers = self.raw['type']['allow_multiple_answers']


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
