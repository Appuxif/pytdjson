from dataclasses import dataclass


@dataclass
class File:
    """Файл"""

    raw: dict

    id: int = None
    size: int = None
    expected_size: int = None
    local_path: str = None
    remote_id: int = None
    remote_unique_id: int = None

    def __post_init__(self):
        self.id = self.raw.pop('id')
        self.size = self.raw.pop('size')
        self.expected_size = self.raw.pop('expected_size')

        self.local_path = self.raw['local'].pop('path')

        self.remote_id = self.raw['remote'].pop('id')
        self.remote_unique_id = self.raw['remote'].pop('unique_id')


@dataclass
class AnimationFile:
    """Анимация"""

    raw: dict

    duration: int = None
    width: int = None
    height: int = None
    file_name: str = None
    mime_type: str = None
    has_stickers: bool = None
    animation: File = None

    def __post_init__(self):
        self.duration = self.raw.pop('duration')
        self.width = self.raw.pop('width')
        self.height = self.raw.pop('height')
        self.file_name = self.raw.pop('file_name')
        self.mime_type = self.raw.pop('mime_type')
        self.has_stickers = self.raw.pop('has_stickers')
        self.animation = File(self.raw.pop('animation'))


@dataclass
class AudioFile:
    """Аудио"""

    raw: dict

    duration: int = None
    title: str = None
    performer: str = None
    file_name: str = None
    mime_type: str = None
    audio: File = None

    def __post_init__(self):
        self.duration = self.raw.pop('duration')
        self.title = self.raw.pop('title')
        self.performer = self.raw.pop('performer')
        self.file_name = self.raw.pop('file_name')
        self.mime_type = self.raw.pop('mime_type')
        self.audio = File(self.raw.pop('audio'))
