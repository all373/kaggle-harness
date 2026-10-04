"""Run user-selected competition modules and record isolated experiments."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import time
from uuid import uuid4


def validate_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Use lowercase letters, numbers and single hyphens for slugs")
    return value


def entry_path(competition: Path, entry: str) -> Path:
    relative = Path(entry)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".py" or relative.parts[0] != "src":
        raise ValueError("entry must be a Python file under the competition's src/ directory")
    if any(not part.isidentifier() for part in relative.with_suffix("").parts):
        raise ValueError("Use Python module names for entry directories and filenames")
    path = competition / relative
    if not path.resolve().is_relative_to((competition / "src").resolve()) or not path.is_file():
        raise ValueError(f"Entry does not exist inside src/: {entry}")
    return path


def load_config(competition: Path, config_path: str = "config.json") -> dict:
    relative = Path(config_path)
    path = competition / relative
    if relative.is_absolute() or not path.resolve().is_relative_to(competition.resolve()):
        raise ValueError("config must be a path inside the competition directory")
    config = json.loads(path.read_text())
    if not isinstance(config, dict):
        raise ValueError("Experiment config must be a JSON object")
    return config


def python_sources(root: Path, competition: Path) -> dict[str, str]:
    """Explicit allowlist for code bundles, also used for provenance hashes."""
    sources = {}
    for folder in (competition / "src", root / "harness"):
        for path in sorted(folder.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
                raise ValueError(f"Source symlinks cannot be bundled: {path.name}")
            sources[path.relative_to(root).as_posix()] = path.read_text()
    return sources


def execute(root: Path, slug: str, entry: str, config: dict, name: str,
            data_dir: Path | None = None, output_dir: Path | None = None) -> dict:
    root = root.resolve()
    validate_slug(slug)
    validate_slug(name)
    competition = root / "competitions" / slug
    entry_path(competition, entry)
    if config.get("device", "auto") not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu or cuda")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:8]
    output = output_dir or root / "runs" / slug / "experiments" / name / run_id
    if output.exists():
        raise FileExistsError(f"Experiment output already exists: {output}")
    data = data_dir or root / config.get("data_dir", f"data/{slug}")
    sources = python_sources(root, competition)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    module_name = f"competitions.{slug}." + ".".join(Path(entry).with_suffix("").parts)
    module = importlib.import_module(module_name)
    if not callable(getattr(module, "run", None)):
        raise ValueError(f"{entry} must define run(config, data_dir, output_dir)")
    started = time.monotonic()
    metrics = module.run(deepcopy(config), data, output)
    if not isinstance(metrics, dict):
        raise ValueError("run() must return a dictionary of JSON-serializable metrics")
    result = {
        "competition": slug, "experiment": name, "entry": entry, "run_id": run_id,
        "config": config, "metrics": metrics, "elapsed_seconds": time.monotonic() - started,
        "data_dir": str(data), "output_dir": str(output),
        "source_sha256": {path: hashlib.sha256(text.encode()).hexdigest() for path, text in sources.items()},
    }
    serialized = json.dumps(result, indent=2, allow_nan=False)
    output.mkdir(parents=True, exist_ok=True)
    (output / "experiment.json").write_text(serialized + "\n")
    print(f"Experiment result: {output / 'experiment.json'}", flush=True)
    return result
