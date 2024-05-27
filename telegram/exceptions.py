class SetupError(ValueError):
    def __init__(self, msg: str = 'Something wrong with setup'):
        super().__init__(msg)


class ApiIdNotSet(SetupError):
    def __init__(self, msg: str = 'api_id not set'):
        super().__init__(msg)


class ApiHashNotSet(SetupError):
    def __init__(self, msg: str = 'api_hash not set'):
        super().__init__(msg)


class PhoneNotSet(SetupError):
    def __init__(self, msg: str = 'phone not set'):
        super().__init__(msg)


class TokenNotSet(SetupError):
    def __init__(self, msg: str = 'token not set'):
        super().__init__(msg)


class AuthCodeNotSet(SetupError):
    def __init__(self, msg: str = 'auth_code not set'):
        super().__init__(msg)


class FirstNameNotSet(SetupError):
    def __init__(self, msg: str = 'first name not set'):
        super().__init__(msg)


class PasswordNotSet(SetupError):
    def __init__(self, msg: str = 'password not set'):
        super().__init__(msg)
