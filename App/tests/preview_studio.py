"""Isolated visual preview; never loads the user's portable settings."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="rebred-studio-preview-") as folder:
        app.DATA_PATH = Path(folder) / "preview.json"
        data = app.default_data()
        data["ui_language"] = "pt"
        data.update(app.normalize_appearance_preferences({"ui_theme": "studio-coral"}))
        app.write_database(app.DATA_PATH, data)
        root = app.PlannerApp()
        root.title("RebRed Studio · Prévia isolada")
        root.title_entry.insert(0, "Anime character illustrations and original characters")
        root.body_text.insert("1.0", "Hi! I’m a 2D illustrator available for character commissions.\n\nI draw original characters, fanart, character sheets and expressive portraits.\n\nPersonal commissions start at $45 USD.\n\nPortfolio\nVGen\nArtStation\n\nContact me with your idea, references and deadline.")
        root.validate()
        root.mainloop()
