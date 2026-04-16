"""JSON exporter for backup history reports."""
import json
from typing import Optional


def export_events_json(events: list[dict], filepath: Optional[str] = None,
                       indent: int = 2) -> str:
    """Export backup events to JSON string (or file if filepath given)."""
    content = json.dumps(events, ensure_ascii=False, indent=indent,
                         default=str)
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    return content


def export_summary_json(summary: dict, filepath: Optional[str] = None,
                        indent: int = 2) -> str:
    """Export a summary/report dict to JSON string (or file if filepath given)."""
    content = json.dumps(summary, ensure_ascii=False, indent=indent,
                         default=str)
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    return content
