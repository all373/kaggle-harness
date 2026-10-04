"""Prepare a private GPU notebook upload without copying local credentials."""

import argparse
import json
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition")
    parser.add_argument("--owner", required=True, help="Your Kaggle username")
    parser.add_argument("--notebook", choices=["gpu-check", "gpu-train"], default="gpu-check")
    args = parser.parse_args()
    for value in (args.competition, args.owner):
        if not re.fullmatch(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*", value):
            parser.error("competition and owner must be slugs, without paths")
    source = ROOT / "competitions" / args.competition / "notebooks" / f"{args.notebook}.ipynb"
    if args.notebook == "gpu-train":
        # Generate a self-contained notebook from the same source used locally.
        from build_training_notebook import build
        build(ROOT / "competitions" / args.competition)
    if not source.is_file():
        parser.error(f"Notebook does not exist: {source.relative_to(ROOT)}")
    destination = ROOT / "runs" / args.competition / f"kaggle-{args.notebook}"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination / source.name)
    metadata = {
        "id": f"{args.owner}/{args.competition}-{args.notebook}",
        "title": f"{args.competition} {args.notebook.replace('-', ' ').title()}",
        "code_file": source.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_internet": "false",
        "machine_shape": "NvidiaTeslaT4",
        "competition_sources": [args.competition],
        "dataset_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    (destination / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Prepared: {destination.relative_to(ROOT)}")
    print(f"Notebook: https://www.kaggle.com/code/{metadata['id']}")
    print("Only the notebook and metadata are prepared; no credentials or local data are copied.")


if __name__ == "__main__":
    main()
