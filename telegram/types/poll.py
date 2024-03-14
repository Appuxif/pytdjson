from dataclasses import dataclass, field
from enum import Enum
from typing import List

from telegram.types.base import RawDataclass, default_getter
from telegram.types.message import MessageSender
from telegram.types.text import FormattedText


@dataclass
class PollOption(RawDataclass):
    """Опция опроса"""

    text: str = None
    voter_count: int = None
    vote_percentage: int = None
    is_chosen: bool = None
    is_being_chosen: bool = None


class PollType(str, Enum):
    """Типы опросов"""

    QUIZ = 'pollTypeQuiz'
    REGULAR = 'pollTypeRegular'


@dataclass
class Poll(RawDataclass):
    """Опрос"""

    id: int = None
    question: str = None
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
        if 'correct_option_id' in self.raw['type']:
            self.correct_option_id = self.raw['type']['correct_option_id']
            self.explanation = FormattedText(self.raw['type']['explanation'])
        if 'allow_multiple_answers' in self.raw['type']:
            self.allow_multiple_answers = self.raw['type']['allow_multiple_answers']
