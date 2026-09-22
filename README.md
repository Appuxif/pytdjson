# PyTDJson

A Python lightweight library to build telegram clients with no requirements.  
It is a wrapper for Telegram's [tdlib](https://core.telegram.org/tdlib) based on asyncio.
https://github.com/tdlib/td/blob/master/td/generate/scheme/td_api.tl

# Getting Started

## Install
> pip clone https://github.com/Appuxif/pytdjson  

or

> pip install https://github.com/Appuxif/pytdjson/archive/master.zip  

or 

> pip install git+https://github.com/Appuxif/pytdjson/

## Tests

Launch tests

> python -m unittest discover -s tests

## MCP server

`pytdjson-mcp` is an optional MCP server for local AI agents. It
uses the same TDLib session database as the Python wrapper. It supports stdio
and Streamable HTTP transports, and exposes compact summaries for chats,
messages, users (including batch user lookup), groups, links, local statistics,
and an allowlisted `send_message` tool; it doesn't mark messages as read.
Forum-aware tools list forum topics, read topic history, and read reply-thread
history.

Install it from a release tag with the optional extra:

> pip install "pytdjson[mcp] @ https://github.com/Appuxif/pytdjson/archive/refs/tags/0.8.0.zip"

Copy `.env.example` to a private local file, set its `PYTDJSON_*` values, and
keep it outside version control. The database encryption key, API hash, and
bot token are secrets. For a phone account, authorize once in a terminal:

> pytdjson-mcp login --env-file /secure/path/pytdjson.env

The command prompts for the Telegram code and two-step-verification password
only when TDLib asks for them. They are never saved to the dotenv file. Later,
run the MCP server with the same files directory:

> pytdjson-mcp serve --env-file /secure/path/pytdjson.env

Configure an MCP host to launch that command over stdio. The server requires
an existing authorized session; if it expires, run `login` again in a terminal.

Message sending is disabled by default. To allow it for selected chats, add
their numeric IDs to the private dotenv file:

> PYTDJSON_ALLOW_SEND_TO_CHATS=-1001564852174,1043638331

Set `PYTDJSON_ALLOW_SEND_TO_CHATS=*` only when sending to every chat is
intentional. The `send_message` tool supports ordinary messages, replies,
non-forum message threads, and forum topics.

For live updates, first call `subscribe_for_updates` with the chat IDs of
interest. Calling `poll_updates` without any subscriptions returns an error
immediately. Otherwise it waits for up to `limit` updates, where `limit`
defaults to `1`, and returns a cursor. After processing the updates, call
`commit_updates` with that cursor. The MCP runtime persists subscriptions,
buffered updates, cursors, and sent-message suppression IDs in its own
`mcp_state.sqlite3` file alongside the TDLib data; it does not access TDLib's
private database schema.
`check_updates_subscription` shows active subscriptions and the bounded
in-memory buffer. `unsubscribe_from_updates` stops collecting updates and
removes buffered events for those chats.

Voice messages and round video messages can be transcribed asynchronously.
After receiving one through `poll_updates`, call
`request_message_transcript(chat_id, message_id)`. The tool returns immediately
with `status: "pending"`; keep polling for a `message_transcription` event with
the final text or an error and commit it using the normal cursor workflow.
Transcription requests survive an MCP restart. TDLib does not provide built-in
transcription for ordinary audio files or regular videos.

For one shared local TDLib session used by multiple MCP clients, run the
Streamable HTTP transport in a persistent terminal or service:

> pytdjson-mcp serve --transport streamable-http --host 127.0.0.1 --port 8765 --env-file /secure/path/pytdjson.env

The endpoint is `http://127.0.0.1:8765/mcp`. Keep the default loopback host
unless you place the server behind authenticated network access. A Codex client
can connect to it with:

```toml
[mcp_servers.telegram]
url = "http://127.0.0.1:8765/mcp"
required = true
startup_timeout_sec = 30
```

## Example

* Take a look at https://core.telegram.org/tdlib
* Get familiar to build your own tdlib for you OS https://github.com/tdlib/td
* An authorization  
  * Start an authorization to get an access code.  
    There will be an ValueError exception that stops an authorization, because you have no access code.  

```py

from telegram.client import Settings, AsyncTelegram


settings = Settings(
    api_id=1111111,
    api_hash='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    database_encryption_key='mytestkeyshouldbechanged',
    phone='+79999999999',
    files_directory='/tmp/telegram/',
    library_path='./libtdjson.so',
)


tg = AsyncTelegram(settings)
tg.login()

```

  * Restart an authorization with provided auth_code. 
  If your Telegram Account has an 2FA Authorization password, pass it too.  

```py

from telegram.client import Settings, AsyncTelegram


settings = Settings(
    api_id=1111111,
    api_hash='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    database_encryption_key='mytestkeyshouldbechanged',
    phone='+79999999999',
    auth_code='123456',
    password='2FATelegramPassword',
    files_directory='/tmp/telegram/',
    library_path='./libtdjson.so',
)

tg = AsyncTelegram(settings)
tg.login()

```


  * The process stops without errors: you successfully authorized! You will no longer need to pass auth_code or 2FA password. 
  * Now you can use it to build your own telegram client   

```py

from telegram.client import Settings, AsyncTelegram
from telegram.types.update import UpdateNewMessage


settings = Settings(
    api_id=1111111,
    api_hash='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    database_encryption_key='mytestkeyshouldbechanged',
    phone='+79999999999',
    auth_code='123456',
    password='2FATelegramPassword',
    files_directory='/tmp/telegram/',
)


async def update_new_message_handler(update: UpdateNewMessage):
    print(update)
    await tg.api.send_message(update.message.chat_id, 'Hello')

    
tg = AsyncTelegram(settings)
tg.login()
tg.add_message_handler(update_new_message_handler)
tg.run()

```

## Projects
Projects, using that library  

* [telegramio](https://telegramio.ru) - Telegram automatizations


# Contributing

[Look at CONTRIBUTING.md](CONTRIBUTING.md)
