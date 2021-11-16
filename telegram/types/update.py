"""https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_update.html"""
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Callable

from .base import build_from_mapping
from .message import Message, build_message

__all__ = ('UpdateNewMessage', 'build_update')


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


@dataclass(frozen=True)
class UpdateAuthorizationState:
    authorization_state: AuthorizationState

    @classmethod
    def build(cls, update: dict) -> 'UpdateAuthorizationState':
        authorization_state = update['authorization_state']['@type']
        return cls(authorization_state=AuthorizationState(authorization_state))


@dataclass(frozen=True)
class UpdateNewMessage:
    message: Message

    @classmethod
    def build(cls, update: dict) -> 'UpdateNewMessage':
        return cls(message=build_message(update['message']))


update_types_mapping = {
    'updateAuthorizationState': UpdateAuthorizationState.build,
    'updateNewMessage': UpdateNewMessage.build,
}
build_update: Callable = partial(build_from_mapping, update_types_mapping)
