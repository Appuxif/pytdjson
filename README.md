# PyTDJson

Библиотека для работы с Телеграм. Для конкуррентности используется asyncio.

## Install

> pip install https://github.com/Appuxif/pytdjson/archive/master.zip  

or  

> pip install git+https://github.com/Appuxif/pytdjson/

## Example

Простейший пример

```py

from telegram.client import Settings, AsyncTelegram


settings = Settings(
    api_id=1111111,
    api_hash='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    database_encryption_key='mytestkeyshouldbechanged',
    phone='+79999999999',
    password='2FATelegramPassword',
    library_path='./telegram/lib/linux/libtdjson.so',
    files_directory='/tmp/telegram/',
    use_message_database=False,
)


async def handler(update):
    print(update)

    
tg = AsyncTelegram(settings)
tg.login()
tg.add_message_handler(handler)
tg.run()

```