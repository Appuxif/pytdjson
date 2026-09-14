import tempfile
from pathlib import Path
from unittest import TestCase

from telegram.mcp.config import ConfigurationError, load_settings


class ConfigurationTestCase(TestCase):
    def test_loads_required_environment_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                environ={
                    'PYTDJSON_API_ID': '42',
                    'PYTDJSON_API_HASH': 'hash',
                    'PYTDJSON_DATABASE_ENCRYPTION_KEY': 'key',
                    'PYTDJSON_FILES_DIRECTORY': str(Path(directory) / 'session'),
                    'PYTDJSON_BOT_TOKEN': 'token',
                }
            )

        self.assertEqual(42, settings.api_id)
        self.assertEqual('token', settings.bot_token)

    def test_rejects_missing_secrets_without_echoing_values(self):
        with self.assertRaises(ConfigurationError) as error:
            load_settings(environ={'PYTDJSON_API_ID': '42'})

        self.assertIn('PYTDJSON_API_HASH', str(error.exception))
