"""Run any competition implementation locally with isolated experiment outputs."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.experiments import execute, load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition")
    parser.add_argument("--entry", default="src/experiment.py")
    parser.add_argument("--config", default="config.json", help="Path relative to the competition")
    parser.add_argument("--name", default="baseline")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--data-dir", type=Path, help="Optional local input directory")
    args = parser.parse_args()
    from harness.experiments import validate_slug
    validate_slug(args.competition)
    config = load_config(ROOT / "competitions" / args.competition, args.config)
    if args.device:
        config["device"] = args.device
    result = execute(ROOT, args.competition, args.entry, config, args.name, args.data_dir)
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
