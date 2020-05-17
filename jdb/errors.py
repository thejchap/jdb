class ChecksumMismatch(Exception):
    """unable to verify crc32"""


class TableOverflow(Exception):
    """max reached"""


class Abort(Exception):
    """transaction aborted"""


class InvalidRequest(Exception):
    """invalid request"""
