from types import SimpleNamespace
from unittest import TestCase

from telegram.exceptions import AuthCodeNotSet
from telegram.mcp.auth import login_interactively


class FakeTDJson:
    def __init__(self):
        self.requests = []
        self.responses = [
            {
                '@type': 'updateAuthorizationState',
                'authorization_state': {'@type': 'authorizationStateClosed'},
            }
        ]

    def send(self, request):
        self.requests.append(request)

    def receive(self):
        return self.responses.pop(0) if self.responses else None


class FakeClient:
    def __init__(self):
        self._tdjson = FakeTDJson()
        self.login_calls = 0
        self.logger = SimpleNamespace(disabled=False)

    def login(self, timeout):
        self.login_calls += 1
        if self.should_request_code:
            raise AuthCodeNotSet()
        return True


class AuthenticationTestCase(TestCase):
    def test_closes_each_client_before_retrying_authentication_code(self):
        settings = SimpleNamespace(auth_code=None)
        first_client = FakeClient()
        first_client.should_request_code = True
        second_client = FakeClient()
        second_client.should_request_code = False
        clients = [first_client, second_client]
        factory_calls = []

        def client_factory(_settings):
            factory_calls.append(_settings)
            return clients.pop(0)

        login_interactively(
            settings,
            client_factory=client_factory,
            secret_input=lambda _prompt: '12345',
        )

        self.assertEqual([settings, settings], factory_calls)
        self.assertEqual(1, first_client.login_calls)
        self.assertEqual(1, second_client.login_calls)
        self.assertEqual('12345', settings.auth_code)
        self.assertEqual([{'@type': 'close'}], first_client._tdjson.requests)
        self.assertEqual([{'@type': 'close'}], second_client._tdjson.requests)
        self.assertTrue(first_client.logger.disabled)
        self.assertTrue(second_client.logger.disabled)
