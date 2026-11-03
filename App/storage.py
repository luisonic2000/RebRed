"""Atomic local persistence with a validated recovery copy."""
import json
import os
from pathlib import Path


def read_database(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("profiles"), list) or not isinstance(value.get("history"), list):
        raise ValueError("Invalid planner database")
    return value


def write_database(path, data):
    path = Path(path)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    backup = path.with_suffix(path.suffix + ".bak")
    if path.exists():
        try:
            previous = read_database(path)
        except (OSError, ValueError):
            pass  # Keep the last valid backup if the current file is damaged.
        else:
            recovery = backup.with_suffix(backup.suffix + ".tmp")
            recovery.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(recovery, backup)
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def read_with_recovery(path):
    try:
        return read_database(path), False
    except (OSError, ValueError):
        return read_database(Path(path).with_suffix(Path(path).suffix + ".bak")), True
