"""framecodec — incremental frame decoder for a length-prefixed byte protocol."""


class FrameError(Exception):
    """A malformed or corrupt frame (data-level error)."""
