import asyncio
import logging
import signal
from asyncio import AbstractEventLoop, Task
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from types import FrameType
from typing import Any, Callable, Coroutine, DefaultDict, Dict, List, Optional, Tuple
from uuid import uuid4

from . import VERSION
from .api import API, AuthAPI
from .tdjson import TDJson
from .types.base import RawDataclass
from .types.update import AuthorizationState, Update, UpdateAuthorizationState
from .utils import Result, ResultCoro

MESSAGE_HANDLER_TYPE: str = 'updateNewMessage'


@dataclass
class Settings:
    """
    Настройки телеграм клиента
    """

    api_id: int  # API ID телеграм приложения
    api_hash: str  # API Hash телеграм приложения
    database_encryption_key: str  # Ключ шифрования БД
    phone: Optional[str] = None  # Телефон клиента
    auth_code: Optional[str] = None  # Код авторизации, если известен
    password: Optional[str] = None  # Пароль авторизации, если имеется
    bot_token: Optional[str] = None  # Токен бота, если не используется клиент
    library_path: Optional[str] = None  # Путь до библиотеки libtdjson
    files_directory: Optional[str] = None  # Путь до файлов клиента
    use_test_dc: bool = False  # Использовать тестовый телеграм сервер
    use_message_database: bool = True  # Использовать БД для сообщений
    use_file_database: bool = True  # Использовать БД для файлов
    use_chat_info_database: bool = True  # Использовать БД для чатов
    enable_storage_optimizer: bool = True  # Использовать оптимизатор хранилища
    device_model: str = 'python-telegram'  # Модель, может быть любой строкой
    application_version: str = VERSION  # Версия, может быть любой строкой
    system_version: str = 'unknown'  # Версия, может быть любой строкой
    system_language_code: str = 'en'  # Код языка
    default_workers_queue_size: int = 1000  # Длина очереди обновлений
    tdlib_verbosity: int = 2  # Логирование tdlib
    first_name: str = ''  # Имя клиента - только для регистрации
    last_name: str = ''  # Фамилия клиента - только для регистрации
    update_timeout: int = 30  # Время ожидания ответа от tdlib
    tdjson_workers: int = 3  # Количество воркеров, который слушают tdlib
    handlers_workers: int = 3  # Количество воркеров, которые обрабатывают обновления

    def __post_init__(self) -> None:

        if not self.bot_token and not self.phone:
            raise ValueError('You must provide bot_token or phone')


UpdateHandlerType = Callable[[Any], Coroutine[Any, Any, None]]


class AsyncTelegram:
    """Асинхронный телеграм клиент"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api = API(self, settings.update_timeout)
        self.authorization = Authorization(self)

        self.logger = logging.getLogger(str(self))

        self.is_enabled = False
        self.is_killing = False

        self._updates: Dict[str, Dict[Any, Any]] = {}
        self._update_handlers: DefaultDict[str, List[UpdateHandlerType]] = defaultdict(
            list
        )

        self._tdjson = TDJson(
            library_path=settings.library_path,
            verbosity=settings.tdlib_verbosity,
        )

        self._loop = asyncio.new_event_loop()
        self._loop.set_exception_handler(self._loop_exception_handler)
        self._loop_tasks: List[Task[Any]] = []

        self.handler_workers_queue = asyncio.Queue[
            Tuple[UpdateHandlerType, Dict[Any, Any]]
        ](
            self.settings.default_workers_queue_size,
            loop=self._loop,
        )

        self._executor = ThreadPoolExecutor(max_workers=1)

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGABRT, self._signal_handler)

    def _loop_exception_handler(
        self, loop: AbstractEventLoop, context: Dict[Any, Any]
    ) -> None:
        if not isinstance(context.get('exception'), asyncio.exceptions.CancelledError):
            self.logger.exception(context.get('message'))
        self.stop()

    def _signal_handler(self, signum: int, frame: Optional[FrameType]) -> None:
        self.logger.debug('stop signal received')
        self.stop(kill=True)

    def run(self) -> None:
        self.logger.debug('running...')
        self.is_enabled = True
        for _ in range(self.settings.tdjson_workers):
            self.create_task(self._tdjson_worker())
        for _ in range(self.settings.handlers_workers):
            self.create_task(self._handlers_worker())
        self.run_forever()

    def run_forever(self) -> None:
        try:
            self.logger.debug('run forever')
            self._loop.run_forever()
        finally:
            self.logger.debug('cancel running forever')
            self.cancel_tasks()

            self._loop.run_until_complete(self.handler_workers_queue.join())
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())

            if self.is_killing:
                self._loop.close()
                self._tdjson.stop()

    def create_task(self, coro: Coroutine[Any, Any, Any]) -> None:
        self.logger.debug(f'created task: {coro.__name__}')
        task = self._loop.create_task(coro)

        def handler(t: Task[Any]) -> None:
            t.result()

        task.add_done_callback(handler)
        self._loop_tasks.append(task)

    def cancel_tasks(self) -> None:
        [task.cancel() for task in self._loop_tasks]
        while self._loop_tasks:
            task = self._loop_tasks.pop()
            self.logger.debug('getting result: %s', task)
            try:
                task.result()
            except asyncio.exceptions.InvalidStateError:
                pass
        self.logger.debug('all tasks canceled')

    async def _wait_futures(
        self, fs: List[Coroutine[Any, Any, Any]], timeout: Optional[int] = None
    ) -> None:
        done, pending = await asyncio.wait(
            fs,
            loop=self._loop,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )
        [f.cancel() for f in pending]
        [f.result() for f in done]

    def stop(self, kill: bool = False) -> None:
        if not self.is_enabled or self.is_killing:
            return

        if kill:
            self.is_killing = True

        self.is_enabled = False
        self._loop.stop()

    def kill(self) -> None:
        self.stop(kill=True)

    async def _tdjson_worker(self) -> None:
        # self.logger.debug('tdjson worker starting...')
        loop = asyncio.get_running_loop()

        while self.is_enabled:
            update = await loop.run_in_executor(self._executor, self._tdjson.receive)

            if update:
                await self._update_async_result(update)
                await self._run_handlers(update)

    def _prepare_update(self, update: Dict[Any, Any]) -> RawDataclass:
        return Update(update)

    async def _handlers_worker(self) -> None:
        # self.logger.debug('handlers worker starting...')
        while self.is_enabled:
            handler, update = await self.handler_workers_queue.get()

            try:
                prepared_update = self._prepare_update(update)
                result = handler(prepared_update)
                if asyncio.iscoroutine(result):
                    await result
            finally:
                self.handler_workers_queue.task_done()

    async def _update_async_result(self, update: Dict[Any, Any]) -> None:

        # for authorizationProcess @extra.request_id doesn't work
        _special_types = ('updateAuthorizationState',)

        if update.get('@type') in _special_types:
            request_id = update['@type']
        else:
            request_id = update.get('@extra', {}).get('request_id')

        if request_id:
            self._updates[request_id] = update

    async def send_data(
        self,
        data: Dict[Any, Any],
        request_id: Optional[str] = None,
        timeout: int = 30,
    ) -> Result:

        data.setdefault('@extra', {})
        request_id = request_id or data['@extra'].get('request_id') or uuid4().hex
        data['@extra']['request_id'] = request_id
        self.logger.debug(f'send_data: {data}')
        self._tdjson.send(data)
        update = await self._get_update(request_id, timeout=timeout)
        return Result(data, update, request_id=request_id)

    def send_data_sync(
        self, data: Dict[Any, Any], request_id: Optional[str] = None
    ) -> Result:
        data.setdefault('@extra', {})
        request_id = request_id or data['@extra'].get('request_id') or uuid4().hex
        data['@extra']['request_id'] = request_id
        update = self._tdjson.td_execute(data)
        return Result(data, update, request_id=request_id)

    async def _get_update(
        self,
        request_id: str,
        timeout: int = 30,
    ) -> Dict[Any, Any]:
        loop = asyncio.get_running_loop()
        timer = loop.time()
        while self.is_enabled:
            result = self._updates.pop(request_id, None)
            if result is not None:
                self.logger.debug(f'get_update: {request_id} {result}')
                return result
            await asyncio.sleep(0.1)

            if loop.time() - timer > timeout:
                raise TimeoutError(f'result not set {request_id}')
        return {}

    async def _run_handlers(self, update: Dict[Any, Any]) -> None:
        update_type: str = update.get('@type', 'unknown')
        for handler in self._update_handlers[update_type]:
            await self.handler_workers_queue.put((handler, update))

    def add_message_handler(
        self, func_or_coro: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> None:
        self.add_update_handler(MESSAGE_HANDLER_TYPE, func_or_coro)

    def add_update_handler(
        self,
        handler_type: str,
        func_or_coro: Callable[[Any], Coroutine[Any, Any, None]],
    ) -> None:
        self.logger.debug(
            f'update handler added: {handler_type} {func_or_coro.__name__}'
        )
        if func_or_coro not in self._update_handlers[handler_type]:
            self._update_handlers[handler_type].append(func_or_coro)

    def clear_update_handler(self, handler_type: str) -> None:
        self._update_handlers[handler_type].clear()

    def login(self, timeout: int = 10) -> bool:
        """Login process (blocking)

        Must be called before any other call.
        It sends initial params to the tdlib, sets database encryption key, etc.
        """
        result = self.authorization.run(timeout)
        return result


class Authorization:
    """Класс авторизации телеграм клиента"""

    def __init__(self, client: AsyncTelegram):
        self.client = client
        self.api = AuthAPI(self.client, client.settings.update_timeout)

        self.authorization_states_mapping = {
            None: self.api.get_authorization_state,
            AuthorizationState.WAIT_TDLIB_PARAMETERS: self.api.set_tdlib_parameters,
            AuthorizationState.WAIT_ENCRYPTION_KEY: self.api.check_database_encryption_key,
            AuthorizationState.WAIT_PHONE_NUMBER: self.set_phone_number_or_bot_token,
            AuthorizationState.WAIT_CODE: self.api.check_authentication_code,
            AuthorizationState.WAIT_REGISTRATION: self.api.register_user,
            AuthorizationState.WAIT_PASSWORD: self.api.check_authentication_password,
            AuthorizationState.READY: self.complete_authorization,
            AuthorizationState.LOGGING_OUT: self.handle_logging_out,
            AuthorizationState.CLOSING: self.api.get_authorization_state,
            AuthorizationState.CLOSED: self.kill_client,
        }

        self.authorized = False
        self.state = None

    async def authorization_state_handler(
        self, update: UpdateAuthorizationState
    ) -> None:
        if not self.client.is_enabled:
            return

        self.state = update.authorization_state
        self.client.logger.debug(f'authorization state received: {self.state}')

        method = self.authorization_states_mapping[self.state]
        result = await method()
        result.is_valid()

    def run(self, timeout: int) -> bool:
        """Запускает процесс авторизации клиента"""
        self.client.add_update_handler(
            'updateAuthorizationState',
            self.authorization_state_handler,
        )
        self.client.create_task(self._wait_code(timeout))
        self.client.run()

        if not self.authorized:
            raise RuntimeError('authorization fails')

        return self.authorized

    async def _wait_code(self, timeout: int = 30) -> None:
        if timeout is None:
            return

        loop = self.client._loop  # noqa
        timer = loop.time()

        while self.client.is_enabled and not self.authorized:

            await asyncio.sleep(1)

            if loop.time() - timer < timeout:
                continue

            raise TimeoutError('LOGIN TOO LONG')

    def set_phone_number_or_bot_token(self) -> ResultCoro:
        """Sends phone number or a bot_token"""
        if self.client.settings.phone:
            coro = self.api.set_authentication_phone_number()
        elif self.client.settings.bot_token:
            coro = self.api.check_authentication_bot_token()
        else:
            raise RuntimeError('Unknown mode: both bot_token and phone are None')
        return coro

    async def complete_authorization(self) -> Result:
        self.authorized = True
        self.client.stop()
        return Result({}, {})

    async def handle_logging_out(self) -> Result:
        self.client.logger.warning('LOGGING OUT')
        return Result({}, {})

    async def kill_client(self) -> Result:
        await self.client.api.close()
        self.client.kill()
        return Result({}, {})
