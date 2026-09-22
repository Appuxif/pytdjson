"""MCP server exposing read tools and explicitly allowlisted write tools."""
import asyncio
import json
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
TRANSCRIPTION = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)
LIMIT = Annotated[int, Field(ge=1, le=100)]
HISTORY_LIMIT = Annotated[int, Field(ge=1, le=500)]
PAGE_LIMIT = Annotated[int, Field(ge=1, le=10)]
USER_IDS = Annotated[list[int], Field(min_length=1, max_length=200)]
CHAT_ID = Annotated[int, Field(ne=0)]
CHAT_IDS = Annotated[list[CHAT_ID], Field(min_length=1, max_length=200)]
POLL_TIMEOUT = Annotated[float, Field(gt=0, le=300)]
CURSOR = Annotated[int, Field(ge=0)]
TEXT_CURSOR = Annotated[str, Field(max_length=4096)]
MESSAGE_TEXT = Annotated[str, Field(min_length=1, max_length=4096)]
MESSAGE_ID = Annotated[int, Field(ge=1)]
FILE_ID = Annotated[int, Field(ge=1)]
EVENT_TYPES = Annotated[list[str], Field(min_length=1, max_length=50)]
TOPIC_IDS = Annotated[list[int], Field(min_length=1, max_length=200)]

MESSAGE_FILTERS = {
    'all': None,
    'animation': 'searchMessagesFilterAnimation',
    'audio': 'searchMessagesFilterAudio',
    'document': 'searchMessagesFilterDocument',
    'photo': 'searchMessagesFilterPhoto',
    'poll': 'searchMessagesFilterPoll',
    'video': 'searchMessagesFilterVideo',
    'voice_note': 'searchMessagesFilterVoiceNote',
    'video_note': 'searchMessagesFilterVideoNote',
    'voice_and_video_note': 'searchMessagesFilterVoiceAndVideoNote',
    'photo_and_video': 'searchMessagesFilterPhotoAndVideo',
    'url': 'searchMessagesFilterUrl',
    'mention': 'searchMessagesFilterMention',
    'unread_mention': 'searchMessagesFilterUnreadMention',
    'unread_reaction': 'searchMessagesFilterUnreadReaction',
    'unread_poll_vote': 'searchMessagesFilterUnreadPollVote',
    'failed_to_send': 'searchMessagesFilterFailedToSend',
    'pinned': 'searchMessagesFilterPinned',
}


def _search_filter(value: str | None) -> str | None:
    if value is None or value == 'all':
        return None
    if value in MESSAGE_FILTERS:
        return MESSAGE_FILTERS[value]
    if value.startswith('searchMessagesFilter'):
        return value
    raise ToolError(
        f'unknown message filter {value!r}; use one of '
        + ', '.join(sorted(MESSAGE_FILTERS))
    )


def _chat_cursor(value: str) -> int:
    if not value:
        return 0
    try:
        parsed = json.loads(value)
        if not isinstance(parsed, dict) or not isinstance(
            parsed.get('from_message_id'), int
        ):
            raise ValueError
        return parsed['from_message_id']
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ToolError('invalid chat message search cursor') from error


def _encode_chat_cursor(message_id: int) -> str:
    return json.dumps({'from_message_id': message_id}, separators=(',', ':'))


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

    sender_cache: dict[int, dict] = {}

    async def _sender_details(messages: list[dict]) -> dict[int, dict]:
        user_ids = {
            (item.get('sender_id') or {}).get('user_id')
            for item in messages
            if (item.get('sender_id') or {}).get('user_id') is not None
        }
        missing = [user_id for user_id in user_ids if user_id not in sender_cache]
        if missing:
            users = await asyncio.gather(
                *(runtime.call('get_user', user_id) for user_id in sorted(missing))
            )
            sender_cache.update(
                {
                    user_id: projection.user(user)
                    for user_id, user in zip(sorted(missing), users)
                }
            )
        return {user_id: sender_cache[user_id] for user_id in user_ids}

    async def _project_messages(
        messages: list[dict], include_sender_details: bool
    ) -> list[dict]:
        details = await _sender_details(messages) if include_sender_details else {}
        return [
            projection.message(
                item,
                details.get((item.get('sender_id') or {}).get('user_id')),
            )
            for item in messages
        ]

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

    @mcp.tool(annotations=READ_ONLY)
    async def search_chats(
        query: str,
        limit: LIMIT = 50,
        on_server: bool = False,
    ) -> dict:
        """Find chats by title or username.

        The default search is fast and uses TDLib's local cache. Set
        ``on_server`` for public-chat discovery beyond the local cache.
        """
        result = await runtime.call(
            'search_chats', query=query, limit=limit, on_server=on_server
        )
        chats = await asyncio.gather(
            *(
                runtime.call('get_chat', chat_id)
                for chat_id in result.get('chat_ids', [])
            )
        )
        return {
            'total_count': result.get('total_count'),
            'query': query,
            'on_server': on_server,
            'chats': [
                projection.chat(chat, include_last_message=False) for chat in chats
            ],
        }

    @mcp.tool(annotations=SUBSCRIPTION)
    async def subscribe_for_updates(
        chat_ids: CHAT_IDS,
        event_types: EVENT_TYPES | None = None,
        topic_ids: TOPIC_IDS | None = None,
    ) -> dict:
        """Subscribe to selected live updates from the given chats.

        By default only new messages and completed asynchronous transcription
        results are collected. Event type names are TDLib update constructor
        names, for example ``updateMessageEdited``. Topic IDs filter messages
        to native forum/message topics; an empty topic filter accepts all.
        """
        kwargs = {}
        if event_types is not None:
            kwargs['event_types'] = set(event_types)
        if topic_ids is not None:
            kwargs['topic_ids'] = set(topic_ids)
        return await runtime.subscribe_for_updates(frozenset(chat_ids), **kwargs)

    @mcp.tool(annotations=SUBSCRIPTION)
    async def unsubscribe_from_updates(chat_ids: CHAT_IDS) -> dict:
        """Stop collecting live updates for the given chat IDs."""
        return await runtime.unsubscribe_from_updates(frozenset(chat_ids))

    @mcp.tool(annotations=READ_ONLY)
    async def check_updates_subscription() -> dict:
        """Show active update filters and bounded buffer state."""
        return runtime.update_subscription()

    @mcp.tool(annotations=READ_ONLY)
    async def poll_updates(
        timeout: POLL_TIMEOUT = 30.0,
        limit: LIMIT = 1,
        cursor: CURSOR | None = None,
    ) -> dict:
        """Wait for updates from subscribed chats.

        Raises an error immediately when no chat subscriptions are configured.
        The call returns up to ``limit`` oldest updates or waits until
        ``timeout`` seconds elapse. ``limit`` defaults to one. Pass the
        returned ``next_cursor`` to the next call to continue without
        repeating the updates. Use ``commit_updates`` after processing them.
        Without a cursor, the retained buffer is read from its oldest
        available event.
        """
        if not runtime.update_subscription()['subscribed_chat_ids']:
            raise ToolError(
                'no update subscriptions configured; call '
                'subscribe_for_updates first'
            )
        updates, next_cursor, timed_out, cursor_expired = await runtime.poll_updates(
            timeout, limit, cursor
        )
        state = runtime.update_subscription()
        projected_updates = [projection.update(update) for update in updates]
        dropped_updates = 0
        if cursor is not None and cursor < state['oldest_cursor']:
            dropped_updates = state['oldest_cursor'] - cursor
        has_more = (
            runtime.has_more_updates(next_cursor)
            if hasattr(runtime, 'has_more_updates')
            else False
        )
        return {
            # Keep the singular field for clients written before batching was
            # added. New clients should consume `updates`.
            'update': projected_updates[0] if len(projected_updates) == 1 else None,
            'updates': projected_updates,
            'timed_out': timed_out,
            'cursor_expired': cursor_expired,
            'dropped_updates': dropped_updates,
            'has_more': has_more,
            'next_cursor': next_cursor,
            'subscribed_chat_ids': state['subscribed_chat_ids'],
            'subscriptions': state.get('subscriptions', []),
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
        include_sender_details: bool = False,
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
        return {
            **projection.history(
                result,
                await _sender_details(result.get('messages') or [])
                if include_sender_details
                else None,
            ),
            'oldest_message_id': min(
                (item.get('id') for item in (result.get('messages') or [])),
                default=0,
            ),
        }

    @mcp.tool(annotations=READ_ONLY)
    async def get_chat_history_complete(
        chat_id: int,
        limit: HISTORY_LIMIT = 100,
        max_pages: PAGE_LIMIT = 5,
        only_local: bool = False,
        include_sender_details: bool = True,
    ) -> dict:
        """Read up to ``limit`` recent messages with automatic pagination.

        TDLib can return short pages while it fills a local history gap. This
        helper retries and advances through older messages until the requested
        amount is available, the history ends, or ``max_pages`` is reached.
        """
        messages_by_id: dict[int, dict] = {}
        from_message_id = 0
        pages_fetched = 0
        stalled = False
        while len(messages_by_id) < limit and pages_fetched < max_pages:
            page_limit = min(100, limit - len(messages_by_id))
            result = await runtime.call(
                'get_chat_history',
                chat_id,
                limit=page_limit,
                from_message_id=from_message_id,
                offset=0,
                only_local=only_local,
            )
            pages_fetched += 1
            page = result.get('messages') or []
            before_count = len(messages_by_id)
            for item in page:
                if item.get('id') is not None:
                    messages_by_id[item['id']] = item
            if not page:
                break
            oldest_message_id = min(
                (item.get('id') for item in page if item.get('id') is not None),
                default=0,
            )
            if not oldest_message_id or (
                len(messages_by_id) == before_count
                and oldest_message_id == from_message_id
            ):
                stalled = True
                break
            from_message_id = oldest_message_id
        messages = sorted(
            messages_by_id.values(), key=lambda item: item.get('id', 0), reverse=True
        )[:limit]
        return {
            'total_count': result.get('total_count') if 'result' in locals() else 0,
            'messages': await _project_messages(messages, include_sender_details),
            'oldest_message_id': min((item.get('id') for item in messages), default=0),
            'pages_fetched': pages_fetched,
            'complete': len(messages) >= limit or not messages or stalled,
            'max_pages_reached': pages_fetched >= max_pages
            and len(messages) < limit
            and not stalled,
        }

    @mcp.tool(annotations=READ_ONLY)
    async def search_messages(
        query: str,
        chat_id: int | None = None,
        sender_id: int | None = None,
        topic_id: int | None = None,
        min_date: int = 0,
        max_date: int = 0,
        limit: LIMIT = 100,
        cursor: TEXT_CURSOR = '',
        chat_list: str | None = 'chatListMain',
        filter: str = 'all',
        include_sender_details: bool = True,
    ) -> dict:
        """Search text and media messages in one chat or across all chats.

        Pass the returned ``next_cursor`` unchanged to continue. Chat-scoped
        cursors are opaque JSON values; global cursors are supplied by TDLib.
        ``topic_id`` is a native forum topic ID when ``chat_id`` is set.
        """
        filter_type = _search_filter(filter)
        if chat_id is not None:
            result = await runtime.call(
                'search_chat_messages',
                chat_id,
                query=query,
                topic_id=topic_id,
                sender_id=sender_id,
                from_message_id=_chat_cursor(cursor),
                offset=0,
                limit=limit,
                filter_type=filter_type,
            )
            next_from_message_id = result.get('next_from_message_id', 0)
            next_cursor = (
                _encode_chat_cursor(next_from_message_id)
                if next_from_message_id
                else ''
            )
        else:
            result = await runtime.call(
                'search_messages',
                query=query,
                offset=cursor,
                limit=limit,
                chat_list=chat_list,
                filter_type=filter_type,
                min_date=min_date,
                max_date=max_date,
            )
            next_cursor = result.get('next_offset', '')
        details = (
            await _sender_details(result.get('messages') or [])
            if include_sender_details
            else {}
        )
        return {
            'query': query,
            'chat_id': chat_id,
            'total_count': result.get('total_count'),
            'messages': [
                projection.message(
                    item,
                    details.get((item.get('sender_id') or {}).get('user_id')),
                )
                for item in (result.get('messages') or [])
            ],
            'next_cursor': next_cursor,
            'has_more': bool(next_cursor),
        }

    @mcp.tool(annotations=READ_ONLY)
    async def get_conversation_context(
        chat_id: int,
        message_id: MESSAGE_ID,
        before: Annotated[int, Field(ge=0, le=50)] = 10,
        after: Annotated[int, Field(ge=0, le=50)] = 10,
        include_sender_details: bool = True,
    ) -> dict:
        """Return a message with nearby messages and thread metadata."""
        target = await runtime.call('get_message', message_id, chat_id)
        target_topic = target.get('topic_id') or {}
        forum_topic_id = target_topic.get('forum_topic_id')
        history_method = (
            'get_forum_topic_history'
            if forum_topic_id is not None
            else 'get_chat_history'
        )
        if forum_topic_id is not None:
            history_args = (chat_id, forum_topic_id)
            history_kwargs = {}
        else:
            history_args = (chat_id,)
            history_kwargs = {'only_local': False}
        requests = [
            runtime.call(
                history_method,
                *history_args,
                limit=before + 1,
                from_message_id=message_id,
                offset=0,
                **history_kwargs,
            )
        ]
        if after:
            requests.append(
                runtime.call(
                    history_method,
                    *history_args,
                    limit=after + 1,
                    from_message_id=message_id,
                    offset=-after,
                    **history_kwargs,
                )
            )
        pages = await asyncio.gather(*requests)
        messages_by_id = {message_id: target}
        for page in pages:
            for item in page.get('messages') or []:
                if item.get('id') is not None:
                    item_topic = item.get('topic_id') or {}
                    if forum_topic_id is not None and (
                        item_topic.get('forum_topic_id') != forum_topic_id
                    ):
                        continue
                    messages_by_id[item['id']] = item
        messages = sorted(messages_by_id.values(), key=lambda item: item.get('id', 0))
        center_index = next(
            (
                index
                for index, item in enumerate(messages)
                if item.get('id') == message_id
            ),
            0,
        )
        window_start = max(0, center_index - before)
        window_end = min(len(messages), center_index + after + 1)
        messages = messages[window_start:window_end]
        details = await _sender_details(messages) if include_sender_details else {}
        projected = [
            projection.message(
                item,
                details.get((item.get('sender_id') or {}).get('user_id')),
            )
            for item in messages
        ]
        target_index = next(
            (index for index, item in enumerate(projected) if item['id'] == message_id),
            0,
        )
        target_projection = projected[target_index]
        return {
            'chat_id': chat_id,
            'message_id': message_id,
            'message': target_projection,
            'messages': projected,
            'target_index': target_index,
            'before_count': target_index,
            'after_count': len(projected) - target_index - 1,
            'topic_id': target_projection.get('topic_id'),
            'reply_to': target_projection.get('reply_to'),
        }

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

    @mcp.tool(annotations=READ_ONLY)
    async def get_file(file_id: FILE_ID) -> dict:
        """Get local and remote metadata for a Telegram file."""
        return projection.file(await runtime.call('get_file', file_id))

    @mcp.tool(annotations=READ_ONLY)
    async def download_file(
        file_id: FILE_ID,
        priority: Annotated[int, Field(ge=1, le=32)] = 16,
        offset: Annotated[int, Field(ge=0)] = 0,
        limit: Annotated[int, Field(ge=0)] = 0,
        synchronous: bool = False,
    ) -> dict:
        """Start a media download and return its current local path/state.

        With ``synchronous=true`` TDLib waits for completion, which can take a
        long time. The default starts the download and lets the local file
        state be checked with ``get_file``.
        """
        result = await runtime.call(
            'download_file',
            file_id,
            priority=priority,
            offset=offset,
            limit=limit,
            synchronous=synchronous,
        )
        return projection.file(result)

    @mcp.tool(annotations=TRANSCRIPTION)
    async def request_message_transcript(chat_id: int, message_id: MESSAGE_ID) -> dict:
        """Start asynchronous speech recognition for a voice or video note.

        The request returns immediately. Subscribe to the chat and keep
        polling for a ``message_transcription`` update containing the final
        transcript or an error.
        """
        try:
            result = await runtime.request_message_transcript(chat_id, message_id)
        except ValueError as error:
            raise ToolError(str(error)) from error
        return projection.transcription_request(result)

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
