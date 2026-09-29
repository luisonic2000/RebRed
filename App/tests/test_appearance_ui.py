"""Window-level appearance checks; run with a desktop or virtual display."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import app  # noqa: E402


@unittest.skipUnless(
    os.name == "nt" or os.environ.get("DISPLAY"),
    "A graphical Tk display is required.",
)
class AppearanceWindowTests(unittest.TestCase):
    def test_palette_switch_and_appearance_dialog_persist_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_path = Path(temporary_directory) / "rebred_data.json"
            with patch.object(app, "DATA_PATH", data_path):
                root = app.PlannerApp()
                try:
                    root.state("normal")
                    root.geometry("980x650")
                    root.update()
                    self.assertEqual(root.profile_list.size(), 33)

                    for theme in (
                        "adwaita-dark",
                        "catppuccin-mocha",
                        "nord",
                        "dracula",
                        "light",
                    ):
                        root.ui_theme = theme
                        root.apply_ui_theme()
                        root.update_idletasks()

                    def apply_test_settings() -> None:
                        dialogs = [
                            widget for widget in root.winfo_children()
                            if isinstance(widget, app.AppearanceDialog)
                        ]
                        self.assertEqual(len(dialogs), 1)
                        dialog = dialogs[0]
                        dialog.theme_var.set("Nord")
                        dialog.scale_var.set("120%")
                        dialog.density_var.set("Compact")
                        dialog.motion_var.set(False)
                        dialog.accent_color = "#123abc"
                        dialog.save()

                    root.after(100, apply_test_settings)
                    root.open_appearance()
                    root.update_idletasks()

                    saved = json.loads(data_path.read_text(encoding="utf-8"))
                    self.assertEqual(saved["ui_theme"], "nord")
                    self.assertEqual(saved["ui_accent_color"], "#123abc")
                    self.assertEqual(saved["ui_font_scale"], 1.2)
                    self.assertEqual(saved["ui_density"], "compact")
                    self.assertIs(saved["ui_reduce_motion"], False)
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
