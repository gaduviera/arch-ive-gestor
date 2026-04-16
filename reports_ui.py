"""Reports UI widgets — HeatmapCanvas and ComparisonCanvas."""
import tkinter as tk
import calendar
from theme import COLORS

_BG     = COLORS["carbon_base"]
_PANEL  = COLORS["carbon_elevated"]
_GOLD   = COLORS["gold_primary"]
_TEXT   = COLORS["platinum"]
_MUTED  = COLORS["silver"]
_SMOKE  = COLORS["smoke"]

# Heatmap intensity palette (0 events → 4+ events)
_HEAT_PALETTE = ["#1A1A1A", "#2A2010", "#4A3A1A", "#9A7F42", "#C6A85E"]


def _heat_color(count: int) -> str:
    idx = min(count, len(_HEAT_PALETTE) - 1)
    return _HEAT_PALETTE[idx]


class HeatmapCanvas(tk.Canvas):
    """Monthly backup-frequency heatmap (calendar grid)."""

    CELL = 28      # cell size in pixels
    PAD  = 8

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", _BG)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, **kwargs)
        self._data: dict[str, int] = {}   # "YYYY-MM-DD" → count
        self._year = 2026
        self._month = 1

    def update_data(self, data: dict, year: int, month: int):
        self._data = data
        self._year = year
        self._month = month
        self.draw()

    def draw(self):
        self.delete("all")
        year, month = self._year, self._month
        p = self.PAD
        c = self.CELL

        # Day-of-week headers
        for i, dow in enumerate(["L", "M", "X", "J", "V", "S", "D"]):
            x = p + i * (c + 2) + c // 2
            self.create_text(x, p + 8, text=dow, fill=_MUTED,
                             font=("Segoe UI", 8), tags="heatmap")

        # Cells
        first_dow, num_days = calendar.monthrange(year, month)
        # Python: Mon=0, we want Mon first
        for day in range(1, num_days + 1):
            key = f"{year}-{month:02d}-{day:02d}"
            count = self._data.get(key, 0)
            col = (first_dow + day - 1) % 7
            row = (first_dow + day - 1) // 7

            x0 = p + col * (c + 2)
            y0 = p + 24 + row * (c + 2)
            x1, y1 = x0 + c, y0 + c

            color = _heat_color(count)
            self.create_rectangle(x0, y0, x1, y1, fill=color,
                                  outline=_PANEL, tags="heatmap")
            self.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                             text=str(day), fill=_TEXT if count > 0 else _SMOKE,
                             font=("Segoe UI", 8), tags="heatmap")


class ComparisonCanvas(tk.Canvas):
    """Side-by-side bar comparison of two periods."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", _BG)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, **kwargs)
        self._result: dict = {}
        self._label_a = "Período A"
        self._label_b = "Período B"

    def update_data(self, result: dict, label_a: str = "Período A",
                    label_b: str = "Período B"):
        self._result = result
        self._label_a = label_a
        self._label_b = label_b
        self.draw()

    def draw(self):
        self.delete("all")
        if not self._result:
            return

        w = self.winfo_width() or int(self.cget("width") or 400)
        h = self.winfo_height() or int(self.cget("height") or 200)
        p = 20

        a_total = self._result.get("period_a", {}).get("total", 0)
        b_total = self._result.get("period_b", {}).get("total", 0)
        delta   = self._result.get("delta", 0)
        delta_pct = self._result.get("delta_pct", 0)

        max_val = max(a_total, b_total, 1)
        bar_h_max = h - p * 4 - 20

        bar_w = (w - p * 3) // 2

        for i, (label, total, color) in enumerate([
            (self._label_a, a_total, "#9A7F42"),
            (self._label_b, b_total, _GOLD),
        ]):
            x0 = p + i * (bar_w + p)
            bar_h = int(bar_h_max * total / max_val) if max_val else 0
            y0 = h - p * 2 - bar_h
            y1 = h - p * 2

            self.create_rectangle(x0, y0, x0 + bar_w, y1,
                                  fill=color, outline="", tags="comp")
            self.create_text(x0 + bar_w // 2, y0 - 8,
                             text=f"{total:,.0f}", fill=_TEXT,
                             font=("Segoe UI", 9, "bold"), tags="comp")
            self.create_text(x0 + bar_w // 2, y1 + 12,
                             text=label, fill=_MUTED,
                             font=("Segoe UI", 8), tags="comp")

        # Delta label center
        sign = "+" if delta >= 0 else ""
        self.create_text(w // 2, p,
                         text=f"Δ {sign}{delta:,.0f}  ({sign}{delta_pct:.1f}%)",
                         fill=_GOLD if delta >= 0 else COLORS["error"],
                         font=("Segoe UI", 10, "bold"), tags="comp")
