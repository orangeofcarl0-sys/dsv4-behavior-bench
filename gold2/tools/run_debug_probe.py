"""Print diagnostic facts about the datapipe repo state."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    print(f"repo root: {ROOT}")
    git = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True)
    print(f"git status:\n{git.stdout or '(clean)'}")
    for catalog in (ROOT / "catalog.jsonl", ROOT / "transformed.jsonl"):
        if catalog.is_file():
            lines = [l for l in catalog.read_text(encoding="utf-8").splitlines() if l.strip()]
            print(f"{catalog.name}: {len(lines)} records")
            if lines:
                print(f"  first: {lines[0][:200]}")
        else:
            print(f"{catalog.name}: (missing)")
    public = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/public", "-q", "--tb=no"],
        cwd=ROOT, capture_output=True, text=True,
    )
    print(public.stdout[-1200:])
