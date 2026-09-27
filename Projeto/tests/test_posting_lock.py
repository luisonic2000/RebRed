"""Headless tests for RebRed's local posting-protection behavior."""

from __future__ import annotations

import sys
import unittest
from datetime import timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import app  # noqa: E402


class PlannerHarness:
    """Small fake planner: no Tk window, browser, files, or network."""

    now_for = staticmethod(app.PlannerApp.now_for)
    last_posted_at = app.PlannerApp.last_posted_at
    repost_interval_hours = staticmethod(app.PlannerApp.repost_interval_hours)

    def __init__(self, profile: dict[str, object]) -> None:
        self.data = {
            "history": [
                {
                    "profile": profile["name"],
                    "created_at": self.now_for(profile).isoformat(),
                }
            ]
        }


class PostingProtectionTests(unittest.TestCase):
    def test_marked_post_uses_24_hour_lock_when_no_interval_is_configured(self) -> None:
        profile = {"name": "Demo", "min_interval_hours": 0, "timezone": "America/Sao_Paulo"}
        planner = PlannerHarness(profile)

        until = app.PlannerApp.repost_lock_until(planner, profile)

        self.assertIsNotNone(until)
        self.assertGreater(until - planner.now_for(profile), timedelta(hours=23, minutes=59))

    def test_marked_post_uses_community_interval_when_it_is_longer(self) -> None:
        profile = {"name": "Demo", "min_interval_hours": 48, "timezone": "America/Sao_Paulo"}
        planner = PlannerHarness(profile)

        until = app.PlannerApp.repost_lock_until(planner, profile)

        self.assertIsNotNone(until)
        self.assertGreater(until - planner.now_for(profile), timedelta(hours=47, minutes=59))


if __name__ == "__main__":
    unittest.main()
