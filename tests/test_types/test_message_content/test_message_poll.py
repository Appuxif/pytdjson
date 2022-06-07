from copy import deepcopy
from unittest import TestCase

from telegram.types.message_content import MessageContent, MessagePoll, PollType

content_message_poll = {
    "@type": "messagePoll",
    "poll": {
        "@type": "poll",
        "id": "5258351215229534512",
        "question": "Что выведет этот код?",
        "options": [
            {
                "@type": "pollOption",
                "text": "True",
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
            {
                "@type": "pollOption",
                "text": "False",
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
            {
                "@type": "pollOption",
                "text": "Ошибку",
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
            {
                "@type": "pollOption",
                "text": "Узнать ответ",
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
        ],
        "total_voter_count": 0,
        "recent_voter_user_ids": [],
        "is_anonymous": True,
        "type": {
            "@type": "pollTypeQuiz",
            "correct_option_id": -1,
            "explanation": {"@type": "formattedText", "text": "", "entities": []},
        },
        "open_period": 0,
        "close_date": 0,
        "is_closed": False,
    },
}


class MessagePollTestCase(TestCase):
    """
    Тест кейс для объекта MessagePoll
    """

    def test_simple(self):
        """Простой тест"""
        content_dict = deepcopy(content_message_poll)

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessagePoll)
        self.assertEqual(PollType.QUIZ, content.poll.type)
        self.assertEqual(-1, content.poll.correct_option_id)
        self.assertEqual('', content.poll.explanation.text)
        self.assertEqual(5258351215229534512, content.poll.id)
        self.assertEqual(4, len(content.poll.options))
        self.assertEqual('True', content.poll.options[0].text)
        self.assertListEqual([], content.poll.recent_voter_user_ids)
        self.assertEqual(True, content.poll.is_anonymous)
        self.assertEqual(False, content.poll.is_closed)
