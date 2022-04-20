from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass
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
    id: int = None
    small: File = None
    big: File = None
    minithumbnail = None
    has_animation: bool = None


class UserType(Enum):
    """Типы пользователей"""

    BOT = 'userTypeBot'
    DELETED = 'userTypeDeleted'
    REGULAR = 'userTypeRegular'
    UNKNOWN = 'userTypeUnknown'


@dataclass
class User(RawDataclass):
    id: int = None
    first_name: str = None
    last_name: str = None
    username: str = None
    phone_number: str = None
    status: UserStatus = None
    profile_photo: ProfilePhoto = None
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
        status = self.raw.get('status', {}).get('@type')
        if status:
            self.status = UserStatus(status)
        profile_photo = self.raw.get('profile_photo')
        if profile_photo:
            self.profile_photo = ProfilePhoto(profile_photo)
        self.type = UserType(self.raw['type']['@type'])


@dataclass
class UserFullInfo(RawDataclass):
    """Дополнительная информация о пользователе"""

    is_blocked: bool = None
    bio: str = None
    share_text: str = None
    description: str = None
