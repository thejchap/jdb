class ChecksumMismatch(Exception):
    """unable to verify crc32"""


class TableOverflow(Exception):
    """max reached"""


class NotFound(Exception):
    """key not found"""


class Abort(Exception):
    """transaction aborted"""
