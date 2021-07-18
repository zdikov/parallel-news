class BaseApplicationError(Exception):
    pass


class RequestError(BaseApplicationError):
    """Raised when request to the website is not successful."""

    def __init__(self, url: str, message="Request to the website %s failed"):
        self.url = url
        self.message = message

        super().__init__(self.message)

    def __str__(self):
        return self.message % self.url


class ParseError(BaseApplicationError):
    """Raised for unsuccessful parsing."""

    def __init__(
        self,
        parser: str,
        parser_message: str,
        message="Parser %s raised an error with the following message:\n%s",
    ):
        self.parser = parser
        self.parser_message = parser_message
        self.message = message

        super().__init__(self.message)

    def __str__(self):
        return self.message % (self.parser, self.parser_message)


class WrongNumberOfArguments(BaseApplicationError):
    """Raised when wrong number of arguments passed."""

    def __init__(
        self, expected: int, got: int, message="Expected %d arguments, but %d got"
    ):
        self.expected = expected
        self.got = got
        self.message = message

        super().__init__(self.message)

    def __str__(self):
        return self.message % (self.expected, self.got)
