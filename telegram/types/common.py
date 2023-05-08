from dataclasses import dataclass
from typing import Optional

from telegram.types.base import RawDataclass


@dataclass
class Contact(RawDataclass):
    """Контакт"""

    phone_number: str = None
    first_name: str = None
    last_name: str = None
    vcard: str = None
    user_id: int = None


@dataclass
class Location(RawDataclass):
    """Локация"""

    latitude: float = None
    longitude: float = None
    horizontal_accuracy: float = None


@dataclass
class Venue(RawDataclass):
    """Место сбора"""

    location: Location = None
    title: str = None
    address: str = None
    provider: str = None
    id: str = None
    type: str = None


@dataclass
class Usernames(RawDataclass):
    """Usernames"""

    active_usernames: list = None
    disabled_usernames: list = None
    editable_username: list = None

    @staticmethod
    def get_username(raw: dict) -> Optional[str]:
        if not raw.get('username') and raw.get('usernames'):
            active_usernames = raw['usernames'].get('active_usernames')
            if isinstance(active_usernames) and active_usernames:
                return raw['usernames']['active_usernames'][0]
