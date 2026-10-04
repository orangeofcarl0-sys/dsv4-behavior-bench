import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("CANDIDATE_REPO",
                           Path(__file__).resolve().parents[1] / "candidate"))
sys.path.insert(0, str(REPO))
