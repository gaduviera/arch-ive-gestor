"""Main window: header + tabs (Sincronizar, Duplicados, Reportes)."""
import tkinter as tk

from core.history import BackupHistoryManager, ReportsCalculator
from core.mirrors import MirrorStore
from ui.duplicates_tab import DuplicatesTab
from ui.reports_tab import ReportsTab
from ui.sync_tab import SyncTab
from ui.theme import COLORS

C_BG, C_PANEL = COLORS["carbon_base"], COLORS["carbon_elevated"]
C_GOLD, C_MUTED = COLORS["gold_primary"], COLORS["silver"]
FONT_BTN = ("Segoe UI", 9, "bold")

TABS = [("sync", "Sincronizar"), ("duplicados", "Duplicados"), ("reportes", "Reportes")]


class App(tk.Tk):
    def __init__(self, store: MirrorStore | None = None, history: BackupHistoryManager | None = None):
        super().__init__()
        self.store = store or MirrorStore()
        self.history = history or BackupHistoryManager()
        self.title("Arch-Ive by SYMETRA — Espejos de carpetas")
        self.configure(bg=C_BG)
        self.minsize(1000, 640)
        self.geometry("1100x700")
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C_PANEL, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ARCH-IVE  by  SYMETRA", font=("Segoe UI", 16, "bold"),
                 fg=C_GOLD, bg=C_PANEL).pack()
        tk.Label(hdr, text="Espejos de carpetas: cada origen se copia en su destino",
                 font=("Segoe UI", 9), fg=C_MUTED, bg=C_PANEL).pack()

        bar = tk.Frame(self, bg=C_PANEL)
        bar.pack(fill="x")
        content = tk.Frame(self, bg=C_BG)
        content.pack(fill="both", expand=True)

        self.reports = ReportsTab(content, history_manager=self.history,
                                  calculator=ReportsCalculator(self.history))
        self.frames = {
            "sync": SyncTab(content, self.store, self.history, on_history=self.reports.refresh),
            "duplicados": DuplicatesTab(content),
            "reportes": self.reports,
        }
        self.tab_btns = {}
        for key, label in TABS:
            b = tk.Button(bar, text=label, font=FONT_BTN, relief="flat", bd=0, padx=20, pady=8,
                          cursor="hand2", command=lambda k=key: self.show(k))
            b.pack(side="left")
            self.tab_btns[key] = b
        for f in self.frames.values():
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.show("sync")

    def show(self, key: str):
        for k, b in self.tab_btns.items():
            b.config(bg=C_GOLD if k == key else C_PANEL, fg=C_BG if k == key else C_MUTED)
        self.frames[key].lift()
