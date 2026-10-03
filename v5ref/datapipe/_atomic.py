"""Atomic file writing helpers.

`fail` mode must never leave a partial output behind: either the whole file is
written, or the previous state of the path is untouched.
"""
import os
import tempfile
from pathlib import Path


def atomic_write_text(path, text):
    """Write `text` to `path` atomically (temp file + os.replace).

    On failure the temporary file is removed and `path` is left exactly as it
    was (absent stays absent, existing keeps its previous content).
    """
    target = Path(path)
    parent = target.parent if str(target.parent) else Path(".")
    fd, tmp = tempfile.mkstemp(dir=str(parent), prefix=".datapipe-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
