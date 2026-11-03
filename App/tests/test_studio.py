"""Studio is an optional complete workspace, sharing the same user data."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class StudioPreferencesTests(unittest.TestCase):
    def test_studio_palette_is_persistable_and_coral_by_default(self):
        settings = app.normalize_appearance_preferences({"ui_theme": "studio-coral"})
        self.assertEqual(settings["ui_theme"], "studio-coral")
        self.assertEqual(settings["ui_accent_color"], "#f47c6c")
        self.assertEqual(app.normalize_appearance_preferences({})["ui_theme"], "adwaita-dark")


@unittest.skipUnless(sys.platform == "win32", "Windows Tk integration")
class StudioWindowTests(unittest.TestCase):
    def test_live_switch_preserves_draft_images_and_restores_classic(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(app, "DATA_PATH", Path(folder) / "test.json"):
            root = app.PlannerApp()
            try:
                root.update()
                root.title_entry.insert(0, "Edited before theme switch")
                root.body_text.insert("1.0", "Keep my own text")
                image_path = Path(folder) / "sample.png"
                app.Image.new("RGB", (80, 50), "coral").save(image_path)
                root.profile["folder"] = folder
                root.selected_images = [image_path]

                def choose_theme(theme):
                    def apply():
                        dialog = next(child for child in root.winfo_children() if isinstance(child, app.AppearanceDialog))
                        dialog.theme_var.set(theme)
                        dialog.save()
                    root.after(100, apply)
                    root.open_appearance()
                    root.update()

                choose_theme("RebRed Studio · Coral")
                self.assertEqual(root.ui_accent_color, "#f47c6c")
                self.assertTrue(hasattr(root, "studio_editor"))
                self.assertEqual(root.title_entry.get(), "Edited before theme switch")
                self.assertEqual(root.body_text.get("1.0", "end").strip(), "Keep my own text")
                self.assertEqual(root.selected_images, [image_path])
                self.assertEqual(len(root._grid_photos), 1)
                self.assertFalse(root.studio_details.winfo_manager())
                root.toggle_studio_details()
                self.assertTrue(root.studio_details.winfo_manager())
                root.advanced_visible.set(True)
                root.toggle_studio_options()
                root.toggle_studio_file_list()
                root.update()
                self.assertEqual(root.image_list.winfo_manager(), "pack")
                root.toggle_ui_language()
                self.assertEqual(root.title_entry.get(), "Edited before theme switch")
                self.assertEqual(root.selected_images, [image_path])
                choose_theme("Nord")
                self.assertEqual(root.ui_theme, "nord")
                self.assertIn("vertical", root.workspace_panes)
                self.assertEqual(root.title_entry.get(), "Edited before theme switch")
                self.assertEqual(root.body_text.get("1.0", "end").strip(), "Keep my own text")
                saved = json.loads(app.DATA_PATH.read_text(encoding="utf-8"))
                self.assertIn("studio", saved["layouts"])
                self.assertIn("classic", saved["layouts"])
            finally:
                root.destroy()

    def test_saved_studio_starts_directly_in_new_workspace(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(app, "DATA_PATH", Path(folder) / "test.json"):
            data = app.default_data()
            data.update(app.normalize_appearance_preferences({"ui_theme": "studio-coral"}))
            app.write_database(app.DATA_PATH, data)
            root = app.PlannerApp()
            try:
                root.state("normal")
                root.geometry("1000x700")
                root.update()
                root.community_search_var.set("AnimeCommission")
                root.update()
                self.assertEqual(root.profile_list.size(), 1)
                root.validate()
                self.assertTrue(root.validation_summary_var.get())
            finally:
                root.destroy()
