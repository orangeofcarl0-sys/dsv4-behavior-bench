import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2] / "ablation-task" / "datapipe"
if "DATAPIPE_REPO" in os.environ:
    REPO = Path(os.environ["DATAPIPE_REPO"])
sys.path.insert(0, str(REPO))

from datapipe import ingest as ingest_mod
from datapipe import transform as transform_mod
from datapipe import emit as emit_mod


@pytest.fixture()
def workdir(tmp_path):
    return tmp_path


def write_jsonl(path, rows):
    path.write_text("\n".join(__import__("json").dumps(r) for r in rows) + "\n", encoding="utf-8")


def read_jsonl(path):
    return [__import__("json").loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
