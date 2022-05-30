import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .types.text import TextParseMode
from .utils import Result, ResultCoro

if TYPE_CHECKING:
    from .client import AsyncTelegram


class BaseAPI:
    """Базовый класс API хелпера для телеграм клиента"""

    def __init__(self, client: 'AsyncTelegram', timeout: int = 30):
        self.client = client
        self._timeout = timeout

    def send_data(
        self,
        method: str,
        request_id: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> ResultCoro:
        """Асинхронный вызов метода"""
        timeout = timeout or self._timeout
        kwargs['@type'] = method
        return self.client.send_data(kwargs, request_id=request_id, timeout=timeout)

    def send_data_sync(
        self, method: str, request_id: Optional[str] = None, **kwargs: Any
    ) -> Result:
        """Синхронный вызов метода"""
        kwargs['@type'] = method
        return self.client.send_data_sync(kwargs, request_id=request_id)


class AuthAPI(BaseAPI):
    """
    API хелпер, который используется только в момента
    аутентификации клиента в телеграм
    """

    def get_authorization_state(self) -> ResultCoro:
        return self.send_data(
            'getAuthorizationState',
            request_id='getAuthorizationState',
        )

    def set_tdlib_parameters(self) -> ResultCoro:

        if not self.client.settings.api_id:
            raise ValueError('api_id not set')

        if not self.client.settings.api_hash:
            raise ValueError('api_id not set')

        parameters = {
            "use_test_dc": self.client.settings.use_test_dc,
            "api_id": self.client.settings.api_id,
            "api_hash": self.client.settings.api_hash,
            "device_model": self.client.settings.device_model,
            "system_version": self.client.settings.system_version,
            "application_version": self.client.settings.application_version,
            "system_language_code": self.client.settings.system_language_code,
            "database_directory": os.path.join(
                self.client.settings.files_directory, "database"
            ),
            "use_file_database": self.client.settings.use_file_database,
            "use_chat_info_database": self.client.settings.use_chat_info_database,
            "use_message_database": self.client.settings.use_message_database,
            "enable_storage_optimizer": self.client.settings.enable_storage_optimizer,
            "files_directory": os.path.join(
                self.client.settings.files_directory, "files"
            ),
        }
        return self.send_data(
            'setTdlibParameters',
            parameters=parameters,
        )

    def check_database_encryption_key(self) -> ResultCoro:
        return self.send_data(
            'checkDatabaseEncryptionKey',
            encryption_key=self.client.settings.database_encryption_key,
        )

    def set_authentication_phone_number(self) -> ResultCoro:
        phone = self.client.settings.phone

        if not phone:
            raise ValueError('phone not set')

        return self.send_data(
            'setAuthenticationPhoneNumber',
            phone_number=phone,
            allow_flash_call=False,
            is_current_phone_number=True,
        )

    def check_authentication_bot_token(self) -> ResultCoro:
        token = self.client.settings.bot_token

        if not token:
            raise ValueError('token not set')

        return self.send_data(
            'checkAuthenticationBotToken',
            token=token,
        )

    def check_authentication_code(self) -> ResultCoro:
        """Запрос для проверки кода авторизации"""
        auth_code = self.client.settings.auth_code

        if not auth_code:
            raise ValueError('auth_code not set')

        return self.send_data(
            'checkAuthenticationCode',
            code=auth_code,
        )

    def register_user(self) -> ResultCoro:
        """Запрос на регистрацию нового пользователя"""
        first_name = self.client.settings.first_name
        last_name = self.client.settings.last_name

        if not first_name:
            raise ValueError('first name not set')

        return self.send_data(
            'registerUser',
            first_name=str(first_name),
            last_name=str(last_name or ''),
        )

    def check_authentication_password(self) -> ResultCoro:
        password = self.client.settings.password

        if not password:
            raise ValueError('password not set')

        return self.send_data(
            'checkAuthenticationPassword',
            password=password,
        )


class API(BaseAPI):
    """API хелпер для телеграм клиента"""

    def get_me(self) -> ResultCoro:
        """Запрашивает личные данные клиента"""
        return self.send_data(
            'getMe',
        )

    def get_chat(self, chat_id: int) -> ResultCoro:
        """Запрашивает информацию о чате. Оффлайн метод"""
        return self.send_data(
            'getChat',
            chat_id=chat_id,
        )

    def get_chats(
        self,
        offset_order: int = 0,
        offset_chat_id: int = 0,
        limit: int = 100,
        chat_list: Optional[str] = None,
    ) -> ResultCoro:
        """Запрашивает список чатов"""
        return self.send_data(
            'getChats',
            offset_order=offset_order,
            offset_chat_id=offset_chat_id,
            limit=limit,
            chat_list=chat_list,
            timeout=600,
        )

    def load_chats(
        self, limit: int = 10, chat_list: Optional[str] = None
    ) -> ResultCoro:
        """Запрашивает загрузку чатов. Чаты будут приходить
        отдельными обновлениями через updateNewChat
        """
        return self.send_data(
            'loadChats',
            limit=limit,
            chat_list=chat_list,
        )

    def get_chat_history(
        self,
        chat_id: int,
        limit: int = 1000,
        from_message_id: int = 0,
        offset: int = 0,
        only_local: bool = False,
    ) -> ResultCoro:
        """Запрашивает историю чата"""
        return self.send_data(
            'getChatHistory',
            chat_id=chat_id,
            limit=limit,
            from_message_id=from_message_id,
            offset=offset,
            only_local=only_local,
        )

    def get_web_page_instant_view(
        self, url: str, force_full: bool = False
    ) -> ResultCoro:
        """Use this method to request instant preview of a webpage.
        Returns error with 404 if there is no preview for this webpage.

        :param url: URL of a webpage
        :param force_full: If true, the full instant view
            for the web page will be returned
        """
        return self.send_data(
            'getWebPageInstantView',
            url=url,
            force_full=force_full,
        )

    def get_user(self, user_id: int) -> ResultCoro:
        """Запрос на получение подробной информации о пользователе. Оффлайн"""
        return self.send_data(
            'getUser',
            user_id=user_id,
        )

    def get_supergroup(self, supergroup_id: int) -> ResultCoro:
        """Запрос на получение информации о супергруппе. Оффлайн"""
        return self.send_data(
            'getSupergroup',
            supergroup_id=supergroup_id,
        )

    def get_supergroup_full_info(self, supergroup_id: int) -> ResultCoro:
        """Запрос на получение полной информации о супергруппе. Кэшируется на 1 минуту"""
        return self.send_data(
            'getSupergroupFullInfo',
            supergroup_id=supergroup_id,
        )

    def get_basic_group(self, basic_group_id: int) -> ResultCoro:
        """Запрос на получение информации о базовой группе. Оффлайн метод"""
        return self.send_data(
            'getBasicGroup',
            basic_group_id=basic_group_id,
        )

    def get_basic_group_full_info(self, basic_group_id: int) -> ResultCoro:
        """Запрос на получение полной информации о базовой группе"""
        return self.send_data(
            'getBasicGroupFullInfo',
            basic_group_id=basic_group_id,
        )

    def get_message(self, message_id: int, chat_id: int) -> ResultCoro:
        """Запрос на получение информации о сообщении"""
        return self.send_data(
            'getMessage',
            message_id=message_id,
            chat_id=chat_id,
        )

    def get_callback_query_answer(
        self,
        chat_id: int,
        message_id: int,
        data: str,
        password: Optional[str] = None,
    ) -> ResultCoro:
        """Запрос на отправку ответа - нажатия на кнопку на клавиатуре бота"""

        if password is not None:
            payload = {
                '@type': 'callbackQueryPayloadDataWithPassword',
                'password': password,
                'data': data,
            }
        else:
            payload = {
                '@type': 'callbackQueryPayloadData',
                'data': data,
            }
        return self.send_data(
            'getCallbackQueryAnswer',
            chat_id=chat_id,
            message_id=message_id,
            payload=payload,
        )

    def open_chat(self, chat_id: int) -> ResultCoro:
        """Запрос на открытие чата"""
        return self.send_data(
            'openChat',
            chat_id=chat_id,
        )

    def close_chat(self, chat_id: int) -> ResultCoro:
        """Запрос на закрытие чата"""
        return self.send_data(
            'closeChat',
            chat_id=chat_id,
        )

    def close(self) -> ResultCoro:
        """Запрос на закрытие клиента"""
        return self.send_data(
            'close',
        )

    def log_out(self) -> ResultCoro:
        """Запрос на выход из клиента"""
        return self.send_data(
            'logOut',
        )

    def view_messages(self, chat_id: int, message_ids: List[int]) -> ResultCoro:
        """Запрос на просмотр сообщений. Все непрочитанные сообщения
        в чате с указанным ID окажутся прочитанными
        """
        return self.send_data(
            'viewMessages',
            chat_id=chat_id,
            message_ids=message_ids,
        )

    def send_message(
        self,
        chat_id: int,
        text: Optional[str] = None,
        parse_mode: Optional[TextParseMode] = None,
        disable_web_page_preview: bool = True,
        reply_to_message_id: int = 0,
        disable_notification: Optional[bool] = None,
        from_background: Optional[bool] = None,
        send_date: Optional[int] = None,
    ) -> ResultCoro:
        """Sends a message to a chat.
        The chat must be in the tdlib's database.
        If there is no chat in the DB, tdlib returns an error.
        Chat is being saved to the database when the client
        receives a message or when you call the `get_chats` method.
        """
        if text is None:
            raise ValueError('Text is None')

        formatted_text = {'@type': 'formattedText', 'text': text}

        if parse_mode is not None and parse_mode is not TextParseMode.NONE:
            result = self.parse_text_entities(text, parse_mode)
            result.is_valid()
            formatted_text = result.update

        input_message_content = {
            '@type': 'inputMessageText',
            'text': formatted_text,
            'disable_web_page_preview': disable_web_page_preview,
        }

        return self.send_data(
            'sendMessage',
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            input_message_content=input_message_content,
            options=_get_send_message_options(
                disable_notification,
                from_background,
                send_date,
            ),
        )

    def parse_text_entities(self, text: str, parse_mode: TextParseMode) -> Result:
        """Синхронный оффлайн запрос на парсинг текста"""
        return self.send_data_sync(
            'parseTextEntities',
            text=text,
            parse_mode={'@type': parse_mode.value, 'version': 2},
        )

    def resend_messages(self, chat_id: int, message_ids: List[int]) -> ResultCoro:
        """Запрос на переотправку неотправленного сообщения"""
        return self.send_data(
            'resendMessages',
            chat_id=chat_id,
            message_ids=message_ids,
        )

    def delete_messages(self, chat_id: int, message_ids: List[int]) -> ResultCoro:
        """Запрос на удаление сообщений"""
        return self.send_data(
            'deleteMessages',
            chat_id=chat_id,
            message_ids=message_ids,
            revoke=True,
        )

    def forward_messages(
        self,
        chat_id: int,
        from_chat_id: int,
        message_ids: List[int],
        disable_notification: Optional[bool] = None,
        from_background: Optional[bool] = None,
        send_date: Optional[int] = None,
    ) -> ResultCoro:
        """Запрос на пересылку сообщения из одного чата в другой"""
        return self.send_data(
            'forwardMessages',
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
            options=_get_send_message_options(
                disable_notification,
                from_background,
                send_date,
            ),
        )

    def ban_chat_member(
        self, chat_id: int, user_id: int, banned_until_date: int = 0
    ) -> ResultCoro:
        """Запрос на бан участника чата

        :param chat_id: Чат
        :param user_id: Пользователь
        :param banned_until_date: Время бана. 0 - навсегда
        """
        status = {
            '@type': 'chatMemberStatusBanned',
            'banned_until_date': banned_until_date,
        }
        return self.send_data(
            'setChatMemberStatus',
            chat_id=chat_id,
            user_id=user_id,
            status=status,
        )

    def join_chat_by_invite_link(self, invite_link: str) -> ResultCoro:
        """Запрос на присоединение к чату через инвайт ссылку"""
        return self.send_data(
            'joinChatByInviteLink',
            invite_link=invite_link,
        )

    def join_chat(self, chat_id: int) -> ResultCoro:
        """Запрос на присоединение к чату через ID"""
        return self.send_data(
            'joinChat',
            chat_id=chat_id,
        )

    def leave_chat(self, chat_id: int) -> ResultCoro:
        """Запрос на покидание чата"""
        return self.send_data(
            'leaveChat',
            chat_id=chat_id,
        )

    def search_public_chat(self, username: str) -> ResultCoro:
        """Запрос на поиск чата по его username"""
        return self.send_data(
            'searchPublicChat',
            username=username,
        )

    def create_private_chat(self, user_id: int) -> ResultCoro:
        """Запрос на создание приватного чата с пользователем"""
        return self.send_data(
            'createPrivateChat',
            user_id=user_id,
        )

    def get_message_link(self, chat_id: int, message_id: int) -> ResultCoro:
        """Запрос на генерацию ссылки для сообщения. Работает только для супергрупп"""
        return self.send_data(
            'getMessageLink',
            chat_id=chat_id,
            message_id=message_id,
        )


Options = Dict[str, Union[int, bool, str, Dict[str, Any]]]


def _get_send_message_options(
    disable_notification: Optional[bool] = None,
    from_background: Optional[bool] = None,
    send_date: Optional[int] = None,
) -> Options:
    """Собирает дополнительные параметры для отправки сообщения"""
    options: Options = {}
    if disable_notification is not None:
        options['disable_notification'] = disable_notification

    if from_background is not None:
        options['from_background'] = from_background

    if send_date is not None:
        options['scheduling_state'] = {
            '@type': 'messageSchedulingStateSendAtDate',
            'send_date': send_date,
        }

    if options:
        options['type'] = 'messageSendOptions'

    return options
