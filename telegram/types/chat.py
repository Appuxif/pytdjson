from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass
from telegram.types.files import File
from telegram.types.message import Message
from telegram.types.message_sender import MessageSender


@dataclass
class ChatPhotoInfo(RawDataclass):
    small: File = None
    big: File = None
    minithumbnail: dict = None
    has_animation: bool = None


@dataclass
class ChatPermissions(RawDataclass):
    can_send_basic_messages: bool = None
    can_send_audios: bool = None
    can_send_documents: bool = None
    can_send_photos: bool = None
    can_send_videos: bool = None
    can_send_video_notes: bool = None
    can_send_voice_notes: bool = None
    can_send_polls: bool = None
    can_send_other_messages: bool = None
    can_add_web_page_previews: bool = None
    can_change_info: bool = None
    can_invite_users: bool = None
    can_pin_messages: bool = None
    can_create_topics: bool = None

    # deprecated
    can_manage_topics: bool = None
    can_send_messages: bool = None
    can_send_media_messages: bool = None


class ChatType(str, Enum):
    """Типы чатов"""

    BASIC_GROUP = 'chatTypeBasicGroup'
    PRIVATE = 'chatTypePrivate'
    SECRET = 'chatTypeSecret'
    SUPER_GROUP = 'chatTypeSupergroup'


class ChatAvailableReactions(str, Enum):
    """ChatAvailableReactions"""

    ALL = 'chatAvailableReactionsAll'
    SOME = 'chatAvailableReactionsSome'


@dataclass
class Chat(RawDataclass):
    id: int = None
    type: ChatType = None
    title: str = None
    photo: ChatPhotoInfo = None
    accent_color_id: int = None
    background_custom_emoji_id: int = None
    profile_accent_color_id: int = None
    profile_background_custom_emoji_id: int = None
    permissions: ChatPermissions = None
    last_message: Message = None
    # positions: list = None
    # chat_lists: list = None
    message_sender: MessageSender = None
    # block_list: BlockList = None
    has_protected_content: bool = None
    is_translatable: bool = None
    is_marked_as_unread: bool = None
    view_as_topics: bool = None
    has_scheduled_messages: bool = None
    can_be_deleted_only_for_self: bool = None
    can_be_deleted_for_all_users: bool = None
    can_be_reported: bool = None
    default_disable_notification: bool = None
    unread_count: int = None
    last_read_inbox_message_id: int = None
    last_read_outbox_message_id: int = None
    unread_mention_count: int = None
    unread_reaction_count: int = None
    # notification_settings: ChatNotificationSettings = None
    available_reactions: ChatAvailableReactions = None
    message_auto_delete_time: int = None
    # emoji_status: emojiStatus
    # background:chatBackground
    theme_name: str = None
    # action_bar: ChatActionBar = None
    # video_chat: VideoChat = None
    # pending_join_requests: ChatJoinRequestInfo = None
    reply_markup_message_id: int = None
    # draft_message: DraftMessage = None
    client_data: str = None

    # for back compatibility
    basic_group_id: int = None
    supergroup_id: int = None
    is_channel: bool = False
    secret_chat_id: int = None
    user_id: int = None

    def _assign_raw(self):
        self.type = ChatType(self.raw['type']['@type'])

        if self.type == ChatType.BASIC_GROUP:
            self.basic_group_id = self.raw['type']['basic_group_id']

        elif self.type == ChatType.PRIVATE:
            self.user_id = self.raw['type']['user_id']

        elif self.type == ChatType.SECRET:
            self.secret_chat_id = self.raw['type']['secret_chat_id']
            self.user_id = self.raw['type']['user_id']

        elif self.type == ChatType.SUPER_GROUP:
            self.supergroup_id = self.raw['type']['supergroup_id']
            self.is_channel = self.raw['type']['is_channel']

        message_sender_id = self.raw.get('message_sender_id')
        if message_sender_id:
            self.message_sender = MessageSender(self.raw['message_sender_id'])

        if self.raw.get('available_reactions'):
            self.available_reactions = ChatAvailableReactions(
                self.raw['available_reactions']['@type']
            )
