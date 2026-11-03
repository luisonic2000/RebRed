import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from messages import translate_check


class TranslationTests(unittest.TestCase):
    def test_dynamic_minimum_is_translated_without_changing_amount(self):
        self.assertEqual(translate_check("Personal minimum is $35 USD.", "pt"), "O preço pessoal mínimo é US$ 35.")


@unittest.skipUnless(sys.platform == "win32", "Windows integration")
class DesktopTests(unittest.TestCase):
    def test_native_data_object_contains_existing_file_without_copy(self):
        import pythoncom
        import ctypes
        from windows_drag import create_file_data_object
        pythoncom.OleInitialize()
        try:
            data = create_file_data_object([Path(__file__)]).GetData((15, None, 1, -1, 1))
            self.assertIsNotNone(data)
        finally:
            ctypes.windll.ole32.OleUninitialize()

    def test_small_window_preserves_access_to_workspace(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(app, "DATA_PATH", Path(folder) / "test.json"):
            root = app.PlannerApp()
            try:
                root.state("normal")
                root.geometry("800x560")
                root.update()
                scroll = root.workspace_scroll
                self.assertGreater(scroll.content.winfo_height(), scroll.canvas.winfo_height())
                scroll.canvas.yview_moveto(1)
                root.update()
                self.assertGreater(scroll.canvas.yview()[0], 0)
            finally:
                root.destroy()
