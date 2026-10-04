"""Run Kaggle CLI with private workspace credentials, without printing them."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


CONFIG = Path(__file__).resolve().parents[1] / "config" / "kaggle.local.json"


def main() -> int:
    executable = shutil.which("kaggle")
    if executable is None:
        print("Install the CLI first: python -m pip install -r requirements-kaggle.txt", file=sys.stderr)
        return 1
    try:
        config = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        print("Create a valid config/kaggle.local.json from config/kaggle.example.json.", file=sys.stderr)
        return 1
    token = config.get("api_token") if isinstance(config, dict) else None
    if not isinstance(token, str) or not token.strip() or token.strip() == "YOUR_KAGGLE_API_TOKEN":
        print("Set api_token in config/kaggle.local.json to your Kaggle API token.", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = token.strip()
    # Keep conflicting legacy credentials out of this CLI invocation.
    env.pop("KAGGLE_USERNAME", None)
    env.pop("KAGGLE_KEY", None)
    return subprocess.call([executable, *sys.argv[1:]], env=env)


if __name__ == "__main__":
    sys.exit(main())
