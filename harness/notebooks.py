"""Package a competition's Python modules for any Kaggle Notebook entry."""

from pathlib import Path

from harness.experiments import python_sources


def source_loader(root: Path, competition: Path, module: str) -> str:
    sources = python_sources(root, competition)
    slug = competition.name
    sources.setdefault("competitions/__init__.py", "")
    sources.setdefault(f"competitions/{slug}/__init__.py", "")
    sources.setdefault(f"competitions/{slug}/src/__init__.py", "")
    return (
        "from pathlib import Path\nimport sys\nimport importlib\n"
        f"SOURCES = {sources!r}\n"
        "ROOT = Path('/kaggle/working/workspace')\n"
        "for relative, text in SOURCES.items():\n"
        "    path = ROOT / relative\n    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    path.write_text(text, encoding='utf-8')\n"
        "sys.path.insert(0, str(ROOT))\n"
        f"implementation = importlib.import_module({module!r})\n"
    )
