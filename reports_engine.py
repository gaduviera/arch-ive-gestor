"""Reports engine — backup history storage and analytics."""
import json
import os
from datetime import datetime
from pathlib import Path


class BackupHistoryManager:
    """Append-only JSON log of backup events."""

    def __init__(self, log_path: str = "logs/backup_history.json"):
        self.log_path = log_path
        self._history: list[dict] = self._load()

    def _load(self) -> list[dict]:
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save(self):
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self._history, f, ensure_ascii=False,
                      indent=2, default=str)

    def append_event(self, event: dict):
        """Add an event with an auto-generated timestamp and persist."""
        record = {"timestamp": datetime.now().isoformat(), **event}
        self._history.append(record)
        self._save()

    def get_events(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        """Return events optionally filtered by date range (inclusive)."""
        result = []
        for ev in self._history:
            if start_date is None and end_date is None:
                result.append(ev)
                continue
            try:
                ts = datetime.fromisoformat(ev["timestamp"])
            except (KeyError, ValueError):
                continue
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            result.append(ev)
        return result

    def get_summary(self) -> dict:
        """Return total count and first/last event timestamps."""
        if not self._history:
            return {"total_events": 0, "first_event": None, "last_event": None}
        timestamps = [ev.get("timestamp") for ev in self._history
                      if ev.get("timestamp")]
        return {
            "total_events": len(self._history),
            "first_event":  min(timestamps) if timestamps else None,
            "last_event":   max(timestamps) if timestamps else None,
        }


class ReportsCalculator:
    """Analytics computed from BackupHistoryManager data."""

    def __init__(self, history_manager: BackupHistoryManager):
        self._hm = history_manager

    def compute_heatmap(self, year: int, month: int) -> dict[str, int]:
        """Return {'YYYY-MM-DD': count} for events in the given year/month."""
        counts: dict[str, int] = {}
        for ev in self._hm.get_events():
            ts_str = ev.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except ValueError:
                continue
            if ts.year == year and ts.month == month:
                key = ts.strftime("%Y-%m-%d")
                counts[key] = counts.get(key, 0) + 1
        return counts

    def compute_monthly_totals(self, year: int) -> dict[str, int]:
        """Return {'YYYY-MM': count} for every month in the given year."""
        counts: dict[str, int] = {}
        for ev in self._hm.get_events():
            ts_str = ev.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except ValueError:
                continue
            if ts.year == year:
                key = ts.strftime("%Y-%m")
                counts[key] = counts.get(key, 0) + 1
        return counts

    def compute_comparison(
        self,
        event_key: str,
        period_a_start: datetime,
        period_a_end: datetime,
        period_b_start: datetime,
        period_b_end: datetime,
    ) -> dict:
        """Compare sum of event_key between two date periods."""

        def _aggregate(start, end):
            values = []
            for ev in self._hm.get_events(start_date=start, end_date=end):
                val = ev.get(event_key)
                if val is not None:
                    try:
                        values.append(float(val))
                    except (TypeError, ValueError):
                        pass
            total = sum(values)
            count = len(values)
            avg   = total / count if count else 0.0
            return {"total": total, "count": count, "avg": avg}

        a = _aggregate(period_a_start, period_a_end)
        b = _aggregate(period_b_start, period_b_end)
        delta = b["total"] - a["total"]
        delta_pct = (delta / a["total"] * 100) if a["total"] != 0 else 0.0

        return {
            "period_a":  a,
            "period_b":  b,
            "delta":     delta,
            "delta_pct": delta_pct,
        }

    def recoverable_space(self, duplicate_groups: list[dict]) -> int:
        """Return bytes recoverable by deleting duplicate copies.

        Each group must have keys: 'size' (int) and 'paths' (list[str]).
        """
        total = 0
        for group in duplicate_groups:
            size   = group.get("size", 0)
            copies = len(group.get("paths", []))
            if copies > 1:
                total += size * (copies - 1)
        return total
