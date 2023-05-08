from dataclasses import dataclass
from enum import Enum
from typing import List

from telegram.types.base import RawDataclass


class TextEntityType(str, Enum):
    """Типы элементов форматирования текста"""

    MENTION = 'textEntityTypeMention'
    HASHTAG = 'textEntityTypeHashtag'
    CASHTAG = 'textEntityTypeCashtag'
    BOT_COMMAND = 'textEntityTypeBotCommand'
    URL = 'textEntityTypeUrl'
    EMAIL_ADDRESS = 'textEntityTypeEmailAddress'
    PHONE_NUMBER = 'textEntityTypePhoneNumber'
    BANK_CARD_NUMBER = 'textEntityTypeBankCardNumber'
    BOLD = 'textEntityTypeBold'
    ITALIC = 'textEntityTypeItalic'
    UNDERLINE = 'textEntityTypeUnderline'
    STRIKETHROUGH = 'textEntityTypeStrikethrough'
    SPOILER = 'textEntityTypeSpoiler'
    CODE = 'textEntityTypeCode'
    PRE = 'textEntityTypePre'
    PRE_CODE = 'textEntityTypePreCode'
    TEXT_URL = 'textEntityTypeTextUrl'
    MENTION_NAME = 'textEntityTypeMentionName'
    CUSTOM_EMOJI = 'textEntityTypeCustomEmoji'
    MEDIA_TIMESTAMP = 'textEntityTypeMediaTimestamp'


@dataclass
class TextEntity(RawDataclass):
    """Элемент форматирования текста"""

    offset: int = None
    length: int = None
    type: TextEntityType = None

    # type-specific
    user_id: int = None
    custom_emoji_id: int = None
    media_timestamp: int = None
    language: str = None
    url: str = None

    def _assign_raw(self):
        _type = self.raw['type']
        self.type = TextEntityType(_type['@type'])
        if self.type == TextEntityType.MENTION_NAME:
            self.user_id = _type['user_id']
        elif self.type == TextEntityType.PRE_CODE:
            self.language = _type['language']
        elif self.type == TextEntityType.TEXT_URL:
            self.url = _type['url']
        elif self.type == TextEntityType.CUSTOM_EMOJI:
            self.custom_emoji_id = _type['custom_emoji_id']
        elif self.type == TextEntityType.MEDIA_TIMESTAMP:
            self.media_timestamp = _type['media_timestamp']


@dataclass
class FormattedText(RawDataclass):
    """Форматированный текст"""

    text: str = None
    entities: List[TextEntity] = None

    def _assign_raw(self):
        self.entities = [TextEntity(entity) for entity in self.raw['entities']]


class TextParseMode(str, Enum):
    """Типы парсинга текстов через tdlib"""

    HTML = 'textParseModeHTML'
    MARKDOWN = 'textParseModeMarkdown'
    NONE = 'None'
