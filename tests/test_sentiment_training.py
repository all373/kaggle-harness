"""Check holdout isolation, checkpoint scoring, and submission ID alignment."""

import csv
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch



ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'competitions/word2vec-nlp-tutorial/src/train.py').is_file():
    raise unittest.SkipTest("Private competition source is not present in this checkout")
from sklearn.metrics import roc_auc_score
TRAINING = importlib.import_module("competitions.word2vec-nlp-tutorial.src.train")


class SentimentTrainingTests(unittest.TestCase):
    def test_holdout_checkpoint_and_submission_alignment(self):
        config = json.loads((ROOT / "competitions/word2vec-nlp-tutorial/config.json").read_text())
        config.update(device="cpu", epochs=2, embedding_dim=8, hidden_dim=8, batch_size=8)
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data"
            data.mkdir()
            train_rows = [(f"id{i}", i % 2, f"{'good' if i % 2 else 'bad'} unique{chr(97 + i // 26)}{chr(97 + i % 26)}")
                          for i in range(40)]
            with (data / "labeledTrainData.tsv").open("w", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["id", "sentiment", "review"])
                writer.writerows(train_rows)
            with (data / "testData.tsv").open("w", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["id", "review"])
                writer.writerows([("test1", "good"), ("test2", "bad"), ("test3", "")])
            TRAINING.write_csv(data / "sampleSubmission.csv", ["id", "sentiment"],
                               [("test3", 0), ("test1", 0), ("test2", 0)])
            output = Path(tmp) / "run"
            metrics = TRAINING.run(config, data, output)
            split = json.loads((output / "split.json").read_text())
            self.assertFalse(set(split["train_ids"]) & set(split["validation_ids"]))
            self.assertEqual(len(split["train_ids"]), 32)
            self.assertEqual(len(split["validation_ids"]), 8)
            vocab = json.loads((output / "vocab.json").read_text())
            reviews = {row[0]: row[2] for row in train_rows}
            for identifier in split["validation_ids"]:
                self.assertNotIn(reviews[identifier].split()[1], vocab)
            with (output / "validation_predictions.csv").open() as f:
                predictions = list(csv.DictReader(f))
            auc = roc_auc_score([int(row["sentiment"]) for row in predictions],
                                [float(row["probability"]) for row in predictions])
            self.assertAlmostEqual(metrics["validation_roc_auc"], auc)
            with (output / "submission.csv").open() as f:
                submission = list(csv.DictReader(f))
            self.assertEqual([row["id"] for row in submission], ["test3", "test1", "test2"])
            self.assertTrue(all(0 <= float(row["sentiment"]) <= 1 for row in submission))
            self.assertTrue((output / "best-model.pt").is_file())
            with self.assertRaises(FileExistsError):
                TRAINING.run(config, data, output)

    def test_cuda_required_does_not_silently_fall_back(self):
        import torch
        with patch.object(torch.cuda, "is_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "CUDA required"):
                TRAINING.run({"seed": 42, "device": "cuda"}, Path("unused"), Path("unused"))


if __name__ == "__main__":
    unittest.main()
