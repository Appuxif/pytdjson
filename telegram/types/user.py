from dataclasses import dataclass
from enum import Enum

from telegram.types.base import RawDataclass
from telegram.types.common import Usernames
from telegram.types.files import File
from telegram.types.text import FormattedText


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
    # accent_color_id
    # background_custom_emoji_id
    # upgraded_gift_colors
    # profile_accent_color_id
    # profile_background_custom_emoji_id
    # emoji_status: emojiStatus
    is_contact: bool = None
    is_mutual_contact: bool = None
    is_close_friend: bool = None
    # verification_status
    # is_verified: bool = None
    is_premium: bool = None
    is_support: bool = None
    # restriction_info
    # restriction_reason: str = None
    # has_active_stories
    # has_unread_active_stories
    # restricts_new_chats
    # paid_message_star_count
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

    # personal_photo
    # photo
    # public_photo
    # block_list:BlockList
    # can_be_called
    # supports_video_calls
    # has_private_calls
    # has_private_forwards
    # has_restricted_voice_and_video_note_messages
    # has_posted_to_profile_stories
    # has_sponsored_messages_enabled
    # need_phone_number_privacy_exception
    # set_chat_background
    bio: str = None
    bio_formatted: FormattedText = None
    # birthdate
    # personal_chat_id
    # gift_count
    # group_in_common_count
    # incoming_paid_message_star_count
    # outgoing_paid_message_star_count
    # gift_settings
    # bot_verification
    # main_profile_tab
    # first_profile_audio
    # rating
    # pending_rating
    # pending_rating_date
    # note
    # business_info
    # bot_info

    def _assign_raw(self):
        if 'bio' in self.raw:
            self.bio_formatted = FormattedText(self.raw['bio'])
            self.bio = self.bio_formatted.text
