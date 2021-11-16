"""https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_update.html"""
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Callable

from .base import build_from_mapping
from .files import File
from .message import Message, build_message

__all__ = (
    'AuthorizationState',
    'UpdateAuthorizationState',
    'UpdateNewMessage',
    'UpdateFile',
    'build_update',
)


class AuthorizationState(Enum):
    """Состояния авторизации"""

    CLOSED = 'authorizationStateClosed'
    CLOSING = 'authorizationStateClosing'
    LOGGING_OUT = 'authorizationStateLoggingOut'
    READY = 'authorizationStateReady'
    WAIT_CODE = 'authorizationStateWaitCode'
    WAIT_ENCRYPTION_KEY = 'authorizationStateWaitEncryptionKey'
    WAIT_OTHER_DEVICE_CONFIRMATION = 'authorizationStateWaitOtherDeviceConfirmation'
    WAIT_PASSWORD = 'authorizationStateWaitPassword'
    WAIT_PHONE_NUMBER = 'authorizationStateWaitPhoneNumber'
    WAIT_REGISTRATION = 'authorizationStateWaitRegistration'
    WAIT_TDLIB_PARAMETERS = 'authorizationStateWaitTdlibParameters'


@dataclass
class UpdateAuthorizationState:
    raw: dict
    authorization_state: AuthorizationState = None

    def __post_init__(self):
        authorization_state = self.raw['authorization_state'].pop('@type')
        self.authorization_state = AuthorizationState(authorization_state)


@dataclass
class UpdateNewMessage:
    raw: dict
    message: Message = None

    def __post_init__(self):
        self.message = build_message(self.raw.pop('message'))


@dataclass
class UpdateFile:
    raw: dict
    file: File = None

    def __post_init__(self):
        self.file = File(self.raw.pop('file'))


update_types_mapping = {
    'updateAuthorizationState': UpdateAuthorizationState,
    'updateFile': UpdateFile,
    'updateNewMessage': UpdateNewMessage,
}
build_update: Callable = partial(build_from_mapping, update_types_mapping)
