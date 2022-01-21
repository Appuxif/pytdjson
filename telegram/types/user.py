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

    def _assign_raw(self):
        self.small = File(self.raw['small'])
        self.big = File(self.raw['big'])


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
        self.status = UserStatus(self.raw['status']['@type'])
        self.profile_photo = ProfilePhoto(self.raw['profile_photo'])
        self.type = UserType(self.raw['type']['@type'])