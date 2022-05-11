# PyTDJson

A Python lightweight library to build telegram clients with no requirements.  
It is a wrapper for Telegram's [tdlib](https://core.telegram.org/tdlib) based on asyncio.

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

* [telegramio](https://telegramio.ru) - Telegram authomatizations
