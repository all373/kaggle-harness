"""Shared CLI invocation for competition-specific orchestration scripts."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def cli(*args: str) -> str:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/kaggle_cli.py"), *args],
                            cwd=ROOT, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout.strip()
