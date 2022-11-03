class CustomError(Exception):
    pass


class TownDoesNotExist(CustomError):
    def __init__(self):
        super().__init__(
            'Такого города не существует'
        )


class Error(CustomError):
    def __init__(self):
        super().__init__(
            'Что-то пошло не так'
        )
