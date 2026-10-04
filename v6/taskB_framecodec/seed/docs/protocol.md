# Protocol v1 — framed byte stream

A stream carries a sequence of frames back to back. There is no inter-frame
padding, and a stream may begin with garbage (bytes before the first SOF are
discarded).

```
frame  := SOF len_lo len_hi body crc_lo crc_hi
SOF    := 0x7E
len    := uint16 little-endian — the number of *escaped* body bytes that follow
body   := payload, byte-stuffed
crc    := uint16 little-endian — CRC-16/CCITT-FALSE over the *unescaped* payload
```

## Byte stuffing

Two byte values are special inside a frame and are escaped in the body:

| payload byte | on the wire |
|---|---|
| `0x7E` (SOF) | `0x7D 0x5E` |
| `0x7D` (ESC) | `0x7D 0x5D` |

Escaping is applied to the payload only; the header and CRC bytes are sent raw.
`len` counts the escaped bytes, so the body on the wire is `len` bytes long and
the CRC follows immediately after.

## CRC

CRC-16/CCITT-FALSE: polynomial `0x1021`, initial value `0xFFFF`, no input or
output reflection, no final XOR. It is computed over the **unescaped payload**
bytes, not over the wire body.

## Chunking

The stream is delivered in arbitrary chunks. A frame may be split across any
number of chunks at any byte offset — in the middle of the header, in the middle
of an escape pair, between the body and the CRC, or between two frames. A single
chunk may contain zero, one, or many complete frames, or the tail of one frame
followed by the head of the next. The decoder must be a state machine over the
byte stream, not a function of a single chunk.

## Errors

A frame whose CRC does not match is corrupt: it is discarded and the decoder
resynchronizes on the next SOF. A SOF byte that appears where a body byte was
expected means the current frame was truncated (the sender restarted); the
partial frame is discarded and the SOF begins a new frame.

## Decoder instances are independent

Each `FrameDecoder` owns its own state. Two decoders fed interleaved chunks must
not affect each other; a partial frame held by one is invisible to the other.
