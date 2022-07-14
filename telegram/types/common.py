from dataclasses import dataclass

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
