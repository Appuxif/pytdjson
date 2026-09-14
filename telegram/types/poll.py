from dataclasses import dataclass, field
from enum import Enum
from typing import List

from telegram.types.base import RawDataclass, default_getter
from telegram.types.message_sender import MessageSender
from telegram.types.text import FormattedText


@dataclass
class PollOption(RawDataclass):
    """Опция опроса"""

    text: str = None
    text_formatted: FormattedText = None
    voter_count: int = None
    vote_percentage: int = None
    is_chosen: bool = None
    is_being_chosen: bool = None

    def _assign_raw(self):
        if 'text' in self.raw:
            self.text_formatted = FormattedText(self.raw['text'])
            self.text = self.text_formatted.text


class PollType(str, Enum):
    """Типы опросов"""

    QUIZ = 'pollTypeQuiz'
    REGULAR = 'pollTypeRegular'


@dataclass
class Poll(RawDataclass):
    """Опрос"""

    id: int = None
    question: str = None
    question_formatted: FormattedText = None
    options: List[PollOption] = field(
        default=None,
        metadata={'getter': lambda options: [PollOption(opt) for opt in options]},
    )
    total_voter_count: int = None
    recent_voter_user_ids: List[int] = field(  # deprecated
        default=None,
        metadata={'getter': default_getter},
    )
    recent_voter_ids: List[MessageSender] = field(
        default=None,
        metadata={'getter': lambda value: [MessageSender(raw) for raw in value]},
    )
    is_anonymous: bool = None
    type: PollType = field(
        default=None,
        metadata={'getter': lambda value: PollType(value['@type'])},
    )
    open_period: int = None
    close_date: int = None
    is_closed: bool = None

    # only pollTypeQuiz
    correct_option_id: int = None
    explanation: FormattedText = None

    # only pollTypeRegular
    allow_multiple_answers: bool = None

    def _assign_raw(self):
        if 'question' in self.raw:
            self.question_formatted = FormattedText(self.raw['question'])
            self.question = self.question_formatted.text

        poll_type = self.raw.get('type', {})
        if 'correct_option_id' in poll_type:
            self.correct_option_id = poll_type['correct_option_id']
        elif 'correct_option_ids' in poll_type:
            correct_option_ids = poll_type['correct_option_ids']
            self.correct_option_id = (
                correct_option_ids[0] if correct_option_ids else -1
            )

        if 'explanation' in poll_type:
            self.explanation = FormattedText(poll_type['explanation'])

        if 'allow_multiple_answers' in poll_type:
            self.allow_multiple_answers = poll_type['allow_multiple_answers']
        elif 'allows_multiple_answers' in self.raw:
            self.allow_multiple_answers = self.raw['allows_multiple_answers']
