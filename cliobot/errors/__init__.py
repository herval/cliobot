

class BaseErrorHandler:

    def capture_exception(self, exception):
        print(exception)

    def set_context(self, data):
        print(data)


class MessageNoLongerExists(Exception):  # should mark the conversation as deleted
    pass


class MessageNotModifiable(Exception):  # should mark the conversation as noop
    pass


class UserBlocked(Exception):  # user blocked the bot or we blocked the user
    pass


class UnknownError(Exception):  # should ignore
    pass


class TransientFailure(Exception):  # should ignore
    pass
