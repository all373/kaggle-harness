"""Small, framework-independent helpers for competition inputs and artifacts."""

import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, fields, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def find_file(root: Path, name: str) -> Path:
    paths = sorted(Path(root).rglob(name))
    if len(paths) != 1:
        raise FileNotFoundError(f"Expected one {name} below {root}; found {len(paths)}")
    return paths[0]


def read_rows(root: Path, name: str) -> list[dict]:
    """Read a CSV/TSV, including a same-named file inside its ZIP archive."""
    files = sorted(root.rglob(name))
    archives = sorted(root.rglob(name + ".zip"))
    delimiter = "," if name.endswith(".csv") else "\t"
    if files:
        with files[0].open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream, delimiter=delimiter))
    if archives:
        with zipfile.ZipFile(archives[0]) as archive:
            with io.TextIOWrapper(archive.open(name), encoding="utf-8", newline="") as stream:
                return list(csv.DictReader(stream, delimiter=delimiter))
    raise FileNotFoundError(f"Missing {name} below {root}")


def source_digest(folder: Path) -> str:
    """Fingerprint all Python modules in a pipeline, rather than its thin entry."""
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*.py")):
        if "__pycache__" not in path.parts:
            digest.update(path.relative_to(folder).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()
