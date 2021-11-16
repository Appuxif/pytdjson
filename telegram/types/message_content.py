from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Callable

from telegram.types.base import build_from_mapping
from telegram.types.files import AnimationFile


class TextParseModeTypes(Enum):
    """Типы парсинга текстов через tdlib"""

    HTML = {'@type': 'textParseModeHTML'}
    MARKDOWN = {'@type': 'textParseModeMarkdown', 'version': 2}


class TextEntityTypeEnum(Enum):
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
class TextEntityType:
    """Тип форматирования текста"""

    raw: dict

    type: TextEntityTypeEnum = None
    user_id: int = None
    language: str = None
    url: str = None

    def __post_init__(self):
        self.type = TextEntityTypeEnum(self.raw.pop('@type'))
        self.user_id = self.raw.pop('user_id', None)
        self.language = self.raw.pop('language', None)
        self.url = self.raw.pop('url', None)


@dataclass
class TextEntity:
    """Элемент форматирования текста"""

    raw: dict

    offset: int = None
    length: int = None
    type: TextEntityType = None

    def __post_init__(self):
        self.offset = self.raw.pop('offset')
        self.length = self.raw.pop('length')
        self.type = TextEntityType(self.raw.pop('type'))


@dataclass
class FormattedText:
    """Форматированный текст"""

    raw: dict

    text: str = None
    entities: [TextEntity] = None

    def __post_init__(self):
        self.text = self.raw.pop('text')
        self.entities = [TextEntity(entity) for entity in self.raw.pop('entities')]


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
class MessageText:
    """Текстовое сообщение"""

    raw: dict

    text: FormattedText = None

    def __post_init__(self):
        self.text = FormattedText(self.raw.pop('text'))


@dataclass
class MessageAnimation:
    """Анимация"""

    raw: dict

    animation: AnimationFile = None
    caption: FormattedText = None

    def __post_init__(self):
        self.animation = AnimationFile(self.raw.pop('animation'))
        self.caption = FormattedText(self.raw.pop('caption'))


message_content_mapping = {
    'messageAnimation': MessageAnimation,
    'messageText': MessageText,
}

build_message_content: Callable = partial(build_from_mapping, message_content_mapping)
