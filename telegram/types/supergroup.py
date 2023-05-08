from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass
from telegram.types.common import Usernames


@dataclass
class Supergroup(RawDataclass):
    """Супергруппа"""

    id: int = None
    usernames: Usernames = None
    date: int = None
    # status: ChatMemberStatus
    member_count: int = None
    has_linked_chat: bool = None
    has_location: bool = None
    sign_messages: bool = None
    join_to_send_messages: bool = None
    join_by_request: bool = None
    is_slow_mode_enabled: bool = None
    is_channel: bool = None
    is_broadcast_group: bool = None
    is_forum: bool = None
    is_verified: bool = None
    restriction_reason: str = None
    is_scam: bool = None
    is_fake: bool = None

    # Для обратной совместимости
    username: str = None

    def _assign_raw(self):
        self.username = Usernames.get_username(self.raw)


@dataclass
class SupergroupFullInfo(RawDataclass):
    """Дополнительная информация о супер группе"""

    # photo: chatPhoto
    description: str = None
    member_count: int = None
    administrator_count: int = None
    restricted_count: int = None
    banned_count: int = None
    linked_chat_id: int = None
    slow_mode_delay: int = None
    slow_mode_delay_expires_in: float = None
    can_get_members: bool = None
    has_hidden_members: bool = None
    can_hide_members: bool = None
    can_set_username: bool = None
    can_set_sticker_set: bool = None
    can_set_location: bool = None
    can_get_statistics: bool = None
    can_toggle_aggressive_anti_spam: bool = None
    is_all_history_available: bool = None
    has_aggressive_anti_spam_enabled: bool = None
    sticker_set_id: int = None
    # location: ChatLocation = None
    # invite_link: ChatInviteLink = None
    # bot_commands: list[BotCommands] = None
    upgraded_from_basic_group_id: int = None
    upgraded_from_max_message_id: int = None


class SupergroupMembersFilter(str, Enum):
    """Фильтры участников супергруппы"""

    RECENT = 'supergroupMembersFilterRecent'
    CONTACTS = 'supergroupMembersFilterContacts'
    ADMINISTRATORS = 'supergroupMembersFilterAdministrators'
    SEARCH = 'supergroupMembersFilterSearch'
    RESTRICTED = 'supergroupMembersFilterRestricted'
    BANNED = 'supergroupMembersFilterBanned'
    MENTION = 'supergroupMembersFilterMention'
    BOTS = 'supergroupMembersFilterBots'

    @classmethod
    def with_query(cls):
        """Генератор фильтров, которые поддерживают поле query"""
        yield SupergroupMembersFilter.CONTACTS
        yield SupergroupMembersFilter.MENTION
        yield SupergroupMembersFilter.RESTRICTED
        yield SupergroupMembersFilter.SEARCH
        yield SupergroupMembersFilter.BANNED

    @classmethod
    def with_thread(cls):
        """Генератор фильтров, которые поддерживают поле message_thread_id"""
        yield SupergroupMembersFilter.MENTION
