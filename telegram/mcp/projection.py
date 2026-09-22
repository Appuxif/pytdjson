"""Compact, stable MCP responses derived from TDLib JSON."""
from typing import Optional


def _sender(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {'type': value.get('@type')}
    result.update({key: value[key] for key in ('user_id', 'chat_id') if key in value})
    return result


def _topic_id(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {'type': value.get('@type')}
    result.update(
        {
            key: value[key]
            for key in (
                'message_thread_id',
                'forum_topic_id',
                'direct_messages_chat_topic_id',
                'saved_messages_topic_id',
            )
            if key in value
        }
    )
    return result


def _reply_to(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {'type': value.get('@type')}
    result.update(
        {
            key: value[key]
            for key in ('chat_id', 'message_id', 'story_poster_chat_id', 'story_id')
            if key in value
        }
    )
    return result


def message(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    content = value.get('content') or {}
    text = content.get('text') or content.get('caption') or {}
    sticker = content.get('sticker') or {}
    sticker_emoji = sticker.get('emoji')
    text_value = text.get('text') if isinstance(text, dict) else None
    if content.get('@type') == 'messageSticker' and text_value is None:
        text_value = sticker_emoji
    return {
        'id': value.get('id'),
        'chat_id': value.get('chat_id'),
        'sender': _sender(value.get('sender_id') or value.get('sender')),
        'date': value.get('date'),
        'edit_date': value.get('edit_date'),
        'is_outgoing': value.get('is_outgoing'),
        'topic_id': _topic_id(value.get('topic_id')),
        'reply_to': _reply_to(value.get('reply_to')),
        'content_type': content.get('@type'),
        'text': text_value,
        'sticker_emoji': sticker_emoji,
        'sticker_id': sticker.get('id'),
        'sticker_set_id': sticker.get('set_id'),
        'sticker_is_premium': content.get('is_premium'),
    }


def _update_chat_id(value: dict) -> Optional[int]:
    if value.get('chat_id') is not None:
        return value['chat_id']
    for key in ('message', 'chat'):
        nested = value.get(key) or {}
        if key == 'message' and nested.get('chat_id') is not None:
            return nested['chat_id']
        if key == 'chat' and nested.get('id') is not None:
            return nested['id']
    return None


def update(value: Optional[dict]) -> Optional[dict]:
    """Project a TDLib update into a compact event for MCP clients."""
    if not value:
        return None

    result = {
        'type': value.get('@type'),
        'chat_id': _update_chat_id(value),
    }
    for key in (
        'date',
        'message_id',
        'message_ids',
        'user_id',
        'supergroup_id',
        'basic_group_id',
        'unread_count',
        'last_read_inbox_message_id',
        'last_read_outbox_message_id',
        'is_deleted',
        'is_pinned',
    ):
        if key in value:
            result[key] = value[key]

    if 'message' in value:
        result['message'] = message(value['message'])
    if 'chat' in value:
        result['chat'] = chat(value['chat'], include_last_message=False)
    if 'error' in value:
        error = value['error'] or {}
        result['error'] = {
            key: error[key] for key in ('code', 'message') if key in error
        }
    return result


def user(value: dict) -> dict:
    usernames = value.get('usernames') or {}
    return {
        'id': value.get('id'),
        'first_name': value.get('first_name'),
        'last_name': value.get('last_name'),
        'username': usernames.get('editable_username')
        or (usernames.get('active_usernames') or [None])[0],
        'is_premium': value.get('is_premium'),
        'is_contact': value.get('is_contact'),
        'type': (value.get('type') or {}).get('@type'),
    }


def chat(value: dict, include_last_message: bool = True) -> dict:
    chat_type = value.get('type') or {}
    result = {
        'id': value.get('id'),
        'title': value.get('title'),
        'type': chat_type.get('@type'),
        'is_channel': chat_type.get('is_channel'),
        'unread_count': value.get('unread_count'),
    }
    if include_last_message:
        result['last_message'] = message(value.get('last_message'))
    return result


def group(value: dict) -> dict:
    return {
        key: value.get(key)
        for key in ('id', 'member_count', 'description', 'is_channel', 'is_forum')
        if key in value
    }


def forum_topic_info(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    icon = value.get('icon') or {}
    return {
        'chat_id': value.get('chat_id'),
        'forum_topic_id': value.get('forum_topic_id'),
        'name': value.get('name'),
        'icon': {
            'color': icon.get('color'),
            'custom_emoji_id': icon.get('custom_emoji_id'),
        },
        'creation_date': value.get('creation_date'),
        'creator': _sender(value.get('creator_id')),
        'is_general': value.get('is_general'),
        'is_outgoing': value.get('is_outgoing'),
        'is_closed': value.get('is_closed'),
        'is_hidden': value.get('is_hidden'),
        'is_name_implicit': value.get('is_name_implicit'),
    }


def forum_topic(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = forum_topic_info(value.get('info')) or {}
    result.update(
        {
            'last_message': message(value.get('last_message')),
            'order': value.get('order'),
            'is_pinned': value.get('is_pinned'),
            'unread_count': value.get('unread_count'),
            'last_read_inbox_message_id': value.get('last_read_inbox_message_id'),
            'last_read_outbox_message_id': value.get('last_read_outbox_message_id'),
            'unread_mention_count': value.get('unread_mention_count'),
            'unread_reaction_count': value.get('unread_reaction_count'),
            'unread_poll_vote_count': value.get('unread_poll_vote_count'),
        }
    )
    return result


def forum_topics(value: dict) -> dict:
    return {
        'total_count': value.get('total_count'),
        'topics': [forum_topic(item) for item in value.get('topics', [])],
        'next_offset': {
            'date': value.get('next_offset_date'),
            'message_id': value.get('next_offset_message_id'),
            'forum_topic_id': value.get('next_offset_forum_topic_id'),
        },
    }


def _reply_info(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    recent_repliers = value.get('recent_replier_ids')
    if recent_repliers is None:
        recent_repliers = value.get('recent_repliers')
    return {
        'reply_count': value.get('reply_count'),
        'recent_repliers': [_sender(item) for item in (recent_repliers or [])],
        'last_read_inbox_message_id': value.get('last_read_inbox_message_id'),
        'last_read_outbox_message_id': value.get('last_read_outbox_message_id'),
        'last_message_id': value.get('last_message_id'),
    }


def message_thread(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    return {
        'chat_id': value.get('chat_id'),
        'message_thread_id': value.get('message_thread_id'),
        'reply_info': _reply_info(value.get('reply_info')),
        'unread_message_count': value.get('unread_message_count'),
        'messages': [message(item) for item in value.get('messages', [])],
    }


def history(value: dict) -> dict:
    return {
        'total_count': value.get('total_count'),
        'messages': [message(item) for item in value.get('messages', [])],
    }


def statistics(value: dict) -> dict:
    return {
        key: value.get(key) for key in ('size', 'count', 'statistics') if key in value
    }
