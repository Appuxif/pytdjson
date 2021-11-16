from dataclasses import dataclass
from enum import Enum

from telegram.types.message_content import build_message_content

__all__ = ('MessageSenderType', 'MessageSender', 'MessageForwardInfo', 'Message')


class MessageSenderType(Enum):
    """Тип отправителя"""

    CHAT = 'messageSenderChat'
    USER = 'messageSenderUser'


@dataclass
class MessageSender:
    """Отправитель сообщения"""

    raw: dict
    type: MessageSenderType = None
    id: int = None

    def __post_init__(self):
        self.type = MessageSenderType(self.raw.pop('@type'))
        if self.type == MessageSenderType.USER:
            self.id = self.raw.pop('user_id')
        else:
            self.id = self.raw.pop('chat_id')


@dataclass
class MessageForwardInfo:
    """Информация об внутреннем отправителе сообщения"""

    raw: dict
    date: int = None
    from_chat_id: int = None
    from_message_id: int = None

    def __post_init__(self):
        self.date = self.raw.pop('date')
        self.from_chat_id = self.raw.pop('from_chat_id')
        self.from_message_id = self.raw.pop('from_message_id')


@dataclass
class Message:
    """Сообщение из обновления телеграм"""

    raw: dict

    id: int = None
    chat_id: int = None
    date: int = None
    edit_date: int = None
    reply_in_chat_id: int = None
    reply_to_message_id: int = None

    is_outgoing: bool = None
    is_pinned: bool = None
    can_be_edited: bool = None
    can_be_forwarded: bool = None
    can_be_deleted_only_for_self: bool = None
    can_be_deleted_for_all_users: bool = None
    can_get_statistics: bool = None
    is_channel_post: bool = None
    contains_unread_mention: bool = None

    sender: MessageSender = None
    forward_info: MessageForwardInfo = None
    content: object = None
    reply_markup: dict = None

    def __post_init__(self):
        self.sender = MessageSender(self.raw.pop('sender'))
        forward_info = self.raw.pop('forward_info', None)
        if forward_info:
            self.forward_info = MessageForwardInfo(forward_info)
        self.content = build_message_content(self.raw.pop('content'))

        keys = self.raw.keys()
        keys = list(keys)
        for key in keys:
            if hasattr(self, key):
                value = self.raw.pop(key)
                setattr(self, key, value)
