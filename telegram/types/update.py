"""https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_update.html"""
from dataclasses import dataclass
from enum import Enum

from .base import ObjectBuilder, RawDataclass
from .basicgroup import BasicGroup
from .chat import Chat
from .files import File
from .message import Message
from .supergroup import Supergroup, SupergroupFullInfo
from .user import User, UserFullInfo


class AuthorizationState(str, Enum):
    """Состояния авторизации"""

    WAIT_TDLIB_PARAMETERS = 'authorizationStateWaitTdlibParameters'
    WAIT_PHONE_NUMBER = 'authorizationStateWaitPhoneNumber'
    WAIT_EMAIL_ADDRESS = 'authorizationStateWaitEmailAddress'
    WAIT_EMAIL_CODE = 'authorizationStateWaitEmailCode'
    WAIT_CODE = 'authorizationStateWaitCode'
    WAIT_OTHER_DEVICE_CONFIRMATION = 'authorizationStateWaitOtherDeviceConfirmation'
    WAIT_REGISTRATION = 'authorizationStateWaitRegistration'
    WAIT_PASSWORD = 'authorizationStateWaitPassword'
    READY = 'authorizationStateReady'
    LOGGING_OUT = 'authorizationStateLoggingOut'
    CLOSING = 'authorizationStateClosing'
    CLOSED = 'authorizationStateClosed'


@dataclass
class UpdateAuthorizationState(RawDataclass):
    authorization_state: AuthorizationState = None

    def _assign_raw(self):
        authorization_state = self.raw['authorization_state']['@type']
        self.authorization_state = AuthorizationState(authorization_state)


@dataclass
class UpdateNewMessage(RawDataclass):
    message: Message = None


@dataclass
class UpdateFile(RawDataclass):
    file: File = None


@dataclass
class UpdateNewChat(RawDataclass):
    """Обновление с новым чатом"""

    chat: Chat = None


@dataclass
class UpdateUser(RawDataclass):
    """Обновление с пользователем"""

    user: User = None


@dataclass
class UpdateUserFullInfo(RawDataclass):
    """Обновление с дополнительной информацией о пользователе"""

    user_id: int = None
    user_full_info: UserFullInfo = None


@dataclass
class UpdateSupergroup(RawDataclass):
    """Обновление с супергруппой"""

    supergroup: Supergroup = None


@dataclass
class UpdateSupergroupFullInfo(RawDataclass):
    """Обновление с супергруппой"""

    supergroup_id: int = None
    supergroup_full_info: SupergroupFullInfo = None


@dataclass
class UpdateBasicGroup(RawDataclass):
    """Обновление с базовой группой"""

    basic_group: BasicGroup = None


class UpdateBuilder(ObjectBuilder):
    """Билдер, возвращает один из типов Update"""

    mapping = {
        'updateAuthorizationState': UpdateAuthorizationState,
        'updateFile': UpdateFile,
        'updateNewMessage': UpdateNewMessage,
        'updateNewChat': UpdateNewChat,
        'updateUser': UpdateUser,
        'updateUserFullInfo': UpdateUserFullInfo,
        'updateSupergroup': UpdateSupergroup,
        'updateSupergroupFullInfo': UpdateSupergroupFullInfo,
    }


Update = UpdateBuilder()
