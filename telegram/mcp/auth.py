"""Interactive terminal-only first-time authorization."""
from getpass import getpass
from time import monotonic
from typing import Callable

from telegram.client import AsyncTelegram, Settings
from telegram.exceptions import AuthCodeNotSet, FirstNameNotSet, PasswordNotSet


def _close_tdlib(client: AsyncTelegram, timeout: float = 10) -> None:
    """Release the TDLib database lock before discarding a client.

    The process-style TDLib API creates clients with ``td_create_client_id``.
    Its matching shutdown operation is a ``close`` request, followed by the
    ``authorizationStateClosed`` update; ``td_json_client_destroy`` belongs to
    TDLib's different pointer-based API and must not be used here.
    """
    client._tdjson.send({'@type': 'close'})
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        update = client._tdjson.receive()
        if (
            update
            and update.get('@type') == 'updateAuthorizationState'
            and update.get('authorization_state', {}).get('@type')
            == 'authorizationStateClosed'
        ):
            return
    raise TimeoutError('TDLib did not close before the shutdown timeout')


def login_interactively(
    settings: Settings,
    client_factory: Callable[[Settings], AsyncTelegram] = AsyncTelegram,
    secret_input: Callable[[str], str] = getpass,
    text_input: Callable[[str], str] = input,
) -> None:
    """Authorize TDLib, keeping prompted credentials only in memory."""
    while True:
        client = client_factory(settings)
        # Missing interactive credentials are expected during first-time login.
        # AsyncTelegram otherwise logs them as worker tracebacks before we can
        # prompt for the required value.
        client.logger.disabled = True
        try:
            try:
                client.login(timeout=None)
                return
            except AuthCodeNotSet:
                settings.auth_code = secret_input('Telegram authentication code: ')
            except PasswordNotSet:
                settings.password = secret_input(
                    'Telegram two-step verification password: '
                )
            except FirstNameNotSet:
                settings.first_name = text_input('Telegram first name: ').strip()
        finally:
            _close_tdlib(client)
