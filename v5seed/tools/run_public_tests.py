"""Run the public test suite against the datapipe package."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/public", "-q", "--tb=short"],
        cwd=ROOT,
    )
    sys.exit(result.returncode)
