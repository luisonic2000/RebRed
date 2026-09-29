"""Headless tests for persisted appearance settings and semantic palettes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import app  # noqa: E402


class AppearanceSettingsTests(unittest.TestCase):
    def test_new_install_uses_adwaita_dark_and_comfortable_defaults(self) -> None:
        settings = app.normalize_appearance_preferences({})

        self.assertEqual(settings["ui_theme"], "adwaita-dark")
        self.assertEqual(settings["ui_density"], "comfortable")
        self.assertEqual(settings["ui_font_scale"], 1.0)
        self.assertTrue(settings["ui_reduce_motion"])

    def test_existing_dark_and_light_preferences_are_migrated(self) -> None:
        self.assertEqual(
            app.normalize_appearance_preferences({"ui_theme": "dark"})["ui_theme"],
            "adwaita-dark",
        )
        self.assertEqual(
            app.normalize_appearance_preferences({"ui_theme": "light"})["ui_theme"],
            "light",
        )

    def test_all_supported_palette_choices_return_semantic_color_tokens(self) -> None:
        for theme_name in ("adwaita-dark", "catppuccin-mocha", "nord", "dracula", "light"):
            with self.subTest(theme=theme_name):
                palette = app.theme_palette(theme_name, "#ee6677")
                for token in (
                    "background", "surface", "surface_raised", "border",
                    "text_primary", "text_secondary", "accent",
                    "accent_hover", "success", "warning", "danger",
                ):
                    self.assertRegex(palette[token], r"^#[0-9a-fA-F]{6}$")
                self.assertEqual(palette["accent"], "#ee6677")

    def test_invalid_theme_density_scale_and_accent_fall_back_safely(self) -> None:
        settings = app.normalize_appearance_preferences({
            "ui_theme": "untrusted-theme",
            "ui_density": "microscopic",
            "ui_font_scale": 80,
            "ui_accent_color": "url(https://example.invalid)",
            "ui_reduce_motion": "no",
        })

        self.assertEqual(settings["ui_theme"], "adwaita-dark")
        self.assertEqual(settings["ui_density"], "comfortable")
        self.assertEqual(settings["ui_font_scale"], 1.0)
        self.assertEqual(settings["ui_accent_color"], app.THEME_ACCENTS["adwaita-dark"])
        self.assertTrue(settings["ui_reduce_motion"])

    def test_custom_accessible_preferences_are_preserved(self) -> None:
        settings = app.normalize_appearance_preferences({
            "ui_theme": "nord",
            "ui_density": "compact",
            "ui_font_scale": 1.2,
            "ui_accent_color": "#123abc",
            "ui_reduce_motion": False,
        })

        self.assertEqual(settings, {
            "ui_theme": "nord",
            "ui_density": "compact",
            "ui_font_scale": 1.2,
            "ui_accent_color": "#123abc",
            "ui_reduce_motion": False,
        })


if __name__ == "__main__":
    unittest.main()
