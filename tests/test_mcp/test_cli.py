from io import StringIO
from unittest import TestCase
from unittest.mock import ANY, patch

from telegram.mcp.cli import main


class CommandLineTestCase(TestCase):
    @patch('telegram.mcp.cli.login_interactively')
    @patch('telegram.mcp.cli.load_settings', return_value=object())
    def test_login_reports_success_after_authorization(self, load_settings, login):
        output = StringIO()
        with patch('sys.stdout', output):
            status = main(['login'])

        self.assertEqual(0, status)
        load_settings.assert_called_once_with(None)
        login.assert_called_once()
        self.assertEqual('Telegram authorization completed.\n', output.getvalue())

    @patch('telegram.mcp.server.create_server')
    @patch('telegram.mcp.runtime.TelegramRuntime')
    @patch('telegram.mcp.cli.load_settings', return_value=object())
    def test_serve_uses_streamable_http_options(
        self, load_settings, runtime_class, create_server
    ):
        output = StringIO()
        server = create_server.return_value
        with patch('sys.stderr', output):
            status = main(
                [
                    'serve',
                    '--transport',
                    'streamable-http',
                    '--port',
                    '9911',
                    '--path',
                    '/telegram',
                ]
            )

        self.assertEqual(0, status)
        load_settings.assert_called_once_with(None)
        runtime_class.assert_called_once_with(ANY, on_ready=ANY)
        server.run.assert_called_once_with(
            transport='streamable-http',
            host='127.0.0.1',
            port=9911,
            streamable_http_path='/telegram',
        )
        self.assertIn('http://127.0.0.1:9911/telegram', output.getvalue())

    @patch('telegram.mcp.server.create_server')
    @patch('telegram.mcp.runtime.TelegramRuntime')
    @patch('telegram.mcp.cli.load_settings', return_value=object())
    def test_serve_exits_silently_on_keyboard_interrupt(
        self, load_settings, runtime_class, create_server
    ):
        create_server.return_value.run.side_effect = KeyboardInterrupt

        with patch('sys.stderr', new_callable=StringIO) as output:
            status = main(['serve'])

        self.assertEqual(0, status)
        self.assertNotIn('KeyboardInterrupt', output.getvalue())
