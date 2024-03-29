import os
from typing import TYPE_CHECKING, List, Optional, Union

from .types.message import ReactionType
from .types.supergroup import SupergroupMembersFilter
from .types.text import TextParseMode

if TYPE_CHECKING:
    from .client import AsyncTelegram


class BaseAPI:
    """Базовый класс API хелпера для телеграм клиента"""

    def __init__(self, client: 'AsyncTelegram', timeout=30):
        self.client = client
        self.timeout = timeout

    def send_data(self, method, request_id=None, timeout=None, **kwargs):
        """Асинхронный вызов метода"""
        timeout = timeout or self.timeout
        kwargs['@type'] = method
        return self.client.send_data(kwargs, request_id=request_id, timeout=timeout)

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
            "database_directory": os.path.join(
                self.client.settings.files_directory, "database"
            ),
            "files_directory": os.path.join(
                self.client.settings.files_directory, "files"
            ),
            'database_encryption_key': self.client.settings.database_encryption_key,
            "use_file_database": self.client.settings.use_file_database,
            "use_chat_info_database": self.client.settings.use_chat_info_database,
            "use_message_database": self.client.settings.use_message_database,
            # 'use_secret_chats': False,
            "api_id": self.client.settings.api_id,
            "api_hash": self.client.settings.api_hash,
            "system_language_code": self.client.settings.system_language_code,
            "device_model": self.client.settings.device_model,
            "system_version": self.client.settings.system_version,
            "application_version": self.client.settings.application_version,
            # "enable_storage_optimizer": self.client.settings.enable_storage_optimizer,  # deleted in 1.8.26
            # 'ignore_file_names': False,
        }
        return self.send_data(
            'setTdlibParameters',
            **parameters,
        )

    def set_authentication_phone_number(self):
        phone = self.client.settings.phone

        if not phone:
            raise ValueError('phone not set')

        return self.send_data(
            'setAuthenticationPhoneNumber',
            phone_number=phone,
            settings={
                'allow_flash_call': False,
                'allow_missed_call': False,
                'is_current_phone_number': True,
            },
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
            disable_notification=True,
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
        # Для обратной совместимости
        offset_order: int = 0,
        offset_chat_id: int = 0,
        limit: int = 100,
        chat_list: str = 'chatListMain',
    ):
        """Запрашивает список чатов"""
        return self.send_data(
            'getChats',
            limit=limit,
            chat_list=chat_list,
        )

    def load_chats(self, limit: int = 10, chat_list: str = 'chatListMain'):
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
    ):
        """Запрашивает историю чата"""
        self.send_data(
            'getChatHistory',
            chat_id=chat_id,
            from_message_id=from_message_id,
            offset=offset,
            limit=limit,
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

    def get_supergroup_members(
        self,
        supergroup_id: int,
        filter_type: SupergroupMembersFilter,
        offset: int = 0,
        limit: int = 200,
        query: str = '',
        message_thread_id: int = None,
    ):
        """Запрос на получение списка пользователей супергруппы.

        query используется не во всех фильтрах.
        message_thread_id только в SupergroupMembersFilter.MENTION.
        """
        filter_type = SupergroupMembersFilter(filter_type)
        limit = min(limit, 200)

        filter_body = {'@type': filter_type.value}
        if query and filter_type in SupergroupMembersFilter.with_query():
            filter_body['query'] = query
        if message_thread_id and filter_type in SupergroupMembersFilter.with_thread():
            filter_body['message_thread_id'] = message_thread_id

        return self.send_data(
            'getSupergroupMembers',
            supergroup_id=supergroup_id,
            filter=filter_body,
            offset=offset,
            limit=limit,
        )

    def get_basic_group(self, basic_group_id: int):
        """Запрос на получение информации о базовой группе. Оффлайн метод"""
        return self.send_data(
            'getBasicGroup',
            basic_group_id=basic_group_id,
        )

    def get_basic_group_full_info(self, basic_group_id: int):
        """Запрос на получение полной информации о базовой группе"""
        return self.send_data(
            'getBasicGroupFullInfo',
            basic_group_id=basic_group_id,
        )

    def get_message(self, message_id: int, chat_id: int):
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

    def view_messages(
        self,
        chat_id: int,
        message_ids: list,
        source: Optional[str] = None,
        force_read: bool = False,
    ):
        """Запрос на просмотр сообщений. Все непрочитанные сообщения
        в чате с указанным ID окажутся прочитанными
        """
        return self.send_data(
            'viewMessages',
            chat_id=chat_id,
            message_ids=message_ids,
            source=source,
            force_read=force_read,
        )

    def send_message(
        self,
        chat_id: int,
        text: str = None,
        parse_mode: TextParseMode = None,
        disable_web_page_preview: bool = True,
        reply_to_message_id: int = 0,
        disable_notification: bool = None,
        from_background: bool = None,
        send_date: int = None,
        message_thread_id: int = 0,
    ):
        """Sends a message to a chat.
        The chat must be in the tdlib's database.
        If there is no chat in the DB, tdlib returns an error.
        Chat is being saved to the database when the client
        receives a message or when you call the `get_chats` method.
        """
        formatted_text = {'@type': 'formattedText', 'text': text}

        if parse_mode is not None and parse_mode is not TextParseMode.NONE:
            result = self.parse_text_entities(text, parse_mode)
            result.is_valid()
            formatted_text = result.update

        input_message_content = {
            '@type': 'inputMessageText',
            'text': formatted_text,
            'disable_web_page_preview': {
                '@type': 'linkPreviewOptions',
                'is_disabled': disable_web_page_preview,
            },
            'clear_draft': True,
        }

        return self.send_data(
            'sendMessage',
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            reply_to={
                '@type': 'InputMessageReplyToMessage',
                'chat_id': 0,  # pass 0 if the message to be replied is in the same chat
                'message_id': reply_to_message_id,
                'quote': None,
            },
            input_message_content=input_message_content,
            options=_get_send_message_options(
                disable_notification,
                from_background,
                send_date,
            ),
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
            quote=None,
        )

    def delete_messages(self, chat_id, message_ids: list):
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
        message_ids: list,
        disable_notification: bool = None,
        from_background: bool = None,
        send_date: int = None,
        message_thread_id: int = 0,
        send_copy: bool = False,
        remove_caption: bool = False,
        only_preview: bool = False,  # deprecated  # noqa
    ):
        """Запрос на пересылку сообщения из одного чата в другой"""
        return self.send_data(
            'forwardMessages',
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
            options=_get_send_message_options(
                disable_notification,
                from_background,
                send_date,
            ),
            send_copy=send_copy,
            remove_caption=remove_caption,
        )

    def ban_chat_member(self, chat_id: int, user_id: int, banned_until_date: int = 0):
        """Запрос на бан участника чата

        :param chat_id: Чат
        :param user_id: Пользовтаель
        :param banned_until_date: Время бана. 0 - навсегда
        """
        status = {
            '@type': 'chatMemberStatusBanned',
            'banned_until_date': banned_until_date,
        }
        return self.send_data(
            'setChatMemberStatus',
            chat_id=chat_id,
            member_id={'@type': 'messageSenderUser', 'user_id': user_id},
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

    def create_private_chat(self, user_id: int, force: bool = False):
        """Запрос на создание приватного чата с пользователем"""
        return self.send_data(
            'createPrivateChat',
            user_id=user_id,
            force=force,
        )

    def get_message_link(
        self, chat_id: int, message_id: int, in_message_thread: bool = False
    ):
        """Запрос на генерацию ссылки для сообщения. Работает только для супергрупп"""
        return self.send_data(
            'getMessageLink',
            chat_id=chat_id,
            message_id=message_id,
            in_message_thread=in_message_thread,
        )

    def add_chat_member(self, chat_id: int, user_id: int, forward_limit: int = 100):
        """Запрос на добавление пользователя в чат.
        forward_limit должен быть не больше 100.
        """
        forward_limit = min(forward_limit, 100)
        return self.send_data(
            'addChatMember',
            chat_id=chat_id,
            user_id=user_id,
            forward_limit=forward_limit,
        )

    def add_chat_members(self, chat_id: int, user_ids: List[int]):
        """Запрос на добавление пользователей в чат.
        Не более 20 пользователей за раз. Остальные игнорируются.
        """
        return self.send_data(
            'addChatMembers',
            chat_id=chat_id,
            user_ids=user_ids,
        )

    def get_message_available_reactions(
        self, chat_id: int, message_id: int, row_size: int = 25
    ):
        """Запрос на доступные реакции к сообщению"""
        row_size = min(max(row_size, 5), 25)
        return self.send_data(
            'getMessageAvailableReactions',
            chat_id=chat_id,
            message_id=message_id,
            row_size=row_size,
        )

    def add_message_reaction(
        self,
        chat_id: int,
        message_id: int,
        reaction_type: ReactionType,
        value: Union[str, int],
        is_big: bool = False,
        update_recent_reactions: bool = False,
    ):
        """Запрос на добавление реакции к сообщению"""
        reaction_type = ReactionType(reaction_type)
        return self.send_data(
            'addMessageReaction',
            chat_id=chat_id,
            message_id=message_id,
            reaction_type=reaction_type.build(value),
            is_big=is_big,
            update_recent_reactions=update_recent_reactions,
        )

    def remove_message_reaction(
        self,
        chat_id: int,
        message_id: int,
        reaction_type: ReactionType,
        value: Union[str, int],
    ):
        """Запрос на удаление реакции к сообщению"""
        reaction_type = ReactionType(reaction_type)
        return self.send_data(
            'removeMessageReaction',
            chat_id=chat_id,
            message_id=message_id,
            reaction_type=reaction_type.build(value),
        )

    def get_message_added_reactions(
        self,
        chat_id: int,
        message_id: int,
        reaction_type: Optional[ReactionType] = None,
        value: Union[str, int] = '',
        offset: int = 0,
        limit: int = 100,
    ):
        """Запрос на информацию о добавленных реакциях к сообщению"""
        limit = min(limit, 100)
        if reaction_type is not None:
            reaction_type = ReactionType(reaction_type).build(value)
        return self.send_data(
            'getMessageAddedReactions',
            chat_id=chat_id,
            message_id=message_id,
            reaction_type=reaction_type,
            limit=limit,
            offset=offset,
        )

    def get_storage_statistics(self, chat_limit: int = 10):
        return self.send_data('getStorageStatistics', chat_limit=chat_limit)

    def get_database_statistics(self):
        return self.send_data('getDatabaseStatistics')

    def optimize_storage(
        self,
        size: int = -1,
        ttl: int = -1,
        count: int = -1,
        immunity_delay: int = -1,
        file_types: Optional[list] = None,
        chat_ids: Optional[list] = None,
        exclude_chat_ids: Optional[list] = None,
        return_deleted_file_statistics: bool = False,
        chat_limit: int = 10,
    ):
        file_types = file_types or []
        chat_ids = chat_ids or []
        exclude_chat_ids = exclude_chat_ids or []
        return self.send_data(
            'optimizeStorage',
            size=size,
            ttl=ttl,
            count=count,
            immunity_delay=immunity_delay,
            file_types=file_types,
            chat_ids=chat_ids,
            exclude_chat_ids=exclude_chat_ids,
            return_deleted_file_statistics=return_deleted_file_statistics,
            chat_limit=chat_limit,
        )


def _get_send_message_options(
    disable_notification: bool = None,
    from_background: bool = None,
    send_date: int = None,
):
    """Собирает дополнительные параметры для отправки сообщения"""
    options = {}
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
