from copy import deepcopy
from unittest import TestCase

from telegram.types.message_content import MessageContent, MessageVenue

content_message_venue = {
    "@type": "messageVenue",
    "venue": {
        "@type": "venue",
        "location": {
            "@type": "location",
            "latitude": 54.0,
            "longitude": 99.0,
            "horizontal_accuracy": 77.0,
        },
        "title": "Venue Title",
        "address": "Venue Address",
        "provider": "Venue provider",
        "id": "Venue id",
        "type": "Venue type",
    },
}


class MessageVenueTestCase(TestCase):
    """
    Тест кейс для объекта MessageVenue
    """

    def test_simple(self):
        """Простой тест"""
        content_dict = deepcopy(content_message_venue)

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessageVenue)
        self.assertEqual('Venue type', content.venue.type)
        self.assertEqual('Venue id', content.venue.id)
        self.assertEqual(54.0, content.venue.location.latitude)
