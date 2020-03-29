class JdbError(Exception):
    pass


class ChecksumMismatch(JdbError):
    pass


class LogOverflow(JdbError):
    pass


class NotFound(JdbError):
    pass
