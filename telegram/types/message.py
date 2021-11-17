from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass
from telegram.types.message_content import MessageContent

__all__ = ('MessageSenderType', 'MessageSender', 'MessageForwardInfo', 'Message')


class MessageSenderType(Enum):
    """Тип отправителя"""

    CHAT = 'messageSenderChat'
    USER = 'messageSenderUser'


@dataclass
class MessageSender(RawDataclass):
    """Отправитель сообщения"""

    type: MessageSenderType = None
    id: int = None

    def _assign_raw(self):
        self.type = MessageSenderType(self.raw.pop('@type'))
        if self.type == MessageSenderType.USER:
            self.id = self.raw.pop('user_id')
        else:
            self.id = self.raw.pop('chat_id')


@dataclass
class MessageForwardInfo(RawDataclass):
    """Информация об внутреннем отправителе сообщения"""

    date: int = None
    from_chat_id: int = None
    from_message_id: int = None


@dataclass
class Message(RawDataclass):
    """Сообщение из обновления телеграм"""

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
    content: MessageContent = None
    reply_markup: dict = None

    def _assign_raw(self):
        self.sender = MessageSender(self.raw.pop('sender'))
        forward_info = self.raw.pop('forward_info', None)
        if forward_info:
            self.forward_info = MessageForwardInfo(forward_info)
        self.content = MessageContent(self.raw.pop('content'))
