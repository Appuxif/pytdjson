from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass
from telegram.types.common import Usernames
from telegram.types.files import File


class UserStatus(str, Enum):
    """Онлайн статус пользователя"""

    EMPTY = 'userStatusEmpty'
    ONLINE = 'userStatusOnline'
    OFFLINE = 'userStatusOffline'
    RECENTLY = 'userStatusRecently'
    LAST_WEEK = 'userStatusLastWeek'
    LAST_MONTH = 'userStatusLastMonth'


@dataclass
class ProfilePhoto(RawDataclass):
    id: int = None
    small: File = None
    big: File = None
    # minithumbnail = None
    has_animation: bool = None
    is_personal: bool = None


class UserType(str, Enum):
    """Типы пользователей"""

    REGULAR = 'userTypeRegular'
    DELETED = 'userTypeDeleted'
    BOT = 'userTypeBot'
    UNKNOWN = 'userTypeUnknown'


@dataclass
class User(RawDataclass):
    """User"""

    id: int = None
    first_name: str = None
    last_name: str = None
    usernames: Usernames = None
    phone_number: str = None
    status: UserStatus = None
    profile_photo: ProfilePhoto = None
    # emoji_status: emojiStatus
    is_contact: bool = None
    is_mutual_contact: bool = None
    is_verified: bool = None
    is_premium: bool = None
    is_support: bool = None
    restriction_reason: str = None
    is_scam: bool = None
    is_fake: bool = None
    have_access: bool = None
    type: UserType = None
    language_code: str = None
    added_to_attachment_menu: bool = None

    # Для обратной совместимости
    username: str = None

    def _assign_raw(self):
        status = self.raw.get('status', {}).get('@type')
        if status:
            self.status = UserStatus(status)
        profile_photo = self.raw.get('profile_photo')
        if profile_photo:
            self.profile_photo = ProfilePhoto(profile_photo)
        self.type = UserType(self.raw['type']['@type'])

        self.username = Usernames.get_username(self.raw)


@dataclass
class UserFullInfo(RawDataclass):
    """Дополнительная информация о пользователе"""

    bio: str = None
    share_text: str = None
    description: str = None
    # block_list:BlockList

    # deprecated
    is_blocked: bool = None
