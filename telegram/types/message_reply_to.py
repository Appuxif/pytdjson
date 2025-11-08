from dataclasses import dataclass, field
from typing import Union

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.message_content import MessageContentBuilder, MessageContentType
from telegram.types.message_origin import MessageOrigin


@dataclass
class MessageReplyToMessage(RawDataclass):
    chat_id: int = None
    message_id: int = None
    # quote: textQuote = None
    checklist_task_id: int = None
    origin: MessageOrigin = field(default=None, metadata={'getter': MessageOrigin})
    origin_send_date: int = None
    content: MessageContentType = field(
        default=None, metadata={'getter': MessageContentBuilder()}
    )


@dataclass
class MessageReplyToStory(RawDataclass):
    story_poster_chat_id: int = None
    story_id: int = None


MessageReplyToType = Union[MessageReplyToMessage, MessageReplyToStory]


@dataclass
class MessageReplyToBuilder(ObjectBuilder):
    """MessageReplyTo"""

    mapping = {
        'messageReplyToMessage': MessageReplyToMessage,
        'messageReplyToStory': MessageReplyToStory,
    }
