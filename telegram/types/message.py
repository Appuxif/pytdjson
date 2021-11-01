from enum import Enum


class TextParseModeTypes(Enum):
    """Типы парсинга текстов через tdlib"""

    HTML = {'@type': 'textParseModeHTML'}
    MARKDOWN = {'@type': 'textParseModeMarkdown', 'version': 2}
