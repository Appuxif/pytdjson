from copy import deepcopy
from unittest import TestCase

from telegram.types.message_content import MessageContent, MessagePoll
from telegram.types.poll import PollType

content_message_poll = {
    "@type": "messagePoll",
    "poll": {
        "@type": "poll",
        "id": "5258351215229534512",
        "question": {"text": "Что выведет этот код?", "entities": []},
        "options": [
            {
                "@type": "pollOption",
                "text": {"text": "True", "entities": []},
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
            {
                "@type": "pollOption",
                "text": {"text": "False", "entities": []},
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
            {
                "@type": "pollOption",
                "text": {"text": "Ошибку", "entities": []},
                "voter_count": 0,
                "vote_percentage": 0,
                "is_chosen": False,
                "is_being_chosen": False,
            },
            {
                "@type": "pollOption",
                "text": {"text": "Узнать ответ", "entities": []},
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

    def test_tdlib_1_8_67_preserves_all_quiz_answers(self):
        content_dict = deepcopy(content_message_poll)
        content_dict['poll']['type'] = {
            '@type': 'pollTypeQuiz',
            'correct_option_ids': [1, 3],
            'explanation': {'@type': 'formattedText', 'text': 'Answer', 'entities': []},
        }
        content_dict['poll']['allows_multiple_answers'] = True

        content = MessageContent(content_dict)

        self.assertEqual([1, 3], content.poll.correct_option_ids)
        self.assertEqual(1, content.poll.correct_option_id)
        self.assertTrue(content.poll.allow_multiple_answers)

    def test_tdlib_1_8_67_legacy_poll_fields(self):
        content_dict = deepcopy(content_message_poll)
        content_dict['poll']['allows_multiple_answers'] = True
        content_dict['poll']['type'] = {
            '@type': 'pollTypeQuiz',
            'correct_option_ids': [2],
            'explanation': {'@type': 'formattedText', 'text': 'Because', 'entities': []},
            'explanation_media': None,
        }

        content = MessageContent(content_dict)

        self.assertEqual(2, content.poll.correct_option_id)
        self.assertEqual('Because', content.poll.explanation.text)
        self.assertTrue(content.poll.allow_multiple_answers)

    def test_tdlib_1_8_67_unanswered_quiz(self):
        content_dict = deepcopy(content_message_poll)
        content_dict['poll']['type'] = {
            '@type': 'pollTypeQuiz',
            'correct_option_ids': [],
            'explanation': {'@type': 'formattedText', 'text': '', 'entities': []},
            'explanation_media': None,
        }

        content = MessageContent(content_dict)

        self.assertEqual(-1, content.poll.correct_option_id)
