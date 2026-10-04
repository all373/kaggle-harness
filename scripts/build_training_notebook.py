"""Build the Kaggle training notebook from version-controlled Python and config."""

import json
from pathlib import Path


def build(competition: Path) -> Path:
    source = (competition / "src" / "train.py").read_text()
    config = json.loads((competition / "config.json").read_text())
    config["device"] = "cuda"
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            "# GPU sentiment baseline\n",
            "Train an EmbeddingBag classifier on a stratified 80/20 split. "
            "Save holdout ROC AUC, checkpoint, predictions, and submission files. "
            "Vocabulary is fitted on the training split only. "
            "Kaggle leaderboard submission is a separate step.\n",
            "Generated from `src/train.py` and `config.json`; edit those files for repository changes.",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "from pathlib import Path\nimport json\n",
            f"CONFIG = {config!r}\n",
            "print(json.dumps(CONFIG, indent=2))\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# Write and import the shared training implementation.\n",
            f"TRAINING_SOURCE = {source!r}\n",
            "import importlib.util\n",
            "module_path = Path('/kaggle/working/train.py')\n",
            "module_path.write_text(TRAINING_SOURCE)\n",
            "spec = importlib.util.spec_from_file_location('sentiment_training', module_path)\n",
            "training = importlib.util.module_from_spec(spec)\n",
            "spec.loader.exec_module(training)\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "from datetime import datetime, timezone\n",
            "RUN_ID = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')\n",
            "OUTPUT_DIR = Path('/kaggle/working') / RUN_ID\n",
            "metrics = training.run(CONFIG, Path('/kaggle/input'), OUTPUT_DIR)\n",
            "print('Artifacts:', OUTPUT_DIR)\n",
        ]},
    ]
    notebook = {"nbformat": 4, "nbformat_minor": 4, "cells": cells,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}}
    destination = competition / "notebooks" / "gpu-train.ipynb"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(notebook, indent=2) + "\n")
    return destination


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(build(root / "competitions" / "word2vec-nlp-tutorial"))
