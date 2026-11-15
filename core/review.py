"""Helpers to review a doubtful file pair before syncing (no UI, stdlib only)."""
from __future__ import annotations

import difflib
import os

TEXT_EXT = {".txt", ".md", ".csv", ".json", ".py", ".log", ".xml", ".html", ".ini", ".yml", ".yaml"}
MAX_TEXT = 1_000_000  # bytes; bigger files are only opened externally


def is_text(path: str) -> bool:
    try:
        return os.path.splitext(path)[1].lower() in TEXT_EXT and os.path.getsize(path) <= MAX_TEXT
    except OSError:
        return False


def _lines(path: str) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def diff_text(dest_path: str, source_path: str, max_lines: int = 2000) -> str:
    """Unified diff destination -> source. Empty string when contents are identical."""
    out = list(difflib.unified_diff(_lines(dest_path), _lines(source_path),
                                    "destino", "origen", lineterm=""))
    if len(out) > max_lines:
        out = out[:max_lines] + [f"… (diff recortado a {max_lines} líneas)"]
    return "\n".join(out)
