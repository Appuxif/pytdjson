from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass


@dataclass
class Supergroup(RawDataclass):
    """Супергруппа"""

    id: int = None
    username: str = None
    member_count: int = None
    has_linked_chat: bool = None
    has_location: bool = None
    sign_messages: bool = None
    is_slow_mode_enabled: bool = None
    is_channel: bool = None
    is_broadcast_group: bool = None
    is_verified: bool = None
    restriction_reason: str = None
    is_scam: bool = None
    is_fake: bool = None


@dataclass
class SupergroupFullInfo(RawDataclass):
    """Дополнительная информация о супер группе"""

    description: str = None
    member_count: int = None
    administrator_count: int = None
    restricted_count: int = None
    banned_count: int = None
    linked_chat_id: int = None
    slow_mode_delay: int = None
    slow_mode_delay_expires_in: int = None
    can_get_members: bool = None
    can_set_username: bool = None
    can_set_sticker_set: bool = None
    cat_set_location: bool = None
    cat_get_statistics: bool = None
    is_all_history_available: bool = None
    sticker_set_id: int = None
    upgraded_from_basic_group_id: int = None
    upgraded_from_max_message_id: int = None


class SupergroupMembersFilter(str, Enum):
    """Фильтры участников супергруппы"""

    ADMINISTRATORS = 'supergroupMembersFilterAdministrators'
    BANNED = 'supergroupMembersFilterBanned'
    BOTS = 'supergroupMembersFilterBots'
    CONTACTS = 'supergroupMembersFilterContacts'
    MENTION = 'supergroupMembersFilterMention'
    RECENT = 'supergroupMembersFilterRecent'
    RESTRICTED = 'supergroupMembersFilterRestricted'
    SEARCH = 'supergroupMembersFilterSearch'

    @classmethod
    def with_query(cls):
        """Генератор фильтров, которые поддерживают поле query"""
        yield SupergroupMembersFilter.CONTACTS
        yield SupergroupMembersFilter.MENTION
        yield SupergroupMembersFilter.RESTRICTED
        yield SupergroupMembersFilter.SEARCH

    @classmethod
    def with_thread(cls):
        """Генератор фильтров, которые поддерживают поле message_thread_id"""
        yield SupergroupMembersFilter.MENTION
