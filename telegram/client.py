import asyncio
import logging
import os
import signal
from collections import defaultdict
from dataclasses import dataclass
from types import FrameType
from typing import Any, Callable, DefaultDict, Dict, List, Optional
from uuid import uuid4

from . import VERSION
from .api import API
from .tdjson import TDJson
from .utils import Result

logger = logging.getLogger(__name__)


MESSAGE_HANDLER_TYPE: str = 'updateNewMessage'


@dataclass
class Settings:
    """Настройки телеграм клиента"""

    api_id: int
    api_hash: str
    database_encryption_key: str
    phone: Optional[str] = None
    password: Optional[str] = None
    bot_token: Optional[str] = None
    library_path: Optional[str] = None
    # worker: Optional[Type[BaseWorker]] = None
    files_directory: Optional[str] = None
    use_test_dc: bool = False
    use_message_database: bool = True
    device_model: str = 'python-telegram'
    application_version: str = VERSION
    system_version: str = 'unknown'
    system_language_code: str = 'en'
    login: bool = False
    default_workers_queue_size: int = 1000
    tdlib_verbosity: int = 2
    first_name: str = ''
    last_name: str = ''

    def __post_init__(self):

        if not self.bot_token and not self.phone:
            raise ValueError('You must provide bot_token or phone')


class Authorisation:
    """Класс авторизации телеграм клиента"""

    # TODO: Инкапсулировать методы для авторизации


class AsyncTelegram:
    """Асинхронный телеграм клиент"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api = API(self)

        self._authorized = False
        self._is_enabled = False
        self.auth_code = None

        self._updates: Dict[str, dict] = {}
        self._update_handlers: DefaultDict[str, List[Callable]] = defaultdict(list)

        self._tdjson = TDJson(
            library_path=settings.library_path,
            verbosity=settings.tdlib_verbosity,
        )

        self._loop = asyncio.new_event_loop()
        self._loop_tasks = []

        self.handler_workers_queue = asyncio.Queue(
            self.settings.default_workers_queue_size,
            loop=self._loop,
        )

        self.authorization_states_mapping = {
            None: self.get_authorization_state,
            'authorizationStateWaitTdlibParameters': self._set_initial_params,
            'authorizationStateWaitEncryptionKey': self._send_encryption_key,
            'authorizationStateWaitPhoneNumber': self._send_phone_number_or_bot_token,
            'authorizationStateWaitCode': self._send_auth_code,
            'authorizationStateWaitRegistration': self._send_register_user,
            'authorizationStateWaitPassword': self._send_auth_password,
            'authorizationStateReady': self._complete_authorization,
            'authorizationStateLoggingOut': lambda *a, **k: None,
            'authorizationStateClosing': lambda *a, **k: None,
            'authorizationStateClosed': self.kill,
        }

        self.authorization_state = None

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGABRT, self._signal_handler)

    def _signal_handler(self, signum: int, frame: FrameType) -> None:
        print('_signal_handler')
        self.stop()

    def run(self):
        self._is_enabled = True
        self.create_task(self._tdjson_worker())
        self.create_task(self._handlers_worker())
        self.run_forever()

    def run_forever(self):
        try:
            self._loop.run_forever()
        finally:
            self.cancel_tasks()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.run_until_complete(self.handler_workers_queue.join())

    def create_task(self, coro):
        self._loop_tasks.append(
            self._loop.create_task(coro),
        )

    def cancel_tasks(self):
        while self._loop_tasks:
            task = self._loop_tasks.pop()
            task.cancel()

    async def _wait_futures(self, fs, timeout=None):
        done, pending = await asyncio.wait(
            fs,
            loop=self._loop,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )
        [f.cancel() for f in pending]
        [f.result() for f in done]

    def stop(self):
        self._is_enabled = False
        self._loop.stop()

    def kill(self):
        self.stop()
        self._loop.close()
        self._tdjson.stop()

    async def _tdjson_worker(self) -> None:
        while self._is_enabled:
            update = self._tdjson.receive()

            if update:
                await self._update_async_result(update)
                await self._run_handlers(update)
            await asyncio.sleep(0.1)

    async def _handlers_worker(self) -> None:

        while self._is_enabled:
            handler, update = await self.handler_workers_queue.get()

            try:
                result = handler(update)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.exception('handlers_worker error')

            self.handler_workers_queue.task_done()
            await asyncio.sleep(0.1)

    async def _update_async_result(self, update: Dict[Any, Any]) -> None:

        # for authorizationProcess @extra.request_id doesn't work
        _special_types = ('updateAuthorizationState',)

        if update.get('@type') in _special_types:
            request_id = update['@type']
        else:
            request_id = update.get('@extra', {}).get('request_id')

        if not request_id:
            logger.debug('request_id has not been found in the update')
        else:
            self._updates[request_id] = update

    async def send_data(
        self, data: Dict[Any, Any], request_id: Optional[str] = None
    ) -> Result:

        data.setdefault('@extra', {})
        request_id = request_id or data['@extra'].get('request_id') or uuid4().hex
        data['@extra']['request_id'] = request_id
        self._tdjson.send(data)
        update = await self._get_update(request_id)
        if update:
            return Result(data, update, request_id=request_id)

    def send_data_sync(
        self, data: Dict[Any, Any], request_id: Optional[str] = None
    ) -> Result:
        data.setdefault('@extra', {})
        request_id = request_id or data['@extra'].get('request_id') or uuid4().hex
        data['@extra']['request_id'] = request_id
        update = self._tdjson.td_execute(data)
        return Result(data, update, request_id=request_id)

    async def _get_update(self, request_id: Optional[str] = None) -> Dict[Any, Any]:
        while self._is_enabled:
            result = self._updates.pop(request_id, None)
            if result is not None:
                return result
            await asyncio.sleep(0.1)

    async def _run_handlers(self, update: Dict[Any, Any]) -> None:
        update_type: str = update.get('@type', 'unknown')
        for handler in self._update_handlers[update_type]:
            await self.handler_workers_queue.put((handler, update))

    def add_message_handler(self, func: Callable) -> None:
        self.add_update_handler(MESSAGE_HANDLER_TYPE, func)

    def add_update_handler(self, handler_type: str, func: Callable) -> None:
        if func not in self._update_handlers[handler_type]:
            self._update_handlers[handler_type].append(func)

    def clear_update_handler(self, handler_type: str) -> None:
        self._update_handlers[handler_type].clear()

    async def _authorization_state_handler(self, update):
        if not self._is_enabled:
            return

        try:
            self.authorization_state = update['authorization_state']['@type']
        except KeyError:
            self.authorization_state = update['@type']

        method = self.authorization_states_mapping[self.authorization_state]
        await method()

    def login(self, timeout=10) -> None:
        """Login process (blocking)

        Must be called before any other call.
        It sends initial params to the tdlib, sets database encryption key, etc.
        """

        self.add_update_handler(
            'updateAuthorizationState',
            self._authorization_state_handler,
        )

        self.create_task(self._login())
        h = self._loop.call_later(timeout, self.stop)
        self.run()
        h.cancel()
        self.clear_update_handler('updateAuthorizationState')

        if not self._authorized:
            raise TimeoutError('authorization timed out')

    async def _login(self) -> None:
        result = await self.get_authorization_state()

        if not result:
            return

        result.is_valid()

        await self._authorization_state_handler(result.update)

    async def _login_wait_code(self, timeout=30):
        timer = self._loop.time()
        while self._is_enabled and not self._authorized:

            await asyncio.sleep(1)

            if self._loop.time() - timer < timeout:
                continue

            if self.authorization_state not in [
                'authorizationStateWaitCode',
                'authorizationStateWaitPassword',
            ]:
                self.stop()
                raise TimeoutError('LOGIN TOO LONG')

            timer = self._loop.time()

        self.stop()

    def get_authorization_state(self):
        data = {'@type': 'getAuthorizationState'}

        return self.send_data(data, request_id='getAuthorizationState')

    def _set_initial_params(self):
        data = {
            '@type': 'setTdlibParameters',
            'parameters': {
                'use_test_dc': self.settings.use_test_dc,
                'api_id': self.settings.api_id,
                'api_hash': self.settings.api_hash,
                'device_model': self.settings.device_model,
                'system_version': self.settings.system_version,
                'application_version': self.settings.application_version,
                'system_language_code': self.settings.system_language_code,
                'database_directory': os.path.join(
                    self.settings.files_directory, 'database'
                ),
                'use_message_database': self.settings.use_message_database,
                'files_directory': os.path.join(self.settings.files_directory, 'files'),
            },
        }

        return self.send_data(data, request_id='updateAuthorizationState')

    def _send_encryption_key(self):
        data = {
            '@type': 'checkDatabaseEncryptionKey',
            'encryption_key': self.settings.database_encryption_key,
        }

        return self.send_data(data, request_id='updateAuthorizationState')

    def _send_phone_number_or_bot_token(self):
        """Sends phone number or a bot_token"""
        if self.settings.phone:
            return self._send_phone_number()
        elif self.settings.bot_token:
            return self._send_bot_token()
        else:
            raise RuntimeError('Unknown mode: both bot_token and phone are None')

    def _send_phone_number(self):
        data = {
            '@type': 'setAuthenticationPhoneNumber',
            'phone_number': self.settings.phone,
            'allow_flash_call': False,
            'is_current_phone_number': True,
        }

        return self.send_data(data, request_id='updateAuthorizationState')

    def _send_bot_token(self):
        data = {
            '@type': 'checkAuthenticationBotToken',
            'token': self.settings.bot_token,
        }

        return self.send_data(data, request_id='updateAuthorizationState')

    def _send_auth_code(self):
        auth_code = input('auth code: ')
        data = {'@type': 'checkAuthenticationCode', 'code': str(auth_code)}

        return self.send_data(data, request_id='updateAuthorizationState')

    def _send_register_user(self):

        if not self.settings.first_name:
            raise ValueError('first name not set')

        data = {
            '@type': 'registerUser',
            'first_name': str(self.settings.first_name),
            'last_name': str(self.settings.last_name or ''),
        }

        return self.send_data(data, request_id='updateAuthorizationState')

    def _send_auth_password(self):
        password = self.settings.password

        if not password:
            raise ValueError('password not set')

        data = {'@type': 'checkAuthenticationPassword', 'password': password}

        return self.send_data(data, request_id='updateAuthorizationState')

    async def _complete_authorization(self) -> None:
        self._authorized = True
        self.stop()
