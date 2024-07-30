class WhenError(Exception):
    pass


class UnknownSourceError(WhenError):
    pass


class DBError(WhenError):
    pass
