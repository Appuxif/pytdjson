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

        local = self.raw.pop('local')
        self.local_path = local['path']

        remote = self.raw.pop('remote')
        self.remote_id = remote['id']
        self.remote_unique_id = remote['unique_id']
