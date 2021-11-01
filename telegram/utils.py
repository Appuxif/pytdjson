from typing import Any, Dict, Optional


class Result:
    """Синхронный результат запроса в tdlib"""

    def __init__(
        self,
        data: Dict[Any, Any],
        update: Dict[Any, Any],
        request_id: Optional[str] = None,
    ):
        self.id = request_id

        self._data: Dict[Any, Any] = data
        self.update: Dict[Any, Any] = update
        self.ok_received = False
        self.error_received = False

        if update.get('@type') == 'error':
            self.error_received = True
        else:
            self.ok_received = True

    def is_valid(self, raise_exc=True):
        try:
            error_messages = []
            if self.error_received:
                error_messages.append('Telegram error')

            if self.update is None:
                error_messages.append('Something wrong, the result update is None')

            if error_messages:
                error_messages.append(str(self._data))
                error_messages.append(str(self.update))
                raise RuntimeError('\n'.join(error_messages))

        except RuntimeError as e:
            if raise_exc:
                raise e
            return False

    def __str__(self) -> str:
        return f'Result <{self.id}>'
