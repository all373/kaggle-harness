"""Run a private Kaggle GPU notebook, collect metrics, and optionally submit once."""

import argparse
import csv
from datetime import datetime, timezone
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

from kaggle_helpers import cli


ROOT = Path(__file__).resolve().parents[1]


def validate_submission(path: Path, metrics: dict) -> None:
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["id", "sentiment"]:
            raise ValueError("Submission must have id,sentiment columns")
        rows = list(reader)
    if len(rows) != metrics["test_rows"] or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Submission row count or ID uniqueness failed")
    if not all(math.isfinite(float(row["sentiment"])) and 0 <= float(row["sentiment"]) <= 1 for row in rows):
        raise ValueError("Submission probabilities must be finite and within [0,1]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--resume", action="store_true", help="Collect an already pushed Notebook; do not push again")
    parser.add_argument("--submit", action="store_true", help="Submit the generated CSV exactly once and fetch its score")
    parser.add_argument("--timeout", type=int, default=1800, help="Notebook runtime limit in seconds")
    args = parser.parse_args()
    for value in (args.competition, args.owner):
        if not re.fullmatch(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*", value):
            parser.error("competition and owner must be slugs")
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    reference = f"{args.owner}/{args.competition}-gpu-train"
    upload = ROOT / "runs" / args.competition / "kaggle-gpu-train"
    if not args.resume:
        subprocess.run([sys.executable, str(ROOT / "scripts/prepare_kaggle_notebook.py"),
                        args.competition, "--owner", args.owner, "--notebook", "gpu-train"], check=True)
        pushed = cli("kernels", "push", "-p", str(upload), "--timeout", str(args.timeout))
        print(pushed, flush=True)
        if "successfully pushed" not in pushed.lower():
            raise RuntimeError("Kaggle did not confirm the Notebook upload")
    deadline = time.monotonic() + args.timeout + 600
    while True:
        status = cli("kernels", "status", reference)
        print(status, flush=True)
        if '"KernelWorkerStatus.COMPLETE"' in status:
            break
        if any(word in status.upper() for word in ("ERROR", "CANCEL", "FAILED")):
            raise RuntimeError(f"Notebook failed: {status}")
        if time.monotonic() >= deadline:
            raise TimeoutError("Notebook still pending; resume later with --resume")
        time.sleep(20)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "runs" / args.competition / "kaggle-results" / run_id
    output.mkdir(parents=True, exist_ok=False)
    print(cli("kernels", "output", reference, "-p", str(output)), flush=True)
    metric_paths = list(output.rglob("metrics.json"))
    if len(metric_paths) != 1:
        raise RuntimeError("Expected exactly one training metrics.json from Notebook")
    artifact_dir = metric_paths[0].parent
    metrics = json.loads(metric_paths[0].read_text())
    print(json.dumps(metrics, indent=2), flush=True)
    submission = artifact_dir / "submission.csv"
    validate_submission(submission, metrics)
    summary = {"notebook": reference, "artifacts": str(artifact_dir.relative_to(ROOT)),
               "validation_roc_auc": metrics["validation_roc_auc"], "submitted": False}
    summary_path = output / "result.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    if args.submit:
        message = f"GPU EmbeddingBag baseline {run_id}"
        # Record intent before sending. Never retry a submission automatically.
        summary.update(submission_message=message, submission_state="requested")
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
        response = cli("competitions", "submit", args.competition,
                       "-f", str(submission), "-m", message)
        print(response, flush=True)
        summary["submission_response"] = response
        summary["submission_state"] = "sent"
        summary["submitted"] = True
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
        score_deadline = time.monotonic() + 600
        while True:
            text = cli("competitions", "submissions", args.competition, "--csv", "--page-size", "20")
            (output / "submissions.csv").write_text(text + "\n")
            matches = [row for row in csv.DictReader(io.StringIO(text)) if row.get("description") == message]
            if matches:
                row = matches[0]
                print(json.dumps(row), flush=True)
                summary["kaggle_submission"] = row
                summary_path.write_text(json.dumps(summary, indent=2) + "\n")
                score = row.get("publicScore", "")
                if score and score.lower() not in {"none", "null", "nan"}:
                    summary["submission_state"] = "scored"
                    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
                    print(f"Kaggle public score: {score}", flush=True)
                    break
                if any(word in row.get("status", "").upper() for word in ("ERROR", "FAILED")):
                    raise RuntimeError("Kaggle scoring failed; see result.json")
            if time.monotonic() >= score_deadline:
                print("Submitted once; score is pending. Check competitions submissions later.", flush=True)
                break
            time.sleep(20)
    print(f"Result: {summary_path.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
