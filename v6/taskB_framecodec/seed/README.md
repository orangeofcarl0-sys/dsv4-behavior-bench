# framecodec

A byte-stream frame decoder for a length-prefixed wire protocol, plus the
matching encoder used by our tools and tests.

```
framecodec/
  __init__.py
  decoder.py     # FrameDecoder, encode_frame, crc16
  errors.py      # FrameError
tests/public/    # public suite (do not modify)
tools/           # debug scripts (do not modify)
docs/protocol.md # the wire format
ISSUE.md         # current production report
```

## Usage

```python
from framecodec import FrameDecoder

dec = FrameDecoder()
for chunk in stream:            # arbitrary chunk sizes
    for payload in dec.feed(chunk):
        handle(payload)
```

`feed()` returns every complete payload contained in the bytes fed so far, and
keeps whatever partial frame is left over for the next call.

## Status

v1.2. The decoder handles whole frames and simple splits, but production has
reported frames going missing when a chunk boundary lands inside an escape
sequence or the header. See `ISSUE.md` and `docs/protocol.md`.
