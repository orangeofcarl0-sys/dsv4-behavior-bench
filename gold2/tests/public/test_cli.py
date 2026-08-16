import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_cli(workdir, *args):
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(REPO) + (os.pathsep + existing if existing else "")
    return subprocess.run(
        [sys.executable, "-m", "datapipe.cli", *args],
        cwd=workdir,
        env=env,
        capture_output=True,
        text=True,
    )


def write_input(workdir):
    src = workdir / "input.csv"
    src.write_text(
        "device_id,timestamp,temp,humidity\n"
        "ab-1,2026-08-01T10:00:00Z,22.5,45\n"
        "cd-2,2026-08-01T10:05:00Z,23.1,50\n",
        encoding="utf-8",
    )
    return src


def test_cli_full_pipeline(workdir):
    src = write_input(workdir)
    r1 = run_cli(workdir, "ingest", str(src))
    assert r1.returncode == 0, r1.stderr
    r2 = run_cli(workdir, "transform")
    assert r2.returncode == 0, r2.stderr
    r3 = run_cli(workdir, "emit", "--format", "json")
    assert r3.returncode == 0, r3.stderr
    assert '"count": 2' in r3.stdout


def test_cli_output_flag(workdir):
    src = write_input(workdir)
    run_cli(workdir, "ingest", str(src))
    run_cli(workdir, "transform")
    out = workdir / "report.json"
    r = run_cli(workdir, "emit", "--format", "json", "--output", str(out))
    assert r.returncode == 0, r.stderr
    assert out.is_file()


def test_cli_format_case_insensitive(workdir):
    src = write_input(workdir)
    run_cli(workdir, "ingest", str(src))
    run_cli(workdir, "transform")
    r = run_cli(workdir, "emit", "--format", "JSON")
    assert r.returncode == 0, r.stderr


def test_cli_missing_input_exit_code(workdir):
    r = run_cli(workdir, "ingest", str(workdir / "nope.csv"))
    assert r.returncode == 1


def test_cli_summary_flag(workdir):
    src = write_input(workdir)
    run_cli(workdir, "ingest", str(src))
    run_cli(workdir, "transform")
    r = run_cli(workdir, "emit", "--format", "md", "--summary")
    assert r.returncode == 0, r.stderr
    assert "## Summary" in r.stdout


def test_cli_filter_wired(workdir):
    src = write_input(workdir)
    run_cli(workdir, "ingest", str(src))
    r = run_cli(workdir, "transform", "--filter", "temp>23")
    assert r.returncode == 0, r.stderr
    out = workdir / "transformed.jsonl"
    rows = [l for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 1


def test_cli_unit_wired(workdir):
    src = write_input(workdir)
    run_cli(workdir, "ingest", str(src))
    r = run_cli(workdir, "transform", "--unit", "f")
    assert r.returncode == 0, r.stderr
    out = workdir / "transformed.jsonl"
    assert "72.5" in out.read_text(encoding="utf-8")
