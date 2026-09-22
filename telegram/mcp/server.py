"""MCP server exposing read tools and explicitly allowlisted write tools."""
import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from telegram.client import Settings
from telegram.mcp import projection
from telegram.mcp.runtime import TelegramRuntime

READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True)
SEND = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)
SUBSCRIPTION = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
)
LIMIT = Annotated[int, Field(ge=1, le=100)]
USER_IDS = Annotated[list[int], Field(min_length=1, max_length=200)]
CHAT_ID = Annotated[int, Field(ne=0)]
CHAT_IDS = Annotated[list[CHAT_ID], Field(min_length=1, max_length=200)]
POLL_TIMEOUT = Annotated[float, Field(gt=0, le=300)]
CURSOR = Annotated[int, Field(ge=0)]
MESSAGE_TEXT = Annotated[str, Field(min_length=1, max_length=4096)]
MESSAGE_ID = Annotated[int, Field(ge=1)]


def create_server(
    settings: Settings, runtime: TelegramRuntime | None = None
) -> MCPServer:
    """Create the stdio server. TDLib starts only when its lifespan begins."""
    runtime = runtime or TelegramRuntime(settings)

    @asynccontextmanager
    async def lifespan(_: MCPServer):
        await runtime.start()
        try:
            yield runtime
        finally:
            await runtime.stop()

    mcp = MCPServer(
        'pytdjson-mcp',
        title='PyTDJson',
        description=(
            'Telegram data and allowlisted message sending through a local TDLib session.'
        ),
        lifespan=lifespan,
    )

    @mcp.tool(annotations=READ_ONLY)
    async def get_me() -> dict:
        """Get the authenticated Telegram account."""
        return projection.user(await runtime.call('get_me'))

    @mcp.tool(annotations=READ_ONLY)
    async def get_user(user_id: int) -> dict:
        """Get a Telegram user by numeric ID."""
        return projection.user(await runtime.call('get_user', user_id))

    @mcp.tool(annotations=READ_ONLY)
    async def get_users(user_ids: USER_IDS) -> dict:
        """Get multiple Telegram users in one MCP call.

        Duplicate IDs are removed while preserving the input order. TDLib
        exposes only getUser, so the individual lookups are performed in
        parallel behind this batch tool.
        """
        unique_user_ids = list(dict.fromkeys(user_ids))
        users = await asyncio.gather(
            *(runtime.call('get_user', user_id) for user_id in unique_user_ids)
        )
        return {
            'total_count': len(users),
            'users': [projection.user(user) for user in users],
        }

    @mcp.tool(annotations=READ_ONLY)
    async def get_chat(chat_id: int) -> dict:
        """Get a cached Telegram chat by numeric ID."""
        return projection.chat(await runtime.call('get_chat', chat_id))

    @mcp.tool(annotations=READ_ONLY)
    async def get_chats(limit: LIMIT = 100, chat_list: str = 'chatListMain') -> dict:
        """List compact cached chat objects from a Telegram chat list."""
        result = await runtime.call('get_chats', limit=limit, chat_list=chat_list)
        chats = await asyncio.gather(
            *(
                runtime.call('get_chat', chat_id)
                for chat_id in result.get('chat_ids', [])
            )
        )
        return {
            'total_count': result.get('total_count'),
            'chats': [
                projection.chat(chat, include_last_message=False) for chat in chats
            ],
        }

    @mcp.tool(annotations=READ_ONLY)
    async def load_chats(limit: LIMIT = 10, chat_list: str = 'chatListMain') -> dict:
        """Ask TDLib to load chats into its local cache."""
        await runtime.call('load_chats', limit=limit, chat_list=chat_list)
        return {'loaded': True}

    @mcp.tool(annotations=SUBSCRIPTION)
    async def subscribe_for_updates(chat_ids: CHAT_IDS) -> dict:
        """Subscribe to live updates associated with the given chat IDs."""
        return await runtime.subscribe_for_updates(frozenset(chat_ids))

    @mcp.tool(annotations=SUBSCRIPTION)
    async def unsubscribe_from_updates(chat_ids: CHAT_IDS) -> dict:
        """Stop collecting live updates for the given chat IDs."""
        return await runtime.unsubscribe_from_updates(frozenset(chat_ids))

    @mcp.tool(annotations=READ_ONLY)
    async def check_updates_subscription() -> dict:
        """Show active update subscriptions and bounded buffer state."""
        return runtime.update_subscription()

    @mcp.tool(annotations=READ_ONLY)
    async def poll_updates(
        timeout: POLL_TIMEOUT = 30.0,
        cursor: CURSOR | None = None,
    ) -> dict:
        """Wait for updates from subscribed chats.

        Raises an error immediately when no chat subscriptions are configured.
        The call returns one oldest update or waits until ``timeout`` seconds
        elapse. Pass the returned ``next_cursor`` to the next call to continue
        without repeating the update. Use ``commit_updates`` after processing
        it. Without a cursor, the retained buffer is read from its oldest
        available event.
        """
        if not runtime.update_subscription()['subscribed_chat_ids']:
            raise ToolError(
                'no update subscriptions configured; call '
                'subscribe_for_updates first'
            )
        update, next_cursor, timed_out, cursor_expired = await runtime.poll_updates(
            timeout, cursor
        )
        state = runtime.update_subscription()
        return {
            'update': projection.update(update),
            'timed_out': timed_out,
            'cursor_expired': cursor_expired,
            'next_cursor': next_cursor,
            'subscribed_chat_ids': state['subscribed_chat_ids'],
        }

    @mcp.tool(annotations=SUBSCRIPTION)
    async def commit_updates(cursor: CURSOR) -> dict:
        """Remove all buffered updates through a processed cursor."""
        try:
            return await runtime.commit_updates(cursor)
        except ValueError as error:
            raise ToolError(str(error)) from error

    @mcp.tool(annotations=READ_ONLY)
    async def get_chat_history(
        chat_id: int,
        limit: LIMIT = 100,
        from_message_id: int = 0,
        offset: int = 0,
        only_local: bool = False,
    ) -> dict:
        """Get a compact page of messages from one chat.

        TDLib can return fewer than ``limit`` messages while it loads a history
        gap. Start with ``from_message_id=0``. For the next page, set
        ``from_message_id`` to the oldest message ID returned, with
        ``offset=0`` and ``only_local=false``. Repeat the same request when a
        short page appears to be loading a gap.
        """
        result = await runtime.call(
            'get_chat_history',
            chat_id,
            limit=limit,
            from_message_id=from_message_id,
            offset=offset,
            only_local=only_local,
        )
        return projection.history(result)

    @mcp.tool(annotations=READ_ONLY)
    async def get_forum_topics(
        chat_id: int,
        query: str = '',
        offset_date: int = 0,
        offset_message_id: int = 0,
        offset_forum_topic_id: int = 0,
        limit: LIMIT = 100,
    ) -> dict:
        """List native forum topics in a forum supergroup.

        Use the returned ``next_offset`` values for the next page. Pass the
        topic name in ``query`` to filter the list on Telegram's server.
        """
        result = await runtime.call(
            'get_forum_topics',
            chat_id,
            query=query,
            offset_date=offset_date,
            offset_message_id=offset_message_id,
            offset_forum_topic_id=offset_forum_topic_id,
            limit=limit,
        )
        return projection.forum_topics(result)

    @mcp.tool(annotations=READ_ONLY)
    async def get_forum_topic(chat_id: int, forum_topic_id: int) -> dict:
        """Get metadata and the latest message for one forum topic."""
        return projection.forum_topic(
            await runtime.call('get_forum_topic', chat_id, forum_topic_id)
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_forum_topic_history(
        chat_id: int,
        forum_topic_id: int,
        limit: LIMIT = 100,
        from_message_id: int = 0,
        offset: int = 0,
    ) -> dict:
        """Get messages from one forum topic.

        Results are newest-first. Start with ``from_message_id=0``. For the
        next page, pass the oldest returned message ID with ``offset=0``.
        Repeat the same request if Telegram returns a short page while it
        loads history.
        """
        result = await runtime.call(
            'get_forum_topic_history',
            chat_id,
            forum_topic_id,
            limit=limit,
            from_message_id=from_message_id,
            offset=offset,
        )
        return projection.history(result)

    @mcp.tool(annotations=READ_ONLY)
    async def get_message_thread(chat_id: int, message_id: int) -> dict:
        """Get metadata and starting messages for a message reply thread."""
        return projection.message_thread(
            await runtime.call('get_message_thread', chat_id, message_id)
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_message_thread_history(
        chat_id: int,
        message_id: int,
        limit: LIMIT = 100,
        from_message_id: int = 0,
        offset: int = 0,
    ) -> dict:
        """Get messages replying to one message.

        Results are newest-first. Start with ``from_message_id=0``. For the
        next page, pass the oldest returned message ID with ``offset=0``.
        """
        result = await runtime.call(
            'get_message_thread_history',
            chat_id,
            message_id,
            limit=limit,
            from_message_id=from_message_id,
            offset=offset,
        )
        return projection.history(result)

    @mcp.tool(annotations=READ_ONLY)
    async def get_message(chat_id: int, message_id: int) -> dict:
        """Get one message by chat and message ID."""
        return projection.message(
            await runtime.call('get_message', message_id, chat_id)
        )

    @mcp.tool(annotations=SEND)
    async def send_message(
        chat_id: int,
        text: MESSAGE_TEXT,
        message_thread_id: MESSAGE_ID | None = None,
        forum_topic_id: MESSAGE_ID | None = None,
        reply_to_message_id: MESSAGE_ID | None = None,
    ) -> dict:
        """Send a text message to an explicitly allowlisted chat.

        Sending is disabled unless ``PYTDJSON_ALLOW_SEND_TO_CHATS`` contains
        the chat ID or is set to ``*``. Use ``message_thread_id`` for a
        non-forum reply thread and ``forum_topic_id`` for a forum topic.
        """
        if not text.strip():
            raise ToolError('text must contain a non-whitespace character')
        if (
            not settings.mcp_allow_send_to_all_chats
            and chat_id not in settings.mcp_allowed_send_to_chats
        ):
            raise ToolError(
                f'sending messages to chat {chat_id} is not allowed; '
                'configure PYTDJSON_ALLOW_SEND_TO_CHATS'
            )
        if message_thread_id is not None and forum_topic_id is not None:
            raise ToolError(
                'message_thread_id and forum_topic_id cannot be used together'
            )
        return projection.message(
            await runtime.send_message(
                chat_id,
                text=text,
                message_thread_id=message_thread_id,
                forum_topic_id=forum_topic_id,
                reply_to_message_id=reply_to_message_id,
            )
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_message_link(
        chat_id: int, message_id: int, in_message_thread: bool = False
    ) -> dict:
        """Get a shareable link for a message."""
        result = await runtime.call(
            'get_message_link', chat_id, message_id, in_message_thread
        )
        return {'link': result.get('link'), 'is_public': result.get('is_public')}

    @mcp.tool(annotations=READ_ONLY)
    async def get_supergroup(supergroup_id: int) -> dict:
        """Get a supergroup or channel by numeric ID."""
        return projection.group(await runtime.call('get_supergroup', supergroup_id))

    @mcp.tool(annotations=READ_ONLY)
    async def get_supergroup_full_info(supergroup_id: int) -> dict:
        """Get compact extended information for a supergroup or channel."""
        return projection.group(
            await runtime.call('get_supergroup_full_info', supergroup_id)
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_basic_group(basic_group_id: int) -> dict:
        """Get a basic group by numeric ID."""
        return projection.group(await runtime.call('get_basic_group', basic_group_id))

    @mcp.tool(annotations=READ_ONLY)
    async def get_basic_group_full_info(basic_group_id: int) -> dict:
        """Get compact extended information for a basic group."""
        return projection.group(
            await runtime.call('get_basic_group_full_info', basic_group_id)
        )

    @mcp.tool(annotations=READ_ONLY)
    async def search_public_chat(username: str) -> dict:
        """Find a public chat by username, without the leading @."""
        return projection.chat(await runtime.call('search_public_chat', username))

    @mcp.tool(annotations=READ_ONLY)
    async def get_storage_statistics(chat_limit: LIMIT = 10) -> dict:
        """Get compact local TDLib storage statistics."""
        return projection.statistics(
            await runtime.call('get_storage_statistics', chat_limit)
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_database_statistics() -> dict:
        """Get compact local TDLib database statistics."""
        return projection.statistics(await runtime.call('get_database_statistics'))

    return mcp
