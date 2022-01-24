from dataclasses import dataclass
from enum import Enum
from typing import List

from telegram.types.base import RawDataclass
from telegram.types.files import File
from telegram.types.message import Message, MessageSender, MessageSenderType


@dataclass
class ChatPhotoInfo(RawDataclass):
    small: File = None
    big: File = None
    minithumbnail = None
    has_animation: bool = None

    def _assign_raw(self):
        self.small = File(self.raw['small'])
        self.big = File(self.raw['big'])


@dataclass
class ChatPermissions(RawDataclass):
    can_send_messages: bool = None
    can_send_media_messages: bool = None
    can_send_polls: bool = None
    can_send_other_messages: bool = None
    can_add_web_page_previews: bool = None
    can_change_info: bool = None
    can_invite_users: bool = None
    can_pin_messages: bool = None


class ChatType(Enum):
    """Типы чатов"""

    BASIC_GROUP = 'chatTypeBasicGroup'
    PRIVATE = 'chatTypePrivate'
    SECRET = 'chatTypeSecret'
    SUPER_GROUP = 'chatTypeSupergroup'


@dataclass
class Chat(RawDataclass):
    id: int = None

    type: ChatType = None
    basic_group_id: int = None
    supergroup_id: int = None
    is_channel: bool = False
    secret_chat_id: int = None
    user_id: int = None

    title: str = None
    photo: ChatPhotoInfo = None
    permissions: ChatPermissions = None
    last_message: Message = None
    positions: List[dict] = None
    message_sender: MessageSender = None

    has_protected_content: bool = None
    is_marked_as_unread: bool = None
    is_blocked: bool = None
    has_scheduled_messages: bool = None
    can_be_deleted_only_for_self: bool = None
    can_be_deleted_for_all_users: bool = None
    can_be_reported: bool = None
    default_disable_notification: bool = None
    unread_count: int = None
    last_read_inbox_message_id: int = None
    last_read_outbox_message_id: int = None
    unread_mention_count: int = None
    # notification_settings: ChatNotificationSettings = None
    message_ttl: int = None
    theme_name: str = None
    # action_bar: ChatActionBar = None
    # video_chat: VideoChat = None
    # pending_join_requests: ChatJoinRequestInfo = None
    reply_markup_message_id: int = None
    # draft_message: DraftMessage = None
    client_data: str = None

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

        photo = self.raw.get('photo')
        if photo:
            self.photo = ChatPhotoInfo(self.raw['photo'])
        self.permissions = ChatPermissions(self.raw['permissions'])

        last_message = self.raw.get('last_message')
        if last_message:
            self.last_message = Message(last_message)

        message_sender_id = self.raw.get('message_sender_id')
        if message_sender_id:
            self.message_sender = MessageSender(self.raw['message_sender_id'])
