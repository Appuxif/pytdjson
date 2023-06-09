from dataclasses import dataclass
from typing import List

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


@dataclass
class DocumentFile(RawDataclass):
    """Документ"""

    file_name: str = None
    mime_type: str = None
    document: File = None


@dataclass
class PhotoSize(RawDataclass):
    """Размеры фото"""

    type: str = None
    photo: File = None
    width: int = None
    height: int = None
    progressive_sizes: List[int] = None

    def _assign_raw(self):
        self.progressive_sizes = [int(size) for size in self.raw['progressive_sizes']]


@dataclass
class PhotoFile(RawDataclass):
    """Фото"""

    has_stickers: bool = None
    sizes: List[PhotoSize] = None

    def _assign_raw(self):
        self.sizes = [PhotoSize(size) for size in self.raw['sizes']]


@dataclass
class VideoFile(RawDataclass):
    """Видео-файл"""

    duration: int = None
    width: int = None
    height: int = None
    file_name: str = None
    mime_type: str = None
    has_stickers: bool = None
    supports_streaming: bool = None
    video: File = None


@dataclass
class VideoNote(RawDataclass):
    """Видео-заметка"""

    duration: int = None
    # waveform: bytes = None
    length: int = None
    video: File = None


@dataclass
class VoiceNote(RawDataclass):
    """Файл голосового сообщения"""

    duration: int = None
    # waveform: bytes = None
    mime_type: str = None
    voice: File = None
