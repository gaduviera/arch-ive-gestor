import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from pathlib import Path

from config import load_config, save_config
from backup_engine import run_backup
from duplicates_tab import DuplicatesTab

# ── Branding SYMETRA ──────────────────────────────────────────────────────────
C_BG      = "#111111"
C_PANEL   = "#1A1A1A"
C_GOLD    = "#C6A85E"
C_TEXT    = "#F5F5F5"
C_MUTED   = "#888888"
C_SUCCESS = "#4CAF50"
C_ERROR   = "#E53935"

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_BTN   = ("Segoe UI", 9, "bold")
FONT_MONO  = ("Consolas", 8)

DAY_OPTIONS = [7, 15, 30, 60]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self._thread = None

        self.title("Arch-Ive by SYMETRA — CDE Backup Tool")
        self.configure(bg=C_BG)
        self.resizable(True, True)
        self.minsize(680, 580)

        self._build_ui()
        self._restore_config()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C_PANEL, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ARCH-IVE  by  SYMETRA",
                 font=("Segoe UI", 16, "bold"), fg=C_GOLD, bg=C_PANEL).pack()
        tk.Label(hdr, text="CDE Backup Tool  —  MVP",
                 font=("Segoe UI", 9), fg=C_MUTED, bg=C_PANEL).pack()

        # ── Tab bar (manual, sin ttk.Notebook para full control de colores) ──
        tab_bar = tk.Frame(self, bg=C_PANEL)
        tab_bar.pack(fill="x")

        self._tab_frames = {}
        self._tab_btns   = {}

        for name, label in [("backup", "Backup Incremental"), ("duplicados", "Duplicados")]:
            btn = tk.Button(
                tab_bar, text=label,
                font=FONT_BTN, relief="flat", bd=0,
                padx=20, pady=8, cursor="hand2",
                command=lambda n=name: self._switch_tab(n),
            )
            btn.pack(side="left")
            self._tab_btns[name] = btn

        # ── Content area ──────────────────────────────────────────────────────
        content = tk.Frame(self, bg=C_BG)
        content.pack(fill="both", expand=True)

        self._tab_frames["backup"]     = self._build_backup_tab(content)
        self._tab_frames["duplicados"] = DuplicatesTab(content)

        for frame in self._tab_frames.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._switch_tab("backup")

    def _switch_tab(self, name: str):
        for n, btn in self._tab_btns.items():
            if n == name:
                btn.config(bg=C_GOLD, fg=C_BG)
            else:
                btn.config(bg=C_PANEL, fg=C_MUTED)
        self._tab_frames[name].lift()

    # ── Backup Tab ────────────────────────────────────────────────────────────

    def _build_backup_tab(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=C_BG)

        body = tk.Frame(frame, bg=C_BG, padx=20, pady=14)
        body.pack(fill="x")

        # Source
        self._source_var = tk.StringVar()
        self._make_path_row(body, "Carpeta CDE (origen):", self._source_var, self._browse_source)

        # Dest
        self._dest_var = tk.StringVar()
        self._make_path_row(body, "Carpeta Backup (destino):", self._dest_var, self._browse_dest)

        # Days selector
        days_row = tk.Frame(body, bg=C_BG)
        days_row.pack(fill="x", pady=(8, 0))
        tk.Label(days_row, text="Últimos días a sincronizar:", font=FONT_LABEL,
                 fg=C_TEXT, bg=C_BG).pack(side="left")
        self._days_var = tk.IntVar(value=30)
        for d in DAY_OPTIONS:
            tk.Radiobutton(
                days_row, text=str(d), variable=self._days_var, value=d,
                font=FONT_LABEL, fg=C_GOLD, bg=C_BG, selectcolor=C_PANEL,
                activebackground=C_BG, activeforeground=C_GOLD,
                bd=0, highlightthickness=0,
            ).pack(side="left", padx=10)

        # Last backup info
        self._last_backup_lbl = tk.Label(body, text="", font=("Segoe UI", 8),
                                         fg=C_MUTED, bg=C_BG)
        self._last_backup_lbl.pack(anchor="w", pady=(4, 0))

        # Buttons
        btn_row = tk.Frame(body, bg=C_BG)
        btn_row.pack(fill="x", pady=12)

        self._btn_dry = self._make_btn(btn_row, "Vista Previa (Dry Run)", self._dry_run, outline=True)
        self._btn_dry.pack(side="left", padx=(0, 10))
        self._btn_run = self._make_btn(btn_row, "Ejecutar Backup", self._run_backup)
        self._btn_run.pack(side="left")

        # Progress bar
        prog_frame = tk.Frame(frame, bg=C_BG, padx=20)
        prog_frame.pack(fill="x")
        self._progress = ttk.Progressbar(prog_frame, mode="indeterminate", length=600)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("gold.Horizontal.TProgressbar",
                        troughcolor=C_PANEL, background=C_GOLD, bordercolor=C_BG)
        self._progress.configure(style="gold.Horizontal.TProgressbar")
        self._progress.pack(fill="x", pady=(0, 8))

        self._status_lbl = tk.Label(frame, text="Listo.", font=FONT_LABEL,
                                    fg=C_MUTED, bg=C_BG)
        self._status_lbl.pack(anchor="w", padx=20)

        # Log area
        log_frame = tk.Frame(frame, bg=C_PANEL, padx=2, pady=2)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")

        self._log = tk.Text(
            log_frame, font=FONT_MONO, bg="#0D0D0D", fg=C_TEXT,
            insertbackground=C_GOLD, selectbackground=C_GOLD,
            relief="flat", bd=0, wrap="none",
            yscrollcommand=scrollbar.set, state="disabled",
        )
        self._log.pack(fill="both", expand=True)
        scrollbar.config(command=self._log.yview)

        self._log.tag_config("gold",    foreground=C_GOLD)
        self._log.tag_config("success", foreground=C_SUCCESS)
        self._log.tag_config("error",   foreground=C_ERROR)
        self._log.tag_config("muted",   foreground=C_MUTED)

        return frame

    # ── Widgets helpers ───────────────────────────────────────────────────────

    def _make_path_row(self, parent, label, var, command):
        row = tk.Frame(parent, bg=C_BG)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, font=FONT_LABEL, fg=C_TEXT, bg=C_BG,
                 width=28, anchor="w").pack(side="left")
        tk.Entry(row, textvariable=var, font=FONT_LABEL,
                 bg=C_PANEL, fg=C_TEXT, insertbackground=C_GOLD,
                 relief="flat", bd=4).pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(row, text="Explorar…", command=command,
                  font=FONT_BTN, fg=C_GOLD, bg=C_PANEL,
                  activeforeground=C_BG, activebackground=C_GOLD,
                  relief="flat", bd=0, padx=10, pady=4, cursor="hand2"
                  ).pack(side="left")

    def _make_btn(self, parent, text, command, outline=False):
        bg = C_PANEL if outline else C_GOLD
        fg = C_GOLD  if outline else C_BG
        return tk.Button(parent, text=text, command=command,
                         font=FONT_BTN, fg=fg, bg=bg,
                         activeforeground=C_BG, activebackground=C_GOLD,
                         relief="flat", bd=0, padx=16, pady=8, cursor="hand2")

    # ── Config ────────────────────────────────────────────────────────────────

    def _restore_config(self):
        self._source_var.set(self.cfg.get("source_path", ""))
        self._dest_var.set(self.cfg.get("dest_path", ""))
        self._days_var.set(self.cfg.get("days", 30))
        last = self.cfg.get("last_backup")
        if last:
            self._last_backup_lbl.config(text=f"Último backup exitoso: {last}")

    def _persist_config(self, success: bool = False):
        self.cfg["source_path"] = self._source_var.get()
        self.cfg["dest_path"]   = self._dest_var.get()
        self.cfg["days"]        = self._days_var.get()
        if success:
            ts = datetime.now().strftime("%d/%m/%Y %H:%M")
            self.cfg["last_backup"] = ts
            self._last_backup_lbl.config(text=f"Último backup exitoso: {ts}")
        save_config(self.cfg)

    # ── Backup actions ────────────────────────────────────────────────────────

    def _browse_source(self):
        path = filedialog.askdirectory(title="Seleccionar carpeta CDE (origen)")
        if path:
            self._source_var.set(path)

    def _browse_dest(self):
        path = filedialog.askdirectory(title="Seleccionar carpeta Backup (destino)")
        if path:
            self._dest_var.set(path)

    def _validate_paths(self) -> bool:
        src = self._source_var.get().strip()
        dst = self._dest_var.get().strip()
        if not src or not dst:
            messagebox.showerror("Error", "Seleccioná carpeta origen y destino antes de continuar.")
            return False
        if not Path(src).exists():
            messagebox.showerror("Error", f"La carpeta origen no existe:\n{src}")
            return False
        return True

    def _dry_run(self):
        if self._validate_paths():
            self._start_operation(dry_run=True)

    def _run_backup(self):
        if not self._validate_paths():
            return
        days = self._days_var.get()
        if not messagebox.askyesno(
            "Confirmar backup",
            f"Se copiarán archivos nuevos/modificados de los últimos {days} días.\n\n"
            f"Origen:  {self._source_var.get()}\n"
            f"Destino: {self._dest_var.get()}\n\n¿Continuar?"
        ):
            return
        self._start_operation(dry_run=False)

    def _start_operation(self, dry_run: bool):
        self._persist_config()
        self._clear_log()
        mode = "VISTA PREVIA (DRY RUN)" if dry_run else "BACKUP INCREMENTAL"
        self._log_line(f"── {mode} iniciado ────────────────────────", "gold")
        self._log_line(f"Origen:  {self._source_var.get()}", "muted")
        self._log_line(f"Destino: {self._dest_var.get()}", "muted")
        self._log_line(f"Días:    {self._days_var.get()}", "muted")
        self._log_line("", None)
        self._set_busy(True)
        self._status_lbl.config(text="Ejecutando…", fg=C_GOLD)
        run_backup(
            source=self._source_var.get(),
            dest=self._dest_var.get(),
            days=self._days_var.get(),
            dry_run=dry_run,
            on_line=self._on_line,
            on_done=lambda ok, log: self.after(0, self._on_done, ok, log, dry_run),
        )

    def _on_line(self, line: str):
        self.after(0, self._log_line, line, None)

    def _on_done(self, success: bool, log_path: str, dry_run: bool):
        self._set_busy(False)
        if success:
            self._log_line("", None)
            label = "Vista previa completada." if dry_run else "Backup completado exitosamente."
            self._log_line(f"✔ {label}", "success")
            if log_path:
                self._log_line(f"Log guardado en: {log_path}", "muted")
            self._status_lbl.config(text=label, fg=C_SUCCESS)
            if not dry_run:
                self._persist_config(success=True)
        else:
            self._log_line("✘ Operación finalizada con errores. Revisá el log.", "error")
            self._status_lbl.config(text="Error en la operación.", fg=C_ERROR)

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self._btn_dry.config(state=state)
        self._btn_run.config(state=state)
        if busy:
            self._progress.start(12)
        else:
            self._progress.stop()
            self._progress["value"] = 0

    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    def _log_line(self, line: str, tag):
        self._log.config(state="normal")
        if tag:
            self._log.insert("end", line + "\n", tag)
        else:
            self._log.insert("end", line + "\n")
        self._log.see("end")
        self._log.config(state="disabled")
