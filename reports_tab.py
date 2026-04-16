"""Reports tab widget — analytics dashboard for Arch-Ive."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from theme import COLORS
from reports_ui import HeatmapCanvas, ComparisonCanvas
from components.chart_canvas import BarChart

_BG    = COLORS["carbon_base"]
_PANEL = COLORS["carbon_elevated"]
_GOLD  = COLORS["gold_primary"]
_TEXT  = COLORS["platinum"]
_MUTED = COLORS["silver"]

FONT_LABEL = ("Segoe UI", 9)
FONT_BTN   = ("Segoe UI", 9, "bold")
FONT_TITLE = ("Segoe UI", 11, "bold")


class ReportsTab(tk.Frame):
    """Full reports tab with heatmap, monthly chart, and export buttons.

    Parameters
    ----------
    parent : tk widget
    history_manager : BackupHistoryManager instance
    calculator : ReportsCalculator instance
    """

    def __init__(self, parent, history_manager=None, calculator=None):
        super().__init__(parent, bg=_BG)
        self._hm = history_manager
        self._calc = calculator
        self._current_year  = datetime.now().year
        self._current_month = datetime.now().month
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=_PANEL, pady=6, padx=12)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="Reportes & Analítica", font=FONT_TITLE,
                 fg=_GOLD, bg=_PANEL).pack(side="left")

        # Export buttons (right-aligned)
        for text, cmd in [
            ("Exportar CSV",  self._export_csv),
            ("Exportar JSON", self._export_json),
            ("Exportar PDF",  self._export_pdf),
        ]:
            tk.Button(toolbar, text=text, command=cmd,
                      font=FONT_BTN, fg=_GOLD, bg=_PANEL,
                      activeforeground=_BG, activebackground=_GOLD,
                      relief="flat", bd=0, padx=10, pady=4,
                      cursor="hand2").pack(side="right", padx=4)

        # ── Month navigation ──────────────────────────────────────────────────
        nav = tk.Frame(self, bg=_BG, pady=6, padx=12)
        nav.pack(fill="x")

        tk.Button(nav, text="◀", command=self._prev_month,
                  font=FONT_BTN, fg=_GOLD, bg=_PANEL,
                  relief="flat", bd=0, padx=8, pady=3,
                  cursor="hand2").pack(side="left")

        self._month_label = tk.Label(nav, text="", font=FONT_LABEL,
                                     fg=_TEXT, bg=_BG, width=16, anchor="center")
        self._month_label.pack(side="left", padx=6)

        tk.Button(nav, text="▶", command=self._next_month,
                  font=FONT_BTN, fg=_GOLD, bg=_PANEL,
                  relief="flat", bd=0, padx=8, pady=3,
                  cursor="hand2").pack(side="left")

        self._update_month_label()

        # ── Content: heatmap + monthly bar chart ──────────────────────────────
        content = tk.Frame(self, bg=_BG)
        content.pack(fill="both", expand=True, padx=12, pady=8)

        # Left: heatmap
        left = tk.Frame(content, bg=_PANEL)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(left, text="Actividad mensual", font=FONT_LABEL,
                 fg=_MUTED, bg=_PANEL).pack(anchor="w", padx=8, pady=(6, 0))

        self._heatmap = HeatmapCanvas(left, width=240, height=200)
        self._heatmap.pack(padx=8, pady=8)

        # Right: monthly totals bar chart
        right = tk.Frame(content, bg=_PANEL)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Backups por mes (año actual)", font=FONT_LABEL,
                 fg=_MUTED, bg=_PANEL).pack(anchor="w", padx=8, pady=(6, 0))

        self._bar_chart = BarChart(right, width=320, height=200)
        self._bar_chart.pack(padx=8, pady=8)

        # ── Stats row ─────────────────────────────────────────────────────────
        stats = tk.Frame(self, bg=_PANEL, pady=6, padx=12)
        stats.pack(fill="x", pady=(0, 8))

        self._total_lbl  = tk.Label(stats, text="Total eventos: —",
                                    font=FONT_LABEL, fg=_TEXT, bg=_PANEL)
        self._total_lbl.pack(side="left", padx=12)

        self._first_lbl  = tk.Label(stats, text="Primer backup: —",
                                    font=FONT_LABEL, fg=_MUTED, bg=_PANEL)
        self._first_lbl.pack(side="left", padx=12)

        self._last_lbl   = tk.Label(stats, text="Último backup: —",
                                    font=FONT_LABEL, fg=_MUTED, bg=_PANEL)
        self._last_lbl.pack(side="left", padx=12)

        self.refresh()

    # ── Data refresh ──────────────────────────────────────────────────────────

    def refresh(self):
        """Reload data from history manager and repaint all widgets."""
        if self._hm is None or self._calc is None:
            return

        # Heatmap
        heatmap_data = self._calc.compute_heatmap(
            self._current_year, self._current_month
        )
        self._heatmap.update_data(heatmap_data,
                                   self._current_year, self._current_month)

        # Monthly bar chart
        totals = self._calc.compute_monthly_totals(self._current_year)
        import calendar as cal
        months = [cal.month_abbr[m] for m in range(1, 13)]
        values = [totals.get(f"{self._current_year}-{m:02d}", 0)
                  for m in range(1, 13)]
        self._bar_chart.update_data(values, months)

        # Stats
        summary = self._hm.get_summary()
        self._total_lbl.config(
            text=f"Total eventos: {summary.get('total_events', 0)}"
        )
        first = summary.get("first_event") or "—"
        last  = summary.get("last_event")  or "—"
        self._first_lbl.config(text=f"Primer backup: {first[:10]}")
        self._last_lbl.config(text=f"Último backup: {last[:10]}")

    # ── Month nav ─────────────────────────────────────────────────────────────

    def _prev_month(self):
        if self._current_month == 1:
            self._current_year  -= 1
            self._current_month  = 12
        else:
            self._current_month -= 1
        self._update_month_label()
        self.refresh()

    def _next_month(self):
        if self._current_month == 12:
            self._current_year  += 1
            self._current_month  = 1
        else:
            self._current_month += 1
        self._update_month_label()
        self.refresh()

    def _update_month_label(self):
        import calendar as cal
        name = cal.month_name[self._current_month]
        self._month_label.config(text=f"{name} {self._current_year}")

    # ── Exports ───────────────────────────────────────────────────────────────

    def _export_csv(self):
        if self._hm is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Exportar CSV",
        )
        if not path:
            return
        from export_csv import export_events_csv
        export_events_csv(self._hm.get_events(), filepath=path)
        messagebox.showinfo("Exportado", f"CSV guardado en:\n{path}")

    def _export_json(self):
        if self._hm is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exportar JSON",
        )
        if not path:
            return
        from export_json import export_events_json
        export_events_json(self._hm.get_events(), filepath=path)
        messagebox.showinfo("Exportado", f"JSON guardado en:\n{path}")

    def _export_pdf(self):
        if self._hm is None:
            return
        from export_pdf import is_pdf_available
        if not is_pdf_available():
            messagebox.showwarning(
                "PDF no disponible",
                "reportlab no está instalado.\n"
                "Instalá con: pip install reportlab"
            )
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Exportar PDF",
        )
        if not path:
            return
        from export_pdf import export_report_pdf
        summary = self._hm.get_summary()
        export_report_pdf(
            title="Arch-Ive — Reporte de Backups",
            events=self._hm.get_events(),
            summary=summary,
            filepath=path,
        )
        messagebox.showinfo("Exportado", f"PDF guardado en:\n{path}")
