import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from datapipe import ingest as ingest_mod
from datapipe import transform as transform_mod
from datapipe import emit as emit_mod


@pytest.fixture()
def workdir(tmp_path):
    return tmp_path


def run_ingest(workdir, content, name="input.csv"):
    src = workdir / name
    src.write_text(content, encoding="utf-8")
    out = workdir / "catalog.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    return out, accepted, skipped


def read_jsonl(path):
    return [json.loads(ln) for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]
