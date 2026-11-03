import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage import write_database, read_with_recovery
from draft_rules import blocked_urls, unresolved_tokens, rule_review_due


class ReliabilityTests(unittest.TestCase):
    def test_corruption_recovers_previous_valid_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            original = {"profiles": [], "history": []}
            write_database(path, original)
            write_database(path, {"profiles": [], "history": [{"title": "new"}]})
            path.write_text("damaged", encoding="utf-8")
            self.assertEqual(read_with_recovery(path), (original, True))

    def test_tokens_detect_both_saved_formats(self):
        self.assertEqual(unresolved_tokens("Hi {links} {{price_block}}"), ["links", "price_block"])

    def test_domain_boundaries(self):
        text = "https://www.instagram.com/a https://notinstagram.com/a"
        self.assertEqual(blocked_urls(text, ["instagram.com"]), {"https://www.instagram.com/a"})

    def test_unverified_rules_are_not_presented_as_checked(self):
        self.assertTrue(rule_review_due({"last_reviewed": "2026-11-03"}))
