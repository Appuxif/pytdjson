from dataclasses import dataclass


@dataclass
class User:
    """Пользователь из обновления телеграм"""

    # error_info = None

    first_name: str
    last_name: str = ''
    username: str = ''
    phone_number: str = ''
    type: str = ''
    is_contact: bool = False
    is_mutual_contact: bool = False
    is_verified: bool = False
    is_support: bool = False
    is_scam: bool = False
    is_bot: bool = False

    # def build(self, data: dict):
