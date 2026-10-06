import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location("submission_details", Path(__file__).resolve().parents[1] / "scripts/kaggle_submission_details.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SubmissionDetailsTests(unittest.TestCase):
    def test_complete_with_error_is_scoring_failure(self):
        response = SimpleNamespace(ref=123, status="COMPLETE", error_description="Notebook threw exception",
                                   public_score="", description="test", url="/submissions/123")
        result = module.details(response)
        self.assertTrue(result["scoring_failed"])
        self.assertEqual(result["error_description"], "Notebook threw exception")

    def test_pending_with_no_error_is_not_declared_failed(self):
        response = SimpleNamespace(ref=123, status="PENDING", error_description="",
                                   public_score="", description="test", url="/submissions/123")
        result = module.details(response)
        self.assertFalse(result["scoring_failed"])
        self.assertEqual(result["status"], "PENDING")

    def test_explicit_error_status_is_failure_even_without_message(self):
        response = SimpleNamespace(ref=123, status="SubmissionStatus.ERROR", error_description="",
                                   public_score="", description="test", url="/submissions/123")
        self.assertTrue(module.details(response)["scoring_failed"])
