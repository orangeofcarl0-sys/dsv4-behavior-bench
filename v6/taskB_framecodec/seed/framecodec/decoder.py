"""framecodec — incremental frame decoder for a length-prefixed byte protocol.

NOTE: v1.2 tree, mid-refactor. The decoder buffers bytes and extracts complete
frames, which is enough for the public suite (whole frames). Production has
reported silent frame loss when a frame straddles a chunk boundary; see
ISSUE.md.
"""
SOF = 0x7E
ESC = 0x7D
ESC_XOR = 0x20


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE."""
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
    """Incremental decoder (v1.2 attempt)."""

    def __init__(self):
        self.buf = bytearray()

    def feed(self, chunk: bytes) -> list:
        self.buf.extend(chunk)
        frames = []
        pos = 0
        while True:
            start = self.buf.find(SOF, pos)
            if start < 0:
                break
            if len(self.buf) - start < 3:
                break
            length = self.buf[start + 1] | (self.buf[start + 2] << 8)
            end = start + 3 + length + 2
            if len(self.buf) < end:
                break
            body = bytes(self.buf[start + 3:start + 3 + length])
            want = self.buf[start + 3 + length] | (self.buf[start + 4 + length] << 8)
            payload = body.replace(bytes([ESC, SOF ^ ESC_XOR]), bytes([SOF]))
            payload = payload.replace(bytes([ESC, ESC ^ ESC_XOR]), bytes([ESC]))
            pos = end
            if want == crc16(payload):
                frames.append(payload)
        # Keep only what is still needed; anything before the last start is
        # consumed. (This is the mid-refactor shortcut: the tail is dropped
        # rather than carried into the next call.)
        self.buf = bytearray()
        return frames
