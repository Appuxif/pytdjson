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


def _file(value: Optional[dict]) -> Optional[dict]:
    """Return file metadata without exposing TDLib's internal object."""
    if not value:
        return None
    local = value.get('local') or {}
    remote = value.get('remote') or {}
    return {
        key: value.get(key) for key in ('id', 'size', 'expected_size') if key in value
    } | {
        'local': {
            key: local.get(key)
            for key in (
                'path',
                'can_be_downloaded',
                'is_downloading_active',
                'is_downloading_completed',
                'download_offset',
                'downloaded_prefix_size',
                'downloaded_size',
            )
            if key in local
        },
        'remote': {
            key: remote.get(key)
            for key in (
                'id',
                'unique_id',
                'is_uploading_active',
                'is_uploading_completed',
                'uploaded_size',
            )
            if key in remote
        },
    }


def _media(value: dict) -> Optional[dict]:
    """Project common media fields and file identifiers."""
    content_type = value.get('@type')
    media_key = {
        'messageAnimation': 'animation',
        'messageAudio': 'audio',
        'messageDocument': 'document',
        'messagePhoto': 'photo',
        'messageVideo': 'video',
        'messageVideoNote': 'video_note',
        'messageVoiceNote': 'voice_note',
    }.get(content_type)
    if media_key is None:
        return None
    media = value.get(media_key) or {}
    result = {'type': content_type}
    result.update(
        {
            key: media.get(key)
            for key in (
                'duration',
                'width',
                'height',
                'length',
                'file_name',
                'mime_type',
                'performer',
                'title',
                'supports_streaming',
            )
            if key in media
        }
    )
    if media.get('thumbnail'):
        result['thumbnail'] = _file((media.get('thumbnail') or {}).get('file'))
    if media.get('album_cover_thumbnail'):
        result['album_cover_thumbnail'] = _file(
            (media.get('album_cover_thumbnail') or {}).get('file')
        )
    if content_type == 'messagePhoto':
        result['files'] = [
            _file(item.get('photo'))
            for item in media.get('sizes', [])
            if _file(item.get('photo')) is not None
        ]
    else:
        file_key = {
            'messageVoiceNote': 'voice',
            'messageVideoNote': 'video',
        }.get(content_type, media_key)
        file_value = media.get(file_key)
        if file_value is None:
            file_value = media.get('file')
        result['file'] = _file(file_value)
    return result


def _forward(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    origin = value.get('origin') or {}
    result = {
        'date': value.get('date'),
        'source': value.get('source'),
        'public_service_announcement_type': value.get(
            'public_service_announcement_type'
        ),
        'origin': {'type': origin.get('@type')},
    }
    for key in (
        'user_id',
        'chat_id',
        'message_id',
        'sender_name',
        'author_signature',
    ):
        if key in origin:
            result['origin'][key] = origin[key]
    return result


def _reaction_type(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {'type': value.get('@type')}
    for key in ('emoji', 'custom_emoji_id', 'star_count'):
        if key in value:
            result[key] = value[key]
    return result


def _available_reaction(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    return {
        'reaction': _reaction_type(value.get('type')),
        'needs_premium': value.get('needs_premium'),
    }


def _interaction(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {
        key: value.get(key) for key in ('view_count', 'forward_count') if key in value
    }
    if value.get('reply_info') is not None:
        result['reply_info'] = _reply_info(value.get('reply_info'))
    reactions = value.get('reactions') or {}
    if reactions:
        result['reactions'] = [
            {
                **(_reaction_type(item.get('type')) or {}),
                'total_count': item.get('total_count'),
                'is_chosen': item.get('is_chosen'),
            }
            for item in reactions.get('reactions', [])
        ]
    return result


def _transcript(content: dict) -> Optional[dict]:
    media_key = {
        'messageVoiceNote': 'voice_note',
        'messageVideoNote': 'video_note',
    }.get(content.get('@type'))
    if media_key is None:
        return None
    result = (content.get(media_key) or {}).get('speech_recognition_result')
    if not result:
        return None
    result_type = result.get('@type')
    if result_type == 'speechRecognitionResultPending':
        return {'status': 'pending', 'text': result.get('partial_text', '')}
    if result_type == 'speechRecognitionResultText':
        return {'status': 'completed', 'text': result.get('text', '')}
    if result_type == 'speechRecognitionResultError':
        error = result.get('error') or {}
        return {
            'status': 'failed',
            'error': {key: error[key] for key in ('code', 'message') if key in error},
        }
    return None


def _project_content(content: Optional[dict]) -> dict:
    content = content or {}
    text = content.get('text') or content.get('caption') or {}
    sticker = content.get('sticker') or {}
    text_value = text.get('text') if isinstance(text, dict) else None
    if content.get('@type') == 'messageSticker' and text_value is None:
        text_value = sticker.get('emoji')
    return {
        'content_type': content.get('@type'),
        'text': text_value,
        'entities': text.get('entities') if isinstance(text, dict) else None,
        'transcript': _transcript(content),
        'sticker_emoji': sticker.get('emoji'),
        'sticker_id': sticker.get('id'),
        'sticker_set_id': sticker.get('set_id'),
        'sticker_is_premium': content.get('is_premium'),
        'media': _media(content),
    }


def message(
    value: Optional[dict], sender_details: Optional[dict] = None
) -> Optional[dict]:
    if not value:
        return None
    content = value.get('content') or {}
    result = {
        'id': value.get('id'),
        'chat_id': value.get('chat_id'),
        'sender': _sender(value.get('sender_id') or value.get('sender')),
        'date': value.get('date'),
        'edit_date': value.get('edit_date'),
        'is_outgoing': value.get('is_outgoing'),
        'topic_id': _topic_id(value.get('topic_id')),
        'reply_to': _reply_to(value.get('reply_to')),
        'is_pinned': value.get('is_pinned'),
        'is_channel_post': value.get('is_channel_post'),
        'reply_info': _reply_info(value.get('interaction_info', {}).get('reply_info'))
        if isinstance(value.get('interaction_info'), dict)
        else None,
        'interaction': _interaction(value.get('interaction_info')),
        'forward': _forward(value.get('forward_info')),
        **_project_content(content),
    }
    if sender_details is not None:
        result['sender_details'] = sender_details
    return result


def file(value: Optional[dict]) -> Optional[dict]:
    return _file(value)


def available_reactions(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    unavailability_reason = value.get('unavailability_reason') or {}
    return {
        'top_reactions': [
            _available_reaction(item) for item in value.get('top_reactions', [])
        ],
        'recent_reactions': [
            _available_reaction(item) for item in value.get('recent_reactions', [])
        ],
        'popular_reactions': [
            _available_reaction(item) for item in value.get('popular_reactions', [])
        ],
        'allow_custom_emoji': value.get('allow_custom_emoji'),
        'are_tags': value.get('are_tags'),
        'unavailability_reason': (
            {'type': unavailability_reason.get('@type')}
            if unavailability_reason
            else None
        ),
    }


def added_reactions(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    return {
        'total_count': value.get('total_count'),
        'reactions': [
            {
                'reaction': _reaction_type(item.get('type')),
                'sender': _sender(item.get('sender_id')),
                'is_outgoing': item.get('is_outgoing'),
                'date': item.get('date'),
            }
            for item in value.get('reactions', [])
        ],
        'next_offset': value.get('next_offset', ''),
    }


def transcription_request(value: Optional[dict]) -> Optional[dict]:
    if not value:
        return None
    result = {
        'status': value.get('status'),
        'chat_id': value.get('chat_id'),
        'message_id': value.get('message_id'),
    }
    if 'text' in value:
        result['text'] = value['text']
    if 'error' in value:
        error = value['error'] or {}
        result['error'] = {
            key: error[key] for key in ('code', 'message') if key in error
        }
    if 'original_message' in value:
        result['original_message'] = message(value['original_message'])
    return result


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
    if value.get('@type') == 'mcpMessageTranscription':
        result['type'] = 'message_transcription'
        result.update(transcription_request(value) or {})
        return result
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

    if 'actor_id' in value:
        result['actor_id'] = _sender(value.get('actor_id'))
    if 'interaction_info' in value:
        result['interaction_info'] = _interaction(value.get('interaction_info'))
    for key in ('old_reaction_types', 'new_reaction_types'):
        if key in value:
            result[key] = [
                _reaction_type(item) for item in (value.get(key) or [])
            ]

    if 'message' in value:
        result['message'] = message(value['message'])
    if value.get('@type') == 'updateMessageContent':
        result['new_content'] = _project_content(value.get('new_content'))
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
        'topics': [forum_topic(item) for item in (value.get('topics') or [])],
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
        'messages': [message(item) for item in (value.get('messages') or [])],
    }


def history(value: dict, sender_details: Optional[dict] = None) -> dict:
    return {
        'total_count': value.get('total_count'),
        'messages': [
            message(
                item,
                (sender_details or {}).get(
                    ((item.get('sender_id') or {}).get('user_id'))
                ),
            )
            for item in (value.get('messages') or [])
        ],
    }


def found_messages(value: dict, sender_details: Optional[dict] = None) -> dict:
    return {
        'total_count': value.get('total_count'),
        'messages': [
            message(
                item,
                (sender_details or {}).get(
                    ((item.get('sender_id') or {}).get('user_id'))
                ),
            )
            for item in (value.get('messages') or [])
        ],
        'next_offset': value.get('next_offset'),
        'next_from_message_id': value.get('next_from_message_id'),
    }


def statistics(value: dict) -> dict:
    return {
        key: value.get(key) for key in ('size', 'count', 'statistics') if key in value
    }
