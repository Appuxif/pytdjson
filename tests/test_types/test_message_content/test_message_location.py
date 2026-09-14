from copy import deepcopy
from unittest import TestCase

from telegram.types.message_content import MessageContent, MessageLocation


static_location = {
    '@type': 'messageLocation',
    'location': {
        '@type': 'location',
        'latitude': 42.441,
        'longitude': 19.263,
        'horizontal_accuracy': 0,
    },
}

live_location = {
    '@type': 'messageLiveLocation',
    'location': {
        '@type': 'liveLocation',
        'location': static_location['location'],
        'live_period': 900,
        'heading': 90,
        'proximity_alert_radius': 150,
    },
    'expires_in': 600,
}


class MessageLocationTestCase(TestCase):
    def test_static_location(self):
        content = MessageContent(deepcopy(static_location))

        self.assertIsInstance(content, MessageLocation)
        self.assertEqual(42.441, content.location.latitude)
        self.assertIsNone(content.live_period)

    def test_live_location_uses_legacy_wrapper_shape(self):
        content = MessageContent(deepcopy(live_location))

        self.assertIsInstance(content, MessageLocation)
        self.assertEqual(42.441, content.location.latitude)
        self.assertEqual(900, content.live_period)
        self.assertEqual(90, content.heading)
        self.assertEqual(150, content.proximity_alert_radius)
        self.assertEqual(600, content.expires_in)
