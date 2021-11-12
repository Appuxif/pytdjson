from dataclasses import dataclass
from functools import partial
from typing import Callable

from .base import build_from_mapping
from .message import Message, build_message

__all__ = ('UpdateNewMessage', 'build_update')


@dataclass(frozen=True)
class UpdateNewMessage:
    message: Message

    @classmethod
    def build(cls, update: dict) -> 'UpdateNewMessage':
        return cls(message=build_message(update['message']))


update_types_mapping = {'updateNewMessage': UpdateNewMessage.build}
build_update: Callable = partial(build_from_mapping, update_types_mapping)
