"""Bundle a custom competition implementation as a private offline Notebook."""

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.experiments import entry_path, load_config, python_sources, validate_slug


def prepare(root: Path, slug: str, owner: str, entry: str = "src/experiment.py",
            config_path: str = "config.json", name: str = "baseline", device: str = "cpu",
            submission_file: str | None = None) -> Path:
    validate_slug(slug)
    validate_slug(name)
    if not re.fullmatch(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*", owner):
        raise ValueError("owner must be your Kaggle username")
    if device not in {"cpu", "cuda"}:
        raise ValueError("Notebook device must be cpu or cuda")
    if submission_file and (Path(submission_file).name != submission_file or submission_file in {".", ".."}):
        raise ValueError("submission-file must be a filename, not a path")
    competition = root / "competitions" / slug
    entry_path(competition, entry)
    config = load_config(competition, config_path)
    config["device"] = device
    sources = python_sources(root, competition)
    # Package markers prevent namespace conflicts and support relative imports.
    sources.setdefault("competitions/__init__.py", "")
    sources.setdefault(f"competitions/{slug}/__init__.py", "")
    sources.setdefault(f"competitions/{slug}/src/__init__.py", "")
    code = (
        "from pathlib import Path\nimport sys\n"
        f"SOURCES = {sources!r}\nCONFIG = {config!r}\n"
        "ROOT = Path('/kaggle/working/workspace')\n"
        "for relative, text in SOURCES.items():\n"
        "    path = ROOT / relative\n    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    path.write_text(text)\n"
        "sys.path.insert(0, str(ROOT))\n"
        "from harness.experiments import execute\n"
        "from datetime import datetime, timezone\n"
        "run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')\n"
        f"OUTPUT = Path('/kaggle/working/experiments') / {name!r} / run_id\n"
        f"result = execute(ROOT, {slug!r}, {entry!r}, CONFIG, {name!r}, Path('/kaggle/input'), OUTPUT)\n"
        "print(result['metrics'])\n"
    )
    if submission_file:
        code += (
            "# Keep the Code Competition output at a stable path during reruns.\n"
            "import shutil\n"
            f"shutil.copyfile(OUTPUT / {submission_file!r}, Path('/kaggle/working') / {submission_file!r})\n"
        )
    notebook = {"nbformat": 4, "nbformat_minor": 4,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": [{"cell_type": "markdown", "metadata": {}, "source": [
            f"# {slug}: {name}\nGenerated from competition Python sources and experiment config. "
            "Private offline Notebook; competition submission is a separate operation."]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [code]}]}
    destination = root / "runs" / slug / "notebooks" / name
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "experiment.ipynb").write_text(json.dumps(notebook, indent=2) + "\n")
    kernel_slug = f"{slug}-{name}"
    metadata = {"id": f"{owner}/{kernel_slug}", "title": kernel_slug.replace("-", " "),
        "code_file": "experiment.ipynb", "language": "python", "kernel_type": "notebook",
        "is_private": "true", "enable_gpu": "true" if device == "cuda" else "false",
        "enable_internet": "false", "competition_sources": [slug], "dataset_sources": [],
        "kernel_sources": [], "model_sources": []}
    if device == "cuda":
        metadata["machine_shape"] = "NvidiaTeslaT4"
    (destination / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Prepared locally: {destination}")
    print(f"Notebook ID: {metadata['id']}")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--entry", default="src/experiment.py")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--name", default="baseline")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--submission-file", help="Copy this output filename to /kaggle/working for Code Competition submission")
    args = parser.parse_args()
    prepare(ROOT, args.competition, args.owner, args.entry, args.config, args.name, args.device, args.submission_file)
