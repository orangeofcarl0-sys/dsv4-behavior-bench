"""framecodec — a byte-stream frame decoder for a length-prefixed wire protocol.

Wire format (v1), documented in docs/protocol.md:

    frame   := SOF len_lo len_hi body crc_lo crc_hi
    SOF     := 0x7E
    len     := little-endian uint16, length of the *escaped* body in bytes
    body    := payload with 0x7E -> 0x7D 0x5E and 0x7D -> 0x7D 0x5D
    crc     := little-endian uint16, CRC-16/CCITT-FALSE over the *unescaped*
               payload bytes

The decoder is fed arbitrary chunks: a frame may be split across chunks at any
byte boundary, including inside the escape sequence or the header.
"""
SOF = 0x7E
ESC = 0x7D
ESC_XOR = 0x20


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no xorout."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(payload: bytes) -> bytes:
    """Encode a payload into a wire frame (used by tests and tools)."""
    out = bytearray([SOF])
    body = bytearray()
    for b in payload:
        if b in (SOF, ESC):
            body.append(ESC)
            body.append(b ^ ESC_XOR)
        else:
            body.append(b)
    length = len(body)
    out.append(length & 0xFF)
    out.append((length >> 8) & 0xFF)
    out.extend(body)
    c = crc16(payload)
    out.append(c & 0xFF)
    out.append((c >> 8) & 0xFF)
    return bytes(out)


class FrameDecoder:
    """Incremental frame decoder.

    feed(chunk) -> list of complete payloads. State is carried across calls, so
    a frame split across chunk boundaries is reassembled. A frame whose CRC does
    not match is discarded and the decoder resynchronizes on the next SOF; a
    SOF seen mid-frame also resynchronizes (the interrupted frame is dropped).
    """

    def __init__(self):
        self._reset()

    def _reset(self):
        self._state = "seek"      # seek -> header -> body -> crc
        self._header = bytearray()
        self._payload = bytearray()
        self._escaped = False
        self._len = 0
        self._raw = 0             # escaped body bytes consumed so far
        self._crc = bytearray()

    def feed(self, chunk: bytes) -> list:
        frames = []
        for b in chunk:
            payload = self._byte(b)
            if payload is not None:
                frames.append(payload)
        return frames

    def _byte(self, b):
        if self._state == "seek":
            if b == SOF:
                self._header = bytearray()
                self._state = "header"
            return None

        if self._state == "header":
            self._header.append(b)
            if len(self._header) == 2:
                self._len = self._header[0] | (self._header[1] << 8)
                self._payload = bytearray()
                self._escaped = False
                self._raw = 0
                if self._len == 0:
                    self._crc = bytearray()
                    self._state = "crc"
                else:
                    self._state = "body"
            return None

        if self._state == "body":
            self._raw += 1
            if self._escaped:
                self._payload.append(b ^ ESC_XOR)
                self._escaped = False
            elif b == ESC:
                self._escaped = True
            elif b == SOF:
                # A fresh SOF before the frame completed: resynchronize; the
                # interrupted frame is dropped and this SOF starts a new one.
                self._header = bytearray()
                self._state = "header"
                return None
            else:
                self._payload.append(b)
            if self._raw >= self._len:
                self._crc = bytearray()
                self._state = "crc"
            return None

        if self._state == "crc":
            self._crc.append(b)
            if len(self._crc) == 2:
                want = self._crc[0] | (self._crc[1] << 8)
                payload = bytes(self._payload)
                self._state = "seek"
                if want == crc16(payload):
                    return payload
                return None
            return None

        return None
