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
    # boost_level: int = None
    # has_automatic_translation
    has_linked_chat: bool = None
    has_location: bool = None
    sign_messages: bool = None
    # show_message_sender
    join_to_send_messages: bool = None
    join_by_request: bool = None
    is_slow_mode_enabled: bool = None
    is_channel: bool = None
    is_broadcast_group: bool = None
    is_forum: bool = None
    # is_direct_messages_group
    # is_administered_direct_messages_group
    # verification_status
    # has_direct_messages_group
    # has_forum_tabs
    # restriction_info
    # paid_message_star_count
    # has_active_stories: bool = None
    # has_unread_active_stories: bool = None

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
    # direct_messages_chat_id
    slow_mode_delay: int = None
    slow_mode_delay_expires_in: float = None
    # can_enable_paid_messages
    # can_enable_paid_reaction
    can_get_members: bool = None
    has_hidden_members: bool = None
    can_hide_members: bool = None
    can_set_sticker_set: bool = None
    can_set_location: bool = None
    can_get_statistics: bool = None
    # can_get_revenue_statistics
    # can_get_star_revenue_statistics
    # can_send_gift
    can_toggle_aggressive_anti_spam: bool = None
    is_all_history_available: bool = None
    # can_have_sponsored_messages
    has_aggressive_anti_spam_enabled: bool = None
    # has_paid_media_allowed
    # has_pinned_stories: bool = None
    # gift_count
    # my_boost_count: int = None
    # unrestrict_boost_count: int = None
    # outgoing_paid_message_star_count
    sticker_set_id: int = None
    # custom_emoji_sticker_set_id: int = None
    # location: ChatLocation = None
    # invite_link: ChatInviteLink = None
    # bot_commands: list[BotCommands] = None
    # bot_verification
    # main_profile_tab
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
        yield SupergroupMembersFilter.SEARCH
        yield SupergroupMembersFilter.RESTRICTED
        yield SupergroupMembersFilter.BANNED
        yield SupergroupMembersFilter.MENTION

    @classmethod
    def with_thread(cls):
        """Генератор фильтров, которые поддерживают поле topic_id (old message_thread_id)"""
        yield SupergroupMembersFilter.MENTION
