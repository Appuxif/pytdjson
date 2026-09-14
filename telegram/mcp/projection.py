"""Compact, stable MCP responses derived from TDLib JSON."""
from typing import Optional


def _sender(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {'type': value.get('@type')}
    result.update({key: value[key] for key in ('user_id', 'chat_id') if key in value})
    return result


def message(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    content = value.get('content') or {}
    text = content.get('text') or content.get('caption') or {}
    return {
        'id': value.get('id'),
        'chat_id': value.get('chat_id'),
        'sender': _sender(value.get('sender_id') or value.get('sender')),
        'date': value.get('date'),
        'edit_date': value.get('edit_date'),
        'is_outgoing': value.get('is_outgoing'),
        'content_type': content.get('@type'),
        'text': text.get('text') if isinstance(text, dict) else None,
    }


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


def history(value: dict) -> dict:
    return {
        'total_count': value.get('total_count'),
        'messages': [message(item) for item in value.get('messages', [])],
    }


def statistics(value: dict) -> dict:
    return {
        key: value.get(key) for key in ('size', 'count', 'statistics') if key in value
    }
