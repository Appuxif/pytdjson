from dataclasses import dataclass
from enum import Enum

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.files import AnimationFile, AudioFile

__all__ = (
    'FormattedText',
    'MessageAnimation',
    'MessageAudio',
    'MessageContent',
    'MessageText',
    'TextEntity',
    'TextEntityType',
)


class TextParseModeTypes(Enum):
    """Типы парсинга текстов через tdlib"""

    HTML = {'@type': 'textParseModeHTML'}
    MARKDOWN = {'@type': 'textParseModeMarkdown', 'version': 2}


class TextEntityType(Enum):
    """Типы элементов форматирования текста"""

    BANK_CARD_NUMBER = 'textEntityTypeBankCardNumber'
    BOLD = 'textEntityTypeBold'
    BOT_COMMAND = 'textEntityTypeBotCommand'
    CASHTAG = 'textEntityTypeCashtag'
    CODE = 'textEntityTypeCode'
    EMAIL_ADDRESS = 'textEntityTypeEmailAddress'
    HASHTAG = 'textEntityTypeHashtag'
    ITALIC = 'textEntityTypeItalic'
    MENTION = 'textEntityTypeMention'
    MENTION_NAME = 'textEntityTypeMentionName'
    PHONE_NUMBER = 'textEntityTypePhoneNumber'
    PRE = 'textEntityTypePre'
    PRE_CODE = 'textEntityTypePreCode'
    STRIKETHROUGH = 'textEntityTypeStrikethrough'
    TEXT_URL = 'textEntityTypeTextUrl'
    UNDERLINE = 'textEntityTypeUnderline'
    URL = 'textEntityTypeUrl'


@dataclass
class TextEntity(RawDataclass):
    """Элемент форматирования текста"""

    offset: int = None
    length: int = None
    type: TextEntityType = None
    user_id: int = None
    language: str = None
    url: str = None

    def _assign_raw(self):
        _type = self.raw['type']
        self.type = TextEntityType(_type.pop('@type'))
        if self.type == TextEntityType.MENTION_NAME:
            self.user_id = _type.pop('user_id')
        elif self.type == TextEntityType.PRE_CODE:
            self.language = _type.pop('language')
        elif self.type == TextEntityType.TEXT_URL:
            self.url = _type.pop('url')


@dataclass
class FormattedText(RawDataclass):
    """Форматированный текст"""

    text: str = None
    entities: [TextEntity] = None

    def _assign_raw(self):
        self.entities = [TextEntity(entity) for entity in self.raw.pop('entities')]

    # def __post_init__(self):
    #     self.text = self.raw.pop('text')


class MessageContentType(Enum):
    """Типы контента сообщений"""

    ANIMATION = 'messageAnimation'
    AUDIO = 'messageAudio'
    BASIC_GROUP_CHAT_CREATE = 'messageBasicGroupChatCreate'
    CALL = 'messageCall'
    CHAT_ADD_MEMBERS = 'messageChatAddMembers'
    CHAT_CHANGE_PHOTO = 'messageChatChangePhoto'
    CHAT_CHANGE_TITLE = 'messageChatChangeTitle'
    CHAT_DELETE_MEMBER = 'messageChatDeleteMember'
    CHAT_DELETE_PHOTO = 'messageChatDeletePhoto'
    CHAT_JOIN_BY_LINK = 'messageChatJoinByLink'
    CHAT_SET_TTL = 'messageChatSetTtl'
    CHAT_UPGRADE_FROM = 'messageChatUpgradeFrom'
    CHAT_UPGRADE_TO = 'messageChatUpgradeTo'
    CONTACT = 'messageContact'
    CONTACT_REGISTERED = 'messageContactRegistered'
    CUSTOM_SERVICE_ACTION = 'messageCustomServiceAction'
    DICE = 'messageDice'
    DOCUMENT = 'messageDocument'
    EXPIRED_PHOTO = 'messageExpiredPhoto'
    EXPIRED_VIDEO = 'messageExpiredVideo'
    GAME = 'messageGame'
    GAME_SCORE = 'messageGameScore'
    INVOICE = 'messageInvoice'
    LOCATION = 'messageLocation'
    PASSPORT_DATA_RECEIVED = 'messagePassportDataReceived'
    PASSPORT_DATA_SENT = 'messagePassportDataSent'
    PAYMENT_SUCCESSFUL = 'messagePaymentSuccessful'
    PAYMENT_SUCCESSFUL_BOT = 'messagePaymentSuccessfulBot'
    PHOTO = 'messagePhoto'
    PIN_MESSAGE = 'messagePinMessage'
    POLL = 'messagePoll'
    PROXIMITY_ALERT_TRIGGERED = 'messageProximityAlertTriggered'
    SCREENSHOT_TAKEN = 'messageScreenshotTaken'
    STICKER = 'messageSticker'
    SUPERGROUP_CHAT_CREATE = 'messageSupergroupChatCreate'
    TEXT = 'messageText'
    UNSUPPORTED = 'messageUnsupported'
    VENUE = 'messageVenue'
    VIDEO = 'messageVideo'
    VIDEO_NOTE = 'messageVideoNote'
    VOICE_NOTE = 'messageVoiceNote'
    WEBSITE_CONNECTED = 'messageWebsiteConnected'

    IGNORED = (
        BASIC_GROUP_CHAT_CREATE,
        CALL,
        CHAT_CHANGE_PHOTO,
        CHAT_CHANGE_TITLE,
        CHAT_DELETE_PHOTO,
        CHAT_SET_TTL,
        CHAT_UPGRADE_FROM,
        CHAT_UPGRADE_TO,
        CONTACT,
        CONTACT_REGISTERED,
        CUSTOM_SERVICE_ACTION,
        DICE,
        EXPIRED_PHOTO,
        EXPIRED_VIDEO,
        GAME,
        GAME_SCORE,
        PASSPORT_DATA_RECEIVED,
        PASSPORT_DATA_SENT,
        PAYMENT_SUCCESSFUL,
        PAYMENT_SUCCESSFUL_BOT,
        PIN_MESSAGE,
        PROXIMITY_ALERT_TRIGGERED,
        SCREENSHOT_TAKEN,
        SUPERGROUP_CHAT_CREATE,
    )


@dataclass
class MessageText(RawDataclass):
    """Текстовое сообщение"""

    text: FormattedText = None

    def _assign_raw(self):
        self.text = FormattedText(self.raw.pop('text'))


@dataclass
class MessageAnimation(RawDataclass):
    """Анимация"""

    animation: AnimationFile = None
    caption: FormattedText = None

    def _assign_raw(self):
        self.animation = AnimationFile(self.raw.pop('animation'))
        self.caption = FormattedText(self.raw.pop('caption'))


@dataclass
class MessageAudio(RawDataclass):
    """Аудио"""

    audio: AudioFile = None
    caption: FormattedText = None

    def _assign_raw(self):
        self.audio = AudioFile(self.raw.pop('audio'))
        self.caption = FormattedText(self.raw.pop('caption'))


class MessageContentBuilder(ObjectBuilder):
    """Билдер, возвращает один из MessageContent"""

    mapping = {
        'messageAnimation': MessageAnimation,
        'messageAudio': MessageAudio,
        'messageText': MessageText,
    }


MessageContent = MessageContentBuilder()
