import os
from typing import TYPE_CHECKING

from .types.text import TextParseMode

if TYPE_CHECKING:
    from .client import AsyncTelegram


class BaseAPI:
    """Базовый класс API хелпера для телеграм клиента"""

    def __init__(self, client: 'AsyncTelegram'):
        self.client = client

    def send_data(self, method, request_id=None, **kwargs):
        """Асинхронный вызов метода"""
        kwargs['@type'] = method
        return self.client.send_data(kwargs, request_id=request_id)

    def send_data_sync(self, method, request_id=None, **kwargs):
        """Синхронный вызов метода"""
        kwargs['@type'] = method
        return self.client.send_data_sync(kwargs, request_id=request_id)


class AuthAPI(BaseAPI):
    """
    API хелпер, который используется только в момента
    аутентификации клиента в телеграм
    """

    def get_authorization_state(self):
        return self.send_data(
            'getAuthorizationState',
            request_id='getAuthorizationState',
        )

    def set_tdlib_parameters(self):

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
            "use_message_database": self.client.settings.use_message_database,
            "files_directory": os.path.join(
                self.client.settings.files_directory, "files"
            ),
        }
        return self.send_data(
            'setTdlibParameters',
            parameters=parameters,
        )

    def check_database_encryption_key(self):
        return self.send_data(
            'checkDatabaseEncryptionKey',
            encryption_key=self.client.settings.database_encryption_key,
        )

    def set_authentication_phone_number(self):
        phone = self.client.settings.phone

        if not phone:
            raise ValueError('phone not set')

        return self.send_data(
            'setAuthenticationPhoneNumber',
            phone_number=phone,
            allow_flash_call=False,
            is_current_phone_number=True,
        )

    def check_authentication_bot_token(self):
        token = self.client.settings.bot_token

        if not token:
            raise ValueError('token not set')

        return self.send_data(
            'checkAuthenticationBotToken',
            token=token,
        )

    def check_authentication_code(self, auth_code=None):
        """Запрос для проверки кода авторизации"""
        auth_code = self.client.settings.auth_code

        if not auth_code:
            raise ValueError('auth_code not set')

        return self.send_data(
            'checkAuthenticationCode',
            code=auth_code,
        )

    def register_user(self):
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

    def check_authentication_password(self):
        password = self.client.settings.password

        if not password:
            raise ValueError('password not set')

        return self.send_data(
            'checkAuthenticationPassword',
            password=password,
        )


class API(BaseAPI):
    """API хелпер для телеграм клиента"""

    def get_me(self):
        """Запрашивает личные данные клиента"""
        return self.send_data(
            'getMe',
        )

    def get_chat(self, chat_id: int):
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
    ):
        """Запрашивает список чатов"""
        return self.send_data(
            'getChats',
            offset_order=offset_order,
            offset_chat_id=offset_chat_id,
            limit=limit,
        )

    def get_chat_history(
        self,
        chat_id: int,
        limit: int = 1000,
        from_message_id: int = 0,
        offset: int = 0,
        only_local: bool = False,
    ):
        """Запрашивает историю чата"""
        self.send_data(
            'getChatHistory',
            chat_id=chat_id,
            limit=limit,
            from_message_id=from_message_id,
            offset=offset,
            only_local=only_local,
        )

    def get_web_page_instant_view(self, url: str, force_full: bool = False):
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

    def get_user(self, user_id: int):
        """Запрос на получение подробной информации о пользователе. Оффлайн"""
        return self.send_data(
            'getUser',
            user_id=user_id,
        )

    def get_supergroup(self, supergroup_id: int):
        """Запрос на получение информации о супергруппе. Оффлайн"""
        return self.send_data(
            'getSupergroup',
            supergroup_id=supergroup_id,
        )

    def get_supergroup_full_info(self, supergroup_id: int):
        """Запрос на получение полной информации о супергруппе. Кэшируется на 1 минуту"""
        return self.send_data(
            'getSupergroupFullInfo',
            supergroup_id=supergroup_id,
        )

    def get_message(self, message_id: int):
        """Запрос на получение информации о сообщении"""
        return self.send_data(
            'getMessage',
            message_id=message_id,
        )

    def get_callback_query_answer(
        self,
        chat_id: int,
        message_id: int,
        data: str,
        password: str = None,
    ):
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

    def open_chat(self, chat_id: int):
        """Запрос на открытие чата"""
        return self.send_data(
            'openChat',
            chat_id=chat_id,
        )

    def close_chat(self, chat_id: int):
        """Запрос на закрытие чата"""
        return self.send_data(
            'closeChat',
            chat_id=chat_id,
        )

    def close(self):
        """Запрос на закрытие клиента"""
        return self.send_data(
            'close',
        )

    def log_out(self):
        """Запрос на выход из клиента"""
        return self.send_data(
            'logOut',
        )

    def view_messages(self, chat_id: int, message_ids: list):
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
        text: str = None,
        parse_mode: TextParseMode = None,
        disable_web_page_preview: bool = True,
        reply_to_message_id: int = 0,
    ):
        """Sends a message to a chat.
        The chat must be in the tdlib's database.
        If there is no chat in the DB, tdlib returns an error.
        Chat is being saved to the database when the client
        receives a message or when you call the `get_chats` method.
        """
        formatted_text = {'@type': 'formattedText', 'text': text}

        if parse_mode is not None:
            formatted_text = self.parse_text_entities(text, parse_mode)

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
        )

    def parse_text_entities(self, text: str, parse_mode: TextParseMode):
        """Синхронный оффлайн запрос на парсинг текста"""
        return self.send_data_sync(
            'parseTextEntities',
            text=text,
            parse_mode={'@type': parse_mode.value, 'version': 2},
        )

    def resend_messages(self, chat_id: int, message_ids: list):
        """Запрос на переотправку неотправленного сообщения"""
        return self.send_data(
            'resendMessages',
            chat_id=chat_id,
            message_ids=message_ids,
        )

    def delete_messages(self, chat_id, message_ids: list):
        """Запрос на удаление сообщений"""
        return self.send_data(
            'deleteMessages',
            chat_id=chat_id,
            message_ids=message_ids,
            revoke=True,
        )

    def forward_messages(self, chat_id: int, from_chat_id: int, message_ids: list):
        """Запрос на пересылку сообщения из одного чата в другой"""
        return self.send_data(
            'forwardMessages',
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
        )

    def ban_chat_member(self, chat_id: int, user_id: int, banned_until_date: int = 0):
        """Запрос на бан участника чата

        :param chat_id: Чат
        :param user_id: Пользовтаель
        :param banned_until_date: Время бана. 0 - навсегда
        """
        status = {
            '@type': 'chatMemberStatusBanned',
            'banned_until_date': 0,
        }
        return self.send_data(
            'setChatMemberStatus',
            chat_id=chat_id,
            user_id=user_id,
            status=status,
        )

    def join_chat_by_invite_link(self, invite_link: str):
        """Запрос на присоединение к чату через инвайт ссылку"""
        return self.send_data(
            'joinChatByInviteLink',
            invite_link=invite_link,
        )

    def join_chat(self, chat_id: int):
        """Запрос на присоединение к чату через ID"""
        return self.send_data(
            'joinChat',
            chat_id=chat_id,
        )

    def leave_chat(self, chat_id: int):
        """Запрос на покидание чата"""
        return self.send_data(
            'leaveChat',
            chat_id=chat_id,
        )

    def search_public_chat(self, username: str):
        """Запрос на поиск чата по его username"""
        return self.send_data(
            'searchPublicChat',
            username=username,
        )

    def create_private_chat(self, user_id: int):
        """Запрос на создание приватного чата с пользователем"""
        return self.send_data(
            'createPrivateChat',
            user_id=user_id,
        )
