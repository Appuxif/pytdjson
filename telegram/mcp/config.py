"""Configuration loading for the optional MCP server."""
import os
from pathlib import Path
from typing import Mapping, Optional

from telegram.client import Settings


class ConfigurationError(ValueError):
    """Raised when MCP startup configuration is incomplete."""


def _parse_send_allowlist(raw_value: Optional[str]) -> tuple[frozenset[int], bool]:
    """Parse the fail-closed MCP message sending allowlist."""
    value = (raw_value or '').strip()
    if not value:
        return frozenset(), False

    entries = [entry.strip() for entry in value.split(',')]
    if any(not entry for entry in entries):
        raise ConfigurationError(
            'PYTDJSON_ALLOW_SEND_TO_CHATS must contain comma-separated chat IDs'
        )
    if '*' in entries:
        if entries != ['*']:
            raise ConfigurationError(
                'PYTDJSON_ALLOW_SEND_TO_CHATS must be either * or chat IDs, not both'
            )
        return frozenset(), True

    try:
        chat_ids = frozenset(int(entry) for entry in entries)
    except ValueError as error:
        raise ConfigurationError(
            'PYTDJSON_ALLOW_SEND_TO_CHATS must contain integer chat IDs'
        ) from error
    if 0 in chat_ids:
        raise ConfigurationError(
            'PYTDJSON_ALLOW_SEND_TO_CHATS cannot contain chat ID 0'
        )
    return chat_ids, False


def load_settings(
    env_file: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Settings:
    """Build Settings from PYTDJSON_* environment variables."""
    if env_file:
        try:
            from dotenv import load_dotenv
        except ImportError as error:
            raise ConfigurationError(
                "dotenv support requires `pytdjson[mcp]`"
            ) from error
        load_dotenv(env_file, override=False)

    values = os.environ if environ is None else environ
    required = (
        'PYTDJSON_API_ID',
        'PYTDJSON_API_HASH',
        'PYTDJSON_DATABASE_ENCRYPTION_KEY',
        'PYTDJSON_FILES_DIRECTORY',
    )
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise ConfigurationError('Missing required settings: ' + ', '.join(missing))

    phone = values.get('PYTDJSON_PHONE') or None
    bot_token = values.get('PYTDJSON_BOT_TOKEN') or None
    if not phone and not bot_token:
        raise ConfigurationError('Set PYTDJSON_PHONE or PYTDJSON_BOT_TOKEN')

    try:
        api_id = int(values['PYTDJSON_API_ID'])
    except ValueError as error:
        raise ConfigurationError('PYTDJSON_API_ID must be an integer') from error

    files_directory = Path(values['PYTDJSON_FILES_DIRECTORY']).expanduser()
    files_directory.mkdir(parents=True, exist_ok=True)
    allowed_send_to_chats, allow_send_to_all_chats = _parse_send_allowlist(
        values.get('PYTDJSON_ALLOW_SEND_TO_CHATS')
    )
    return Settings(
        api_id=api_id,
        api_hash=values['PYTDJSON_API_HASH'],
        database_encryption_key=values['PYTDJSON_DATABASE_ENCRYPTION_KEY'],
        files_directory=str(files_directory),
        phone=phone,
        bot_token=bot_token,
        library_path=values.get('PYTDJSON_LIBRARY_PATH') or None,
        tdlib_verbosity=int(values.get('PYTDJSON_TDLIB_VERBOSITY', '0')),
        mcp_allowed_send_to_chats=allowed_send_to_chats,
        mcp_allow_send_to_all_chats=allow_send_to_all_chats,
    )
