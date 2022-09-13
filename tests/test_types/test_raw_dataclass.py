from dataclasses import dataclass
from enum import Enum
from unittest import TestCase

from telegram.types.base import RawDataclass


class TestEnum(int, Enum):
    """TestEnum"""

    A = 1
    B = 2


@dataclass
class TestRawDataclass(RawDataclass):
    enum_value: TestEnum = None
    value: str = None


class RawDataclassTestCase(TestCase):
    """
    Тест кейс для объекта RawDataclass
    """

    def test_asdict(self):
        instance = TestRawDataclass({'enum_value': 1, 'value': 'test'})
        result = instance.asdict()

        expected = {
            'raw': {
                'enum_value': 1,
                'value': 'test',
            },
            'enum_value': 'TestEnum.A',
            'value': 'test',
        }

        self.assertDictEqual(expected, result)
