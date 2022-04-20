from dataclasses import dataclass

from telegram.types.base import RawDataclass


@dataclass
class BasicGroup(RawDataclass):
    """Базовая группа"""

    id: int = None
    member_count: int = None
    is_active: bool = None
    upgraded_to_supergroup_id: int = None


@dataclass
class BasicGroupFullInfo(RawDataclass):
    """Дополнительная информация о базовой группе"""

    description: str = None
    creator_user_id: int = None
