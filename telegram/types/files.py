from dataclasses import dataclass


@dataclass
class File:
    """Файл"""

    id: int
    size: int
    expected_size: int
    local_path: str
    remote_id: int
    remote_unique_id: int


@dataclass
class Animation:
    """Анимация"""

    duration: int
    width: int
    height: int
    file_name: str
    mime_type: str
    has_stickers: bool
    animation: File


@dataclass
class Audio:
    """Аудио"""

    duration: int
    title: str
    performer: str
    file_name: str
    mime_type: str
    audio: File


@dataclass
class Contact:
    """Контакт"""

    phone_number: str
    first_name: str
    last_name: str
    vcard: str
    user_id: str
