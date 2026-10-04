"""Public suite for framecodec (do not modify).

Covers the happy paths the team relies on. It is intentionally small: it does
not exercise chunk-boundary splits, escape splitting, CRC recovery, or decoder
independence.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from framecodec import FrameDecoder, encode_frame, crc16


def test_crc_known_vector():
    # CRC-16/CCITT-FALSE of "123456789" is 0x29B1.
    assert crc16(b"123456789") == 0x29B1


def test_roundtrip_whole_frame():
    dec = FrameDecoder()
    assert dec.feed(encode_frame(b"hello")) == [b"hello"]


def test_multiple_frames_one_chunk():
    dec = FrameDecoder()
    assert dec.feed(encode_frame(b"a") + encode_frame(b"b")) == [b"a", b"b"]


def test_empty_payload():
    dec = FrameDecoder()
    assert dec.feed(encode_frame(b"")) == [b""]


def test_garbage_before_first_sof_ignored():
    dec = FrameDecoder()
    assert dec.feed(b"\x00\x01\x02" + encode_frame(b"ok")) == [b"ok"]


def test_escaped_payload_roundtrip():
    dec = FrameDecoder()
    payload = bytes([0x7E, 0x7D, 0x00, 0xFF])
    assert dec.feed(encode_frame(payload)) == [payload]
