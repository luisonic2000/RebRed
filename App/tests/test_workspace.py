import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from workspace import store_draft, get_draft
from community_evidence import apply_evidence


class WorkspaceTests(unittest.TestCase):
    def test_drawforme_requires_weekend_paid_offer_without_title_contact(self):
        profile = {"name": "DrawForMe", "rules": {}}
        apply_evidence(profile)
        self.assertEqual(profile["min_interval_hours"], 168)
        self.assertEqual(profile["rules"]["offer_days"], ["Sat", "Sun"])
        self.assertTrue(profile["rules"]["no_title_contact"])

    def test_dnd_requires_human_description(self):
        profile = {"name": "DnD", "rules": {}}
        apply_evidence(profile)
        self.assertEqual(profile["rules"]["min_body_chars"], 400)
        self.assertTrue(profile["rules"]["manual_description"])

    def test_drafts_are_isolated_by_artist_and_community(self):
        data = {}
        store_draft(data, "AnimeCommission", "Alice", "Alice title", "body", [])
        store_draft(data, "AnimeCommission", "Bob", "Bob title", "body", [])
        self.assertEqual(get_draft(data, "AnimeCommission", "Alice")["title"], "Alice title")
        self.assertEqual(get_draft(data, "AnimeCommission", "Bob")["title"], "Bob title")
        self.assertEqual(get_draft(data, "DnD", "Alice"), {})

    def test_rule_migration_keeps_previous_rules_and_custom_folder(self):
        profile = {"name": "AnimeCommission", "folder": "my/art", "rules": {"minimum_personal": 45}}
        apply_evidence(profile)
        apply_evidence(profile)
        self.assertEqual(profile["folder"], "my/art")
        self.assertEqual(profile["rules"]["minimum_personal"], 35)
        self.assertEqual(len(profile["previous_rule_packs"]), 1)
        self.assertEqual(profile["previous_rule_packs"][0]["minimum_personal"], 45)

    def test_unresearched_community_not_marked_verified(self):
        profile = {"name": "Example", "rules": {}}
        apply_evidence(profile)
        self.assertEqual(profile["rules"]["verification_status"], "unverified")


@unittest.skipUnless(sys.platform == "win32", "Windows Tk integration")
class WorkspaceWindowTests(unittest.TestCase):
    def test_switching_community_restores_edited_draft_and_collapses_options(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(app, "DATA_PATH", Path(folder) / "test.json"):
            root = app.PlannerApp()
            try:
                root.update()
                root.title_entry.insert(0, "My edited title")
                root.body_text.insert("1.0", "My edited description")
                root.load_profile(1)
                root.load_profile(0)
                self.assertEqual(root.title_entry.get(), "My edited title")
                self.assertEqual(root.body_text.get("1.0", "end").strip(), "My edited description")
                root.advanced_visible.set(False)
                root.toggle_advanced()
                root.advanced_visible.set(True)
                root.toggle_advanced()
                root.reset_layout()
                root.update()
                self.assertTrue(root.advanced_options.winfo_manager())
            finally:
                root.destroy()
