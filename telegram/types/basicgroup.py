from dataclasses import dataclass

from telegram.types.base import RawDataclass


@dataclass
class BasicGroup(RawDataclass):
    """Базовая группа"""
    id: int = None
    member_count: int = None
    # status:ChatMemberStatus
    is_active: bool = None
    upgraded_to_supergroup_id: int = None


@dataclass
class BasicGroupFullInfo(RawDataclass):
    """Дополнительная информация о базовой группе"""
    # photo:chatPhoto
    description: str = None
    creator_user_id: int = None
    # members:vector<chatMember>
    # can_hide_members:Bool
    # can_toggle_aggressive_anti_spam:Bool
    # invite_link:chatInviteLink
    # bot_commands:vector<botCommands>
