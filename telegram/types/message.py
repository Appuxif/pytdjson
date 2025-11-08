from dataclasses import dataclass, field
from enum import Enum
from typing import Union

from telegram.types.base import RawDataclass
from telegram.types.message_content import MessageContentBuilder, MessageContentType
from telegram.types.message_origin import MessageOrigin
from telegram.types.message_reply_to import MessageReplyToBuilder, MessageReplyToType
from telegram.types.message_sender import MessageSender

__all__ = (
    'ReactionType',
    'ForwardSource',
    'MessageForwardInfo',
    'Message',
    'MessageLink',
)


class ReactionType(str, Enum):
    """ReactionType"""

    EMOJI = 'reactionTypeEmoji'
    CUSTOM = 'reactionTypeCustomEmoji'
    PAID = 'reactionTypePaid'

    def build(self, value: Union[int, str]):
        data = {'@type': self.value}
        if self == ReactionType.EMOJI:
            data['emoji'] = value
        if self == ReactionType.CUSTOM:
            data['custom_emoji_id'] = value
        return data


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
    # is_from_offline:Bool
    can_be_saved: bool = None
    has_timestamped_media: bool = None
    is_channel_post: bool = None
    # is_paid_star_suggested_post:Bool
    # is_paid_ton_suggested_post:Bool
    contains_unread_mention: bool = None
    date: int = None
    edit_date: int = None
    forward_info: MessageForwardInfo = None
    # import_info: messageImportInfo
    # interaction_info: messageInteractionInfo
    # unread_reactions: list[UnreadReaction]
    # fact_check:factCheck
    # suggested_post_info:suggestedPostInfo
    reply_to: MessageReplyToType = field(
        default=None, metadata={'getter': MessageReplyToBuilder()}
    )
    # topic_id:MessageTopic
    # self_destruct_type:MessageSelfDestructType
    self_destruct_in: float = None
    auto_delete_in: float = None
    via_bot_user_id: int = None
    # sender_business_bot_user_id:int53
    sender_boost_count: int = None
    # paid_message_star_count:int53
    author_signature: str = None
    media_album_id: int = None
    # effect_id:int64
    # restriction_info:restrictionInfo
    content: MessageContentType = field(
        default=None, metadata={'getter': MessageContentBuilder()}
    )
    reply_markup: dict = None

    def _assign_raw(self):
        if self.raw.get('sender_id') and not self.raw.get('sender'):
            self.sender = MessageSender(self.raw['sender_id'])


@dataclass
class MessageLink(RawDataclass):
    """Ссылка на сообщение"""

    link: str = None
    is_public: bool = None
