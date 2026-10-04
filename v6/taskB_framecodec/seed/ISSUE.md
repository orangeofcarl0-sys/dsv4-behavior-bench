# ISSUE: frames lost at chunk boundaries

**Reported by:** ingest team
**Severity:** high — silent data loss

## Symptom

Frames disappear from the decoded stream. It is not reproducible with a fixed
chunking, but shows up in production where the transport delivers chunks of
whatever size the socket read returns. A payload that encodes and decodes fine
when the whole frame arrives in one chunk is sometimes dropped when the same
bytes are split across two reads.

The most reliable reproduction is a payload that contains `0x7E` or `0x7D`
(so the body is byte-stuffed) combined with a chunk boundary that lands inside
the escape pair, or a chunk boundary inside the 2-byte length header. Under those
splits, the frame is dropped and no error is raised — the bytes are silently
consumed.

## What we need

The decoder must be correct for **any** chunking of a valid stream: splitting a
frame at any byte offset (including inside the escape sequence, the header, the
body/CRC boundary, and between frames) must yield exactly the same frames as
delivering the whole stream in one chunk. Corrupt frames must still be dropped,
and a truncated frame interrupted by a new SOF must not corrupt the frame that
follows.

Do not change the wire format or the public API. Keep `FrameDecoder`, `feed`,
`encode_frame`, `crc16`, and `FrameError` as they are. Do not modify `tests/`.
