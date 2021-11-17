from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass


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


class TextParseMode(Enum):
    """Типы парсинга текстов через tdlib"""

    # HTML = {'@type': 'textParseModeHTML'}
    HTML = 'textParseModeHTML'
    # MARKDOWN = {'@type': 'textParseModeMarkdown', 'version': 2}
    MARKDOWN = 'textParseModeMarkdown'
