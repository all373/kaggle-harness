"""Implement your own model, validation, and submission generation here."""

from pathlib import Path


def run(config: dict, data_dir: Path, output_dir: Path) -> dict:
    """Create outputs below output_dir and return JSON-serializable metrics.

    data_dir is the local data directory or /kaggle/input on Kaggle.
    output_dir is a NEW path allocated for this experiment, not an existing folder.
    Read data, split it appropriately, fit your model, score it, and save predictions.
    Use config["seed"] and config["device"] where relevant.
    Return measured values, for example {"validation_roc_auc": float(score)}.
    """
    raise NotImplementedError("Implement run() in your competition's src/experiment.py")
