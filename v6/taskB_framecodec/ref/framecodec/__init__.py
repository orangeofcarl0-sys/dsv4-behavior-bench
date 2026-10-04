"""framecodec — incremental frame decoder for a length-prefixed byte protocol.

Public API:
    FrameDecoder  -- feed(chunk) -> list[bytes] of complete payloads
    encode_frame  -- bytes -> wire frame (for tests/tools)
    crc16         -- CRC-16/CCITT-FALSE
    FrameError    -- raised on a malformed frame when strict=True
"""
from .decoder import FrameDecoder, encode_frame, crc16
from .errors import FrameError

__all__ = ["FrameDecoder", "FrameError", "encode_frame", "crc16"]
