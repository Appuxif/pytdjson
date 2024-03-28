from dataclasses import dataclass, field
from enum import Enum
from typing import Union

from telegram.types.base import RawDataclass
from telegram.types.message_content import MessageContent

__all__ = (
    'MessageForwardInfo',
    'Message',
    'MessageLink',
)

from telegram.types.message_sender import MessageSender


class ReactionType(str, Enum):
    """ReactionType"""

    EMOJI = 'reactionTypeEmoji'
    CUSTOM = 'reactionTypeCustomEmoji'

    def build(self, value: Union[int, str]):
        data = {'@type': self.value}
        if self == ReactionType.EMOJI:
            data['emoji'] = value
        if self == ReactionType.CUSTOM:
            data['custom_emoji_id'] = value
        return data


@dataclass
class MessageOrigin(RawDataclass):
    """Источник сообщения"""

    class Type(str, Enum):
        """Тип источника сообщения"""

        USER = 'messageOriginUser'
        HIDDEN = 'messageOriginHiddenUser'
        CHAT = 'messageOriginChat'

    message_origin_type: Type = Type.USER

    # messageOriginUser
    sender_user_id: int = None

    # messageOriginHiddenUser
    sender_name: str = None

    # messageOriginChat
    sender_chat_id: int = None
    author_signature: str = None

    def _assign_raw(self):
        if self.raw.get('sender_user_id'):
            self.message_origin_type = self.Type.USER
            self.sender_user_id = self.raw['sender_user_id']

        if self.raw.get('sender_name'):
            self.message_origin_type = self.Type.HIDDEN
            self.sender_name = self.raw['sender_name']

        if self.raw.get('sender_chat_id'):
            self.message_origin_type = self.Type.CHAT
            self.sender_chat_id = self.raw['sender_chat_id']
            self.author_signature = self.raw.get('author_signature')


@dataclass
class ForwardSource(RawDataclass):
    """Источник пересылаемого сообщения"""

    chat_id: int = None
    message_id: int = None
    sender_id: MessageSender = field(default=None, metadata={'getter': MessageSender})
    sender_name: str = None
    date: int = None
    is_outgoing: bool = None


@dataclass
class MessageForwardInfo(RawDataclass):
    """Информация об внутреннем отправителе сообщения"""

    origin: MessageOrigin = field(default=None, metadata={'getter': MessageOrigin})
    date: int = None
    source: ForwardSource = field(default=None, metadata={'getter': ForwardSource})
    public_service_announcement_type: str = None

    # for back compatibility
    from_chat_id: int = None
    from_message_id: int = None

    def _assign_raw(self):
        if self.raw.get('source'):
            self.from_chat_id = self.raw['source'].get('chat_id')
            self.from_message_id = self.raw['source'].get('message_id')


@dataclass
class Message(RawDataclass):
    """Сообщение из обновления телеграм"""

    id: int = None
    sender: MessageSender = None
    chat_id: int = None
    # sending_state: MessageSendingState
    # scheduling_state:MessageSchedulingState
    is_outgoing: bool = None
    is_pinned: bool = None
    can_be_edited: bool = None
    can_be_forwarded: bool = None
    can_be_replied_in_another_chat: bool = None
    can_be_saved: bool = None
    can_be_deleted_only_for_self: bool = None
    can_be_deleted_for_all_users: bool = None
    can_get_added_reactions: bool = None
    can_get_statistics: bool = None
    can_get_message_thread: bool = None
    can_get_read_date: bool = None
    can_get_viewers: bool = None
    can_get_media_timestamp_links: bool = None
    can_report_reactions: bool = None
    has_timestamped_media: bool = None
    is_channel_post: bool = None
    is_topic_message: bool = None
    contains_unread_mention: bool = None
    date: int = None
    edit_date: int = None
    forward_info: MessageForwardInfo = None
    # import_info: messageImportInfo
    # interaction_info: messageInteractionInfo
    # unread_reactions: list[UnreadReaction]
    # reply_to: MessageReplyTo  # <--
    message_thread_id: int = None
    saved_messages_topic_id: int = None
    # self_destruct_type:MessageSelfDestructType
    self_destruct_in: float = None
    auto_delete_in: float = None
    via_bot_user_id: int = None
    sender_boost_count: int = None
    author_signature: str = None
    media_album_id: int = None
    restriction_reason: str = None
    content: MessageContent = None
    reply_markup: dict = None

    # for back compatibility
    reply_in_chat_id: int = None
    reply_to_message_id: int = None
    self_destruct_time: int = None

    def _assign_raw(self):
        if self.raw.get('sender_id') and not self.raw.get('sender'):
            self.sender = MessageSender(self.raw['sender_id'])


@dataclass
class MessageLink(RawDataclass):
    """Ссылка на сообщение"""

    link: str = None
    is_public: bool = None
