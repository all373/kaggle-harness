"""Create a competition directory from the tracked template."""

import argparse
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="Competition slug, e.g. titanic")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        parser.error("slug must use lowercase letters, numbers and single hyphens")
    target = ROOT / "competitions" / args.slug
    if target.exists():
        parser.error(f"directory already exists: {target}")
    shutil.copytree(ROOT / "competitions" / "_template", target)
    for name in ("README.md", "config.json"):
        path = target / name
        path.write_text(path.read_text().replace("__SLUG__", args.slug))
    print(f"Created {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
