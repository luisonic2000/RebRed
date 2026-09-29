"""Headless tests for the community picker and draft title counter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import app  # noqa: E402


class CommunitySearchTests(unittest.TestCase):
    def test_empty_query_keeps_original_profile_order(self) -> None:
        profiles = [{"name": "VGen"}, {"name": "Art Commission"}]

        self.assertEqual(app.filter_profile_indices(profiles, ""), [0, 1])

    def test_query_is_case_insensitive_and_matches_partial_names(self) -> None:
        profiles = [{"name": "VGen"}, {"name": "Art Commission"}, {"name": "DrawForMe"}]

        self.assertEqual(app.filter_profile_indices(profiles, "ART"), [1])

    def test_search_normalizes_accents_without_changing_profiles(self) -> None:
        profiles = [{"name": "Comissões"}, {"name": "VGen"}]

        self.assertEqual(app.filter_profile_indices(profiles, "comissoes"), [0])
        self.assertEqual([profile["name"] for profile in profiles], ["Comissões", "VGen"])


class DraftTitleCountTests(unittest.TestCase):
    def test_title_count_reports_remaining_characters(self) -> None:
        self.assertEqual(app.title_character_count("A title"), (7, 293))

    def test_title_count_flags_titles_over_reddit_limit(self) -> None:
        self.assertEqual(app.title_character_count("x" * 301), (301, -1))

    def test_title_count_accepts_the_exact_reddit_limit(self) -> None:
        self.assertEqual(app.title_character_count("x" * 300), (300, 0))


if __name__ == "__main__":
    unittest.main()
