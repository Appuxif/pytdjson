from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
        self.type = MessageSenderType(self.raw['@type'])
        if self.type == MessageSenderType.USER:
            self.id = self.raw['user_id']
        else:
            self.id = self.raw['chat_id']


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

    sender: Optional[MessageSender] = None
    forward_info: Optional[MessageForwardInfo] = None
    content: Optional[MessageContent] = None
    reply_markup: dict = None

    def _assign_raw(self):
        self._assign_raw_optional('sender', MessageSender)
        self._assign_raw_optional('forward_info', MessageForwardInfo)
        self._assign_raw_optional('content', MessageContent)
