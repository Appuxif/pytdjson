from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass


@dataclass
class MessageOrigin(RawDataclass):
    """Источник сообщения

    Example:
        origin: MessageOrigin = field(default=None, metadata={'getter': MessageOrigin})
    """

    class Type(str, Enum):
        """Тип источника сообщения"""

        USER = 'messageOriginUser'
        HIDDEN = 'messageOriginHiddenUser'
        CHAT = 'messageOriginChat'
        CHANNEL = 'messageOriginChannel'

    message_origin_type: Type = Type.USER

    # messageOriginUser
    sender_user_id: int = None

    # messageOriginHiddenUser
    sender_name: str = None

    # messageOriginChat
    sender_chat_id: int = None
    author_signature: str = None

    # messageOriginChannel
    channel_chat_id: int = None
    channel_message_id: int = None
    # author_signature: str = None

    def _assign_raw(self):
        if self.raw.get('sender_user_id'):
            self.message_origin_type = self.Type.USER
            self.sender_user_id = self.raw['sender_user_id']

        elif self.raw.get('sender_name'):
            self.message_origin_type = self.Type.HIDDEN
            self.sender_name = self.raw['sender_name']

        elif self.raw.get('sender_chat_id'):
            self.message_origin_type = self.Type.CHAT
            self.sender_chat_id = self.raw['sender_chat_id']
            self.author_signature = self.raw.get('author_signature')

        else:
            self.message_origin_type = self.Type.CHANNEL
            self.channel_chat_id = self.raw['chat_id']
            self.channel_message_id = self.raw['message_id']
            self.author_signature = self.raw.get('author_signature')
