from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from telegram.types.base import RawDataclass, RawDataclassField
from telegram.types.files import File


class UserStatus(Enum):
    """Онлайн статус пользователя"""

    EMPTY = 'userStatusEmpty'
    LAST_MONTH = 'userStatusLastMonth'
    LAST_WEEK = 'userStatusLastWeek'
    OFFLINE = 'userStatusOffline'
    ONLINE = 'userStatusOnline'
    RECENTLY = 'userStatusRecently'


@dataclass
class ProfilePhoto(RawDataclass):
    """Фото профиля"""

    _no_assign_raw = True
    id: int = RawDataclassField[int]()
    small: File = RawDataclassField[File]()
    big: File = RawDataclassField[File]()
    minithumbnail: Dict[Any, Any] = RawDataclassField[Dict[Any, Any]]()
    has_animation: bool = RawDataclassField[bool]()


class UserType(Enum):
    """Типы пользователей"""

    BOT = 'userTypeBot'
    DELETED = 'userTypeDeleted'
    REGULAR = 'userTypeRegular'
    UNKNOWN = 'userTypeUnknown'


@dataclass
class User(RawDataclass):
    id: int = RawDataclassField()
    first_name: str = RawDataclassField()
    last_name: str = RawDataclassField()
    username: str = RawDataclassField()
    phone_number: str = RawDataclassField()
    status: UserStatus = RawDataclassField[UserStatus](value_getter=('status', '@type'))
    profile_photo: ProfilePhoto = RawDataclassField()

    is_contact: bool = None
    is_mutual_contact: bool = None
    is_verified: bool = None
    is_support: bool = None
    restriction_reason_: str = None
    is_scam: bool = None
    is_fake: bool = None
    have_access: bool = None
    type: UserType = None
    language_code: str = None

    def _assign_raw(self):
        # status = self.raw.get('status', {}).get('@type')
        # if status:
        #     self.status = UserStatus(status)
        # profile_photo = self.raw.get('profile_photo')
        # if profile_photo:
        #     self.profile_photo = ProfilePhoto(profile_photo)
        self.type = UserType(self.raw['type']['@type'])


@dataclass
class UserFullInfo(RawDataclass):
    """Дополнительная информация о пользователе"""

    is_blocked: bool = None
    bio: str = None
    share_text: str = None
    description: str = None
