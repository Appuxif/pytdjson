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
        self.local_path = self.raw['local'].pop('path')
        self.remote_id = self.raw['remote'].pop('id')
        self.remote_unique_id = self.raw['remote'].pop('unique_id')


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

    def _assign_raw(self):
        self.animation = File(self.raw.pop('animation'))


@dataclass
class AudioFile(RawDataclass):
    """Аудио"""

    duration: int = None
    title: str = None
    performer: str = None
    file_name: str = None
    mime_type: str = None
    audio: File = None

    def _assign_raw(self):
        self.audio = File(self.raw.pop('audio'))
