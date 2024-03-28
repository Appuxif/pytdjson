from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass


class MessageSenderType(str, Enum):
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
