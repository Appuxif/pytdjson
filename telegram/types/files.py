from dataclasses import dataclass

from telegram.types.base import RawDataclass


@dataclass
class File(RawDataclass):
    """Файл"""

    id: int = None
    size: int = None
    expected_size: int = None
    local_path: str = None
    remote_id: int = None
    remote_unique_id: int = None

    def _assign_raw(self):
        self.local_path = self.raw['local']['path']
        self.remote_id = self.raw['remote']['id']
        self.remote_unique_id = self.raw['remote']['unique_id']


@dataclass
class AnimationFile(RawDataclass):
    """Анимация"""

    duration: int = None
    width: int = None
    height: int = None
    file_name: str = None
    mime_type: str = None
    has_stickers: bool = None
    animation: File = None


@dataclass
class AudioFile(RawDataclass):
    """Аудио"""

    duration: int = None
    title: str = None
    performer: str = None
    file_name: str = None
    mime_type: str = None
    audio: File = None
