# PyTDJson

Библиотека для работы с Телеграм. Для конкуррентности используется asyncio.

## Install

> pip install https://github.com/Appuxif/pytdjson/archive/master.zip  

или 

> pip install git+https://github.com/Appuxif/pytdjson/

## Tests

Запуск тестов

> python -m unittest discover -s tests

## Example

Простейший пример  

Сначала запустить авторизацию, чтобы запросить код.  
Будет выброшена ошибка ValueError и авторизация прервется.
```py

from telegram.client import Settings, AsyncTelegram


settings = Settings(
    api_id=1111111,
    api_hash='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    database_encryption_key='mytestkeyshouldbechanged',
    phone='+79999999999',
    files_directory='/tmp/telegram/',
)


tg = AsyncTelegram(settings)
tg.login()

```

Повторно запустить и указать код и, при необходимости,  
пароль для двухфакторной аутентификации
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
)


async def handler(update):
    print(update)

    
tg = AsyncTelegram(settings)
tg.login()
tg.add_message_handler(handler)
tg.run()

```

При последующих запусках код и пароль уже будут не нужны, 
авторизация будет проходить по сессии, которую сгенерирует tdlib

## Projects
Проекты, успешно использующие эту библиотеку  

* [telegramio](https://telegramio.ru) - Сервис по автоматизации телеграма
