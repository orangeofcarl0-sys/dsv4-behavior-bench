"""framecodec hidden suite — chunk-boundary state machine, error recovery,
decoder independence.

Every behavior here is derivable from docs/protocol.md + ISSUE.md. The public
suite is deliberately blind to all of it.

Behaviors (see behavior_manifest.json):
  B1 any-split equivalence      B2 escape split       B3 partial header
  B4 partial payload            B5 crc failure recovery
  B6 truncated frame + resync   B7 multiple frames/chunk
  B8 empty chunk no-op          B9 decoder independence
"""
import itertools
import os
import sys
from pathlib import Path

import pytest

REPO = Path(os.environ.get("CANDIDATE_REPO",
                           Path(__file__).resolve().parents[1] / "candidate"))
sys.path.insert(0, str(REPO))

from framecodec import FrameDecoder, encode_frame, crc16  # noqa: E402


def all_splits(frame):
    """Every 1- and 2-cut split of `frame` into chunks."""
    n = len(frame)
    for i in range(n + 1):
        yield [frame[:i], frame[i:]]
    for i in range(n + 1):
        for j in range(i, n + 1):
            yield [frame[:i], frame[i:j], frame[j:]]


# ── B1: any chunking of one frame decodes identically ────────────────────────

@pytest.mark.parametrize("payload", [
    b"hello", b"", bytes([0x00, 0x01, 0x02]),
    bytes([0x7E]), bytes([0x7D]), bytes([0x7E, 0x7D, 0x7E, 0x7D]),
    bytes(range(256)),
])
def test_b1_any_split_equivalence(payload):
    frame = encode_frame(payload)
    for chunks in all_splits(frame):
        dec = FrameDecoder()
        out = []
        for c in chunks:
            out.extend(dec.feed(c))
        assert out == [payload], f"payload={payload!r} chunks={chunks!r} -> {out!r}"


# ── B2: a split inside the escape pair must not corrupt the payload ──────────

def test_b2_escape_split_inside_pair():
    payload = b"A\x7eB\x7dC"
    frame = encode_frame(payload)
    for i in range(len(frame) + 1):
        dec = FrameDecoder()
        out = dec.feed(frame[:i]) + dec.feed(frame[i:])
        assert out == [payload], f"cut={i} -> {out!r}"


# ── B3: a split inside the 2-byte length header ──────────────────────────────

def test_b3_partial_header():
    payload = b"payload-with-more-than-255-escaped-bytes" * 6
    frame = encode_frame(payload)
    # cut between SOF and the first length byte, and between the two length bytes
    for cut in (1, 2):
        dec = FrameDecoder()
        out = dec.feed(frame[:cut]) + dec.feed(frame[cut:])
        assert out == [payload], f"cut={cut} -> {len(out)} frames"


# ── B4: a frame split before its payload is complete ─────────────────────────

def test_b4_partial_payload_across_many_chunks():
    payload = bytes([0x7E, 0x11, 0x7D, 0x22] * 10)
    frame = encode_frame(payload)
    dec = FrameDecoder()
    out = []
    for b in frame:                       # byte-at-a-time
        out.extend(dec.feed(bytes([b])))
    assert out == [payload]


# ── B5: a corrupt frame is dropped and the next good frame survives ──────────

def test_b5_crc_failure_recovery():
    good = encode_frame(b"good")
    bad = bytearray(encode_frame(b"bad!"))
    bad[-1] ^= 0xFF                       # corrupt the CRC high byte
    dec = FrameDecoder()
    assert dec.feed(bytes(bad)) == []
    assert dec.feed(good) == [b"good"]


def test_b5_crc_failure_same_chunk():
    good = encode_frame(b"good")
    bad = bytearray(encode_frame(b"bad!"))
    bad[-1] ^= 0xFF
    dec = FrameDecoder()
    assert dec.feed(bytes(bad) + good) == [b"good"]


# ── B6: a truncated frame interrupted by a new SOF resynchronizes ────────────

def test_b6_truncated_then_new_frame():
    truncated = encode_frame(b"abcdef")[:-3]   # missing tail of body + crc
    nxt = encode_frame(b"next")
    dec = FrameDecoder()
    out = dec.feed(truncated + nxt)
    assert out == [b"next"], out


def test_b6_truncated_then_new_frame_split():
    truncated = encode_frame(b"abcdef")[:-3]
    nxt = encode_frame(b"next")
    stream = truncated + nxt
    for cut in range(len(stream) + 1):
        dec = FrameDecoder()
        out = dec.feed(stream[:cut]) + dec.feed(stream[cut:])
        assert out == [b"next"], f"cut={cut} -> {out!r}"


# ── B7: several frames in one chunk, plus a trailing partial ─────────────────

def test_b7_many_frames_one_chunk_plus_partial():
    f1, f2, f3 = encode_frame(b"one"), encode_frame(b"two"), encode_frame(b"three")
    stream = f1 + f2 + f3
    dec = FrameDecoder()
    out = dec.feed(stream + f1[:4])
    assert out == [b"one", b"two", b"three"]
    out2 = dec.feed(f1[4:])
    assert out2 == [b"one"]


# ── B8: empty chunk is a no-op and carries no state ──────────────────────────

def test_b8_empty_chunk_noop():
    dec = FrameDecoder()
    assert dec.feed(b"") == []
    frame = encode_frame(b"x")
    assert dec.feed(frame[:2]) == []
    assert dec.feed(b"") == []
    assert dec.feed(frame[2:]) == [b"x"]


# ── B9: decoder instances are independent (no shared state) ──────────────────

def test_b9_decoder_independence():
    d1, d2 = FrameDecoder(), FrameDecoder()
    f1, f2 = encode_frame(b"aaa"), encode_frame(b"bbb")
    d1.feed(f1[:3])                       # d1 holds a partial frame
    assert d2.feed(f2) == [b"bbb"], "state leaked between decoder instances"
    assert d1.feed(f1[3:]) == [b"aaa"]
