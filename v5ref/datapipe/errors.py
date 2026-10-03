"""Error types for datapipe.

`DataError` marks a record-level data problem (malformed / invalid record).
It is deliberately NOT a subclass of ValueError so that data errors can be
told apart from usage/config errors at the CLI boundary.
"""


class DataError(Exception):
    """A record-level data error (malformed or invalid input record)."""
