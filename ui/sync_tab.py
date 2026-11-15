"""Sincronizar tab: list of mirror pairs, analyze, preview, run."""
from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from core.executor import check_space, execute
from core.mirrors import MirrorStore, new_mirror, warnings
from core.sync import ARCHIVE_DIR, DEFAULT_EXCLUDES, SyncError, analyze
from ui.theme import COLORS

C_BG, C_PANEL, C_HOVER = COLORS["carbon_base"], COLORS["carbon_elevated"], COLORS["carbon_hover"]
C_GOLD, C_TEXT, C_MUTED = COLORS["gold_primary"], COLORS["platinum"], COLORS["silver"]
C_SMOKE, C_OK, C_WARN, C_ERR = COLORS["smoke"], COLORS["success"], COLORS["warning"], COLORS["error"]
F_LABEL, F_SMALL, F_BTN = ("Segoe UI", 9), ("Segoe UI", 8), ("Segoe UI", 9, "bold")
F_TITLE, F_NUM, F_MONO = ("Segoe UI", 12, "bold"), ("Segoe UI", 15, "bold"), ("Consolas", 8)

MODE_LABEL = {"mirror": "Espejo", "add_only": "Solo agregar"}
MODE_HELP = {
    "mirror": "El destino queda igual al origen. Lo borrado o reemplazado va a _archivo/.",
    "add_only": "Copia nuevos y modificados. Nunca saca del destino lo que se borró en el origen.",
}
STATS = [("new", "Nuevos"), ("modified", "Modificados"), ("moved", "Movidos"),
         ("archived", "A archivo"), ("kept", "Se conservan")]
ARCHIVE_WARN_RATIO = 0.30


def fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.2f} TB"


def ago(iso: str | None) -> str:
    if not iso:
        return "nunca"
    try:
        days = (datetime.now() - datetime.fromisoformat(iso)).days
    except ValueError:
        return "—"
    return "hoy" if days == 0 else "ayer" if days == 1 else f"hace {days} días"


def pending(summary: dict | None) -> int:
    """Changes found by the last analysis (modified files count once, inside archived)."""
    if not summary:
        return 0
    return sum(summary.get(k, 0) for k in ("new", "moved", "archived"))


def button(parent, text, cmd, primary=False):
    return tk.Button(parent, text=text, command=cmd, font=F_BTN,
                     fg=C_BG if primary else C_GOLD, bg=C_GOLD if primary else C_PANEL,
                     activeforeground=C_BG, activebackground=C_GOLD, disabledforeground=C_SMOKE,
                     relief="flat", bd=0, padx=12, pady=6, cursor="hand2")


def style_tree():
    st = ttk.Style()
    st.theme_use("clam")
    st.configure("Arch.Treeview", background=C_PANEL, fieldbackground=C_PANEL, foreground=C_TEXT,
                 rowheight=26, borderwidth=0, font=F_LABEL)
    st.map("Arch.Treeview", background=[("selected", COLORS["gold_subtle"])],
           foreground=[("selected", C_TEXT)])
    st.configure("Arch.Treeview.Heading", background=C_BG, foreground=C_MUTED,
                 relief="flat", font=F_SMALL)
    st.configure("gold.Horizontal.TProgressbar", troughcolor=C_PANEL, background=C_GOLD, bordercolor=C_BG)


class SyncTab(tk.Frame):
    def __init__(self, parent, store: MirrorStore, history, on_history=None):
        super().__init__(parent, bg=C_BG)
        self.store, self.history, self.on_history = store, history, on_history
        self.plans: dict[str, object] = {}        # mirror name -> fresh Plan
        self.batch_errors: dict[str, str] = {}
        self._q: queue.Queue = queue.Queue()
        self._cancel = threading.Event()
        self._busy = False
        style_tree()
        self._build()
        self.refresh_list()
        self.after(100, self._poll)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        left = tk.Frame(self, bg=C_BG, width=400)
        left.pack(side="left", fill="y", padx=(16, 8), pady=12)
        left.pack_propagate(False)

        top = tk.Frame(left, bg=C_BG)
        top.pack(fill="x")
        tk.Label(top, text="Espejos", font=F_TITLE, fg=C_GOLD, bg=C_BG).pack(side="left")
        self.btn_new = button(top, "+ Nuevo", self.new_mirror)
        self.btn_new.pack(side="right")

        self.tree = ttk.Treeview(left, style="Arch.Treeview", show="tree", selectmode="browse",
                                 columns=("info",))
        self.tree.column("#0", width=150, stretch=True)
        self.tree.column("info", width=230, stretch=True)
        self.tree.tag_configure("problem", foreground=C_ERR)
        self.tree.tag_configure("pending", foreground=C_WARN)
        self.tree.tag_configure("loose", foreground=C_MUTED)
        self.tree.pack(fill="both", expand=True, pady=8)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())
        self.tree.bind("<Double-1>", lambda e: self.edit_mirror())

        self.btn_batch = button(left, "Analizar fijados", self.analyze_pinned)
        self.btn_batch.pack(fill="x")

        self.right = tk.Frame(self, bg=C_PANEL)
        self.right.pack(side="left", fill="both", expand=True, padx=(8, 16), pady=12)
        self._build_empty()
        self._build_detail()

    def _build_empty(self):
        f = self.empty = tk.Frame(self.right, bg=C_PANEL)
        tk.Label(f, text="Crea tu primer espejo", font=F_TITLE, fg=C_TEXT, bg=C_PANEL).pack(pady=(80, 6))
        tk.Label(f, text="Un espejo copia una carpeta origen en una carpeta destino.\n"
                         "Crea uno por cada par de carpetas que quieras mantener sincronizadas.",
                 font=F_LABEL, fg=C_MUTED, bg=C_PANEL, justify="center").pack()
        button(f, "Nuevo espejo", self.new_mirror, primary=True).pack(pady=16)

    def _build_detail(self):
        f = self.detail = tk.Frame(self.right, bg=C_PANEL, padx=16, pady=12)
        head = tk.Frame(f, bg=C_PANEL)
        head.pack(fill="x")
        self.lbl_name = tk.Label(head, font=F_TITLE, fg=C_TEXT, bg=C_PANEL)
        self.lbl_name.pack(side="left")
        self.lbl_mode = tk.Label(head, font=F_SMALL, fg=C_BG, bg=C_GOLD, padx=8, pady=1)
        self.lbl_mode.pack(side="left", padx=10)
        button(head, "Eliminar", self.delete_mirror).pack(side="right")
        button(head, "Editar", self.edit_mirror).pack(side="right", padx=6)

        self.lbl_src = tk.Label(f, font=F_MONO, fg=C_TEXT, bg=C_PANEL, anchor="w")
        self.lbl_src.pack(fill="x", pady=(10, 0))
        tk.Label(f, text="↓", font=F_LABEL, fg=C_GOLD, bg=C_PANEL, anchor="w").pack(fill="x", padx=4)
        self.lbl_dst = tk.Label(f, font=F_MONO, fg=C_TEXT, bg=C_PANEL, anchor="w")
        self.lbl_dst.pack(fill="x")
        self.lbl_meta = tk.Label(f, font=F_SMALL, fg=C_MUTED, bg=C_PANEL, anchor="w", justify="left")
        self.lbl_meta.pack(fill="x", pady=(6, 0))

        grid = tk.Frame(f, bg=C_PANEL)
        grid.pack(fill="x", pady=12)
        self.stat_lbls = {}
        for i, (key, label) in enumerate(STATS):
            cell = tk.Frame(grid, bg=C_BG, padx=10, pady=6)
            cell.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0))
            grid.columnconfigure(i, weight=1)
            tk.Label(cell, text=label, font=F_SMALL, fg=C_MUTED, bg=C_BG).pack(anchor="w")
            self.stat_lbls[key] = tk.Label(cell, text="—", font=F_NUM, fg=C_TEXT, bg=C_BG)
            self.stat_lbls[key].pack(anchor="w")
        self.lbl_bytes = tk.Label(f, font=F_LABEL, fg=C_MUTED, bg=C_PANEL, anchor="w")
        self.lbl_bytes.pack(fill="x")

        btns = tk.Frame(f, bg=C_PANEL)
        btns.pack(fill="x", pady=10)
        self.btn_analyze = button(btns, "Analizar", self.analyze_selected)
        self.btn_analyze.pack(side="left")
        self.btn_detail = button(btns, "Ver detalle", self.show_detail)
        self.btn_detail.pack(side="left", padx=6)
        self.btn_run = button(btns, "Sincronizar", self.run_selected, primary=True)
        self.btn_run.pack(side="left")
        self.btn_cancel = button(btns, "Cancelar", self._cancel.set)
        button(btns, "Abrir archivo", self.open_archive).pack(side="right")

        self.progress = ttk.Progressbar(f, style="gold.Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill="x")
        self.lbl_status = tk.Label(f, text="Listo.", font=F_LABEL, fg=C_MUTED, bg=C_PANEL, anchor="w")
        self.lbl_status.pack(fill="x", pady=(4, 6))

        logf = tk.Frame(f, bg=C_BG)
        logf.pack(fill="both", expand=True)
        sb = tk.Scrollbar(logf)
        sb.pack(side="right", fill="y")
        self.log = tk.Text(logf, font=F_MONO, bg="#0D0D0D", fg=C_TEXT, relief="flat", bd=0,
                           wrap="none", height=8, yscrollcommand=sb.set, state="disabled")
        self.log.pack(fill="both", expand=True)
        sb.config(command=self.log.yview)
        for tag, color in (("gold", C_GOLD), ("ok", C_OK), ("err", C_ERR), ("muted", C_MUTED), ("warn", C_WARN)):
            self.log.tag_config(tag, foreground=color)

    # ── List and selection ────────────────────────────────────────────────────

    def selected(self) -> dict | None:
        return self.store.get(self.store.selected)

    def _status_text(self, m: dict) -> str:
        if m["name"] in self.batch_errors:
            return self.batch_errors[m["name"]]
        if not os.path.isdir(m["source"]):
            return "origen no disponible"
        n = pending(m.get("last_summary"))
        return f"{n:,} pendientes" if n else f"sincronizado {ago(m.get('last_run'))}" if m.get("last_run") else "nunca"

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for m in self.store.ordered():
            pin = "★ " if m.get("pinned") else "   "
            status = self._status_text(m)
            tag = ("problem" if m["name"] in self.batch_errors or status == "origen no disponible"
                   else "pending" if pending(m.get("last_summary")) else "" if m.get("pinned") else "loose")
            self.tree.insert("", "end", iid=m["name"], text=f"{pin}{m['name']}",
                             values=(f"{MODE_LABEL.get(m['mode'], m['mode'])} · {status}",), tags=(tag,))
        sel = self.selected()
        if sel is None and self.store.mirrors:
            self.store.selected = self.store.ordered()[0]["name"]
            sel = self.selected()
        if sel:
            self.tree.selection_set(sel["name"])
        self.btn_batch.config(state="normal" if self.store.pinned() else "disabled")
        self._show_selected()

    def _on_select(self):
        sel = self.tree.selection()
        if sel and sel[0] != self.store.selected:
            self.store.selected = sel[0]
            self.store.save()
            self._show_selected()

    def _show_selected(self):
        m = self.selected()
        self.empty.pack_forget()
        self.detail.pack_forget()
        if not m:
            self.empty.pack(fill="both", expand=True)
            return
        self.detail.pack(fill="both", expand=True)
        self.lbl_name.config(text=m["name"])
        self.lbl_mode.config(text=MODE_LABEL.get(m["mode"], m["mode"]))
        self.lbl_src.config(text=f"Origen   {m['source']}")
        self.lbl_dst.config(text=f"Destino  {m['dest']}")
        excl = ", ".join(m.get("exclude") or []) or "ninguna"
        self.lbl_meta.config(text=f"{MODE_HELP.get(m['mode'], '')}\nExcluir: {excl}   ·   "
                                  f"Última sincronización: {ago(m.get('last_run'))}")
        self._show_plan(self.plans.get(m["name"]))

    def _show_plan(self, plan):
        if plan is None:
            for lbl in self.stat_lbls.values():
                lbl.config(text="—")
            self.lbl_bytes.config(text="Analiza para ver qué cambió desde la última vez.")
        else:
            c = plan.counts()
            for key, lbl in self.stat_lbls.items():
                lbl.config(text=f"{c[key]:,}")
            extra = f"   ·   {len(plan.scan_errors)} carpetas sin acceso en origen" if plan.scan_errors else ""
            self.lbl_bytes.config(text=f"{fmt_bytes(plan.bytes_to_copy)} a copiar   ·   "
                                       f"{fmt_bytes(plan.bytes_saved)} ahorrados por movidos   ·   "
                                       f"{c['unchanged']:,} sin cambios{extra}")
        self._sync_buttons()

    def _sync_buttons(self):
        m = self.selected()
        has_plan = bool(m and m["name"] in self.plans)
        idle = "disabled" if self._busy else "normal"
        for b in (self.btn_analyze, self.btn_new, self.btn_batch):
            b.config(state=idle)
        if not self.store.pinned():
            self.btn_batch.config(state="disabled")
        self.btn_detail.config(state=idle if has_plan else "disabled")
        self.btn_run.config(state=idle if has_plan and not self.plans[m["name"]].is_empty else "disabled")
        if self._busy:
            self.btn_cancel.pack(side="left", padx=6)
        else:
            self.btn_cancel.pack_forget()

    # ── Mirror CRUD ───────────────────────────────────────────────────────────

    def new_mirror(self):
        MirrorDialog(self, None)

    def edit_mirror(self):
        if self.selected() and not self._busy:
            MirrorDialog(self, self.selected())

    def delete_mirror(self):
        m = self.selected()
        if not m or self._busy:
            return
        if messagebox.askyesno("Eliminar espejo",
                               f"¿Eliminar el espejo «{m['name']}»?\n\n"
                               "Solo se borra la configuración. Las carpetas y archivos no se tocan.",
                               parent=self):
            self.plans.pop(m["name"], None)
            self.store.delete(m["name"])
            self.refresh_list()

    def saved(self, mirror: dict, old_name: str | None):
        if old_name:
            self.plans.pop(old_name, None)
            self.batch_errors.pop(old_name, None)
        self.store.selected = mirror["name"]
        self.store.save()
        self.refresh_list()

    def open_archive(self):
        m = self.selected()
        path = os.path.join(m["dest"], ARCHIVE_DIR) if m else ""
        if path and os.path.isdir(path):
            os.startfile(path)
        else:
            messagebox.showinfo("Archivo", "Este espejo todavía no archivó nada.", parent=self)

    # ── Logging ───────────────────────────────────────────────────────────────

    def write(self, line: str, tag: str | None = None):
        self.log.config(state="normal")
        self.log.insert("end", line + "\n", tag or ())
        self.log.see("end")
        self.log.config(state="disabled")

    def status(self, text: str, color=C_MUTED):
        self.lbl_status.config(text=text, fg=color)

    # ── Background work ───────────────────────────────────────────────────────

    def _start(self, target, *args):
        self._busy = True
        self._cancel.clear()
        self._sync_buttons()
        threading.Thread(target=target, args=args, daemon=True).start()

    def _poll(self):
        try:
            while True:
                kind, payload = self._q.get_nowait()
                getattr(self, f"_on_{kind}")(*payload)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _analyze_worker(self, mirrors: list[dict], batch: bool):
        results = []
        for i, m in enumerate(mirrors, 1):
            if self._cancel.is_set():
                break
            self._q.put(("progress", (i - 1, len(mirrors), f"Analizando «{m['name']}»…")))
            try:
                results.append((m["name"], analyze(m), None))
            except SyncError as exc:
                results.append((m["name"], None, str(exc)))
            except OSError as exc:
                results.append((m["name"], None, f"Error leyendo carpetas: {exc}"))
        self._q.put(("analyzed", (results, batch)))

    def _on_progress(self, done, total, text):
        self.progress.config(maximum=max(total, 1), value=done)
        self.status(text, C_GOLD)

    def _on_analyzed(self, results, batch):
        self._busy = False
        self.progress.config(value=0)
        for name, plan, err in results:
            if err:
                self.plans.pop(name, None)
                self.batch_errors[name] = err
                self.write(f"✘ {name}: {err}", "err")
                continue
            self.batch_errors.pop(name, None)
            self.plans[name] = plan
            self.store.record(name, summary=plan.counts())
            c = plan.counts()
            self.write(f"● {name}: {c['new']} nuevos, {c['modified']} modificados, {c['moved']} movidos, "
                       f"{c['archived']} a archivo · {fmt_bytes(plan.bytes_to_copy)} a copiar",
                       "muted" if plan.is_empty else "gold")
        self.status("Análisis terminado." if results else "Análisis cancelado.", C_OK)
        self.refresh_list()
        if batch:
            BatchDialog(self, [r for r in results])

    def _run_worker(self, jobs: list[tuple[dict, object]]):
        for idx, (m, plan) in enumerate(jobs, 1):
            if self._cancel.is_set():
                break
            label = f"[{idx}/{len(jobs)}] {m['name']}" if len(jobs) > 1 else m["name"]

            def progress(done, total, rel, label=label):
                self._q.put(("progress", (done, total, f"{label}: {rel}")))
            try:
                res = execute(plan, m["source"], m["dest"], on_progress=progress, cancel=self._cancel)
            except OSError as exc:
                self._q.put(("ran", (m, None, str(exc))))
                continue
            self._q.put(("ran", (m, res, None)))
        self._q.put(("finished", ()))

    def _on_ran(self, m, res, err):
        name = m["name"]
        self.plans.pop(name, None)
        if err:
            self.write(f"✘ {name}: {err}", "err")
            return
        self.store.record(name, summary={}, ran=not res.cancelled)
        self.history.append_event({
            "mirror": name, "mode": m["mode"], "copied": res.copied, "moved": res.moved,
            "archived": res.archived, "errors": len(res.errors), "bytes_copied": res.bytes_copied,
            "duration_s": res.duration_s, "cancelled": res.cancelled,
        })
        tag = "warn" if res.errors or res.cancelled else "ok"
        word = "cancelado" if res.cancelled else "listo"
        self.write(f"✔ {name} {word}: {res.copied} copiados, {res.moved} movidos, {res.archived} archivados, "
                   f"{fmt_bytes(res.bytes_copied)} en {res.duration_s:.0f} s", tag)
        for e in res.errors[:50]:
            self.write(f"   ✘ {e}", "err")
        if len(res.errors) > 50:
            self.write(f"   … y {len(res.errors) - 50} errores más", "err")

    def _on_finished(self):
        self._busy = False
        self.progress.config(value=0)
        self.status("Sincronización terminada. Analiza de nuevo para confirmar.", C_OK)
        self.refresh_list()
        if self.on_history:
            self.on_history()

    # ── Actions ───────────────────────────────────────────────────────────────

    def analyze_selected(self):
        m = self.selected()
        if m and not self._busy:
            self.write(f"── Analizando «{m['name']}» ──", "gold")
            self._start(self._analyze_worker, [m], False)

    def analyze_pinned(self):
        pinned = self.store.pinned()
        if pinned and not self._busy:
            self.write(f"── Analizando {len(pinned)} espejos fijados ──", "gold")
            self._start(self._analyze_worker, pinned, True)

    def confirm(self, jobs: list[tuple[dict, object]]) -> bool:
        lines, risky = [], []
        for m, plan in jobs:
            c = plan.counts()
            lines.append(f"• {m['name']}: {c['new']} nuevos, {c['modified']} modificados, "
                         f"{c['moved']} movidos, {c['archived']} a archivo ({fmt_bytes(plan.bytes_to_copy)})")
            dest_total = c["unchanged"] + c["modified"] + c["moved"] + len(plan.deleted) + c["kept"]
            if dest_total and (len(plan.deleted) + c["modified"]) / dest_total > ARCHIVE_WARN_RATIO:
                risky.append(m["name"])
            if not check_space(plan, m["dest"]):
                messagebox.showerror("Sin espacio", f"El destino de «{m['name']}» no tiene espacio "
                                     f"para {fmt_bytes(plan.bytes_to_copy)}.", parent=self)
                return False
        if not messagebox.askyesno("Confirmar sincronización",
                                   "\n".join(lines) + "\n\nLo que sale del destino va a _archivo/. ¿Continuar?",
                                   parent=self):
            return False
        if risky:
            return messagebox.askyesno(
                "Muchos archivos a archivar",
                "Más del 30 % del destino se movería a _archivo/ en:\n" + "\n".join(risky) +
                "\n\nPuede ser una carpeta de origen equivocada o desconectada. ¿Seguro?",
                icon="warning", parent=self)
        return True

    def run_selected(self):
        m = self.selected()
        plan = self.plans.get(m["name"]) if m else None
        if plan and not self._busy and self.confirm([(m, plan)]):
            self.write(f"── Sincronizando «{m['name']}» ──", "gold")
            self._start(self._run_worker, [(m, plan)])

    def run_batch(self, names: list[str]):
        jobs = [(self.store.get(n), self.plans[n]) for n in names
                if self.store.get(n) and n in self.plans and not self.plans[n].is_empty]
        if jobs and not self._busy and self.confirm(jobs):
            self.write(f"── Sincronizando {len(jobs)} espejos ──", "gold")
            self._start(self._run_worker, jobs)
            return True
        return False

    def show_detail(self):
        m = self.selected()
        if m and m["name"] in self.plans:
            DetailDialog(self, m["name"], self.plans[m["name"]])


class MirrorDialog(tk.Toplevel):
    def __init__(self, tab: SyncTab, mirror: dict | None):
        super().__init__(tab)
        self.tab, self.old = tab, mirror
        m = mirror or new_mirror("", "", "")
        self.title("Editar espejo" if mirror else "Nuevo espejo")
        self.configure(bg=C_BG, padx=18, pady=14)
        self.resizable(False, False)
        self.transient(tab.winfo_toplevel())

        self.v_name = tk.StringVar(value=m["name"])
        self.v_src = tk.StringVar(value=m["source"])
        self.v_dst = tk.StringVar(value=m["dest"])
        self.v_mode = tk.StringVar(value=m["mode"])
        self.v_pin = tk.BooleanVar(value=m.get("pinned", True))

        self._row("Nombre", self.v_name)
        self._row("Carpeta origen", self.v_src, self._pick_src)
        self._row("Carpeta destino", self.v_dst, self._pick_dst)

        tk.Label(self, text="Modo", font=F_BTN, fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(10, 2))
        for key in ("mirror", "add_only"):
            tk.Radiobutton(self, text=f"{MODE_LABEL[key]} — {MODE_HELP[key]}", variable=self.v_mode,
                           value=key, font=F_LABEL, fg=C_TEXT, bg=C_BG, selectcolor=C_PANEL,
                           activebackground=C_BG, activeforeground=C_GOLD, anchor="w",
                           wraplength=520, justify="left").pack(fill="x")
        tk.Checkbutton(self, text="Fijar (se incluye en «Analizar fijados»)", variable=self.v_pin,
                       font=F_LABEL, fg=C_TEXT, bg=C_BG, selectcolor=C_PANEL, activebackground=C_BG,
                       activeforeground=C_GOLD).pack(anchor="w", pady=(10, 0))

        tk.Label(self, text="Excluir (un patrón por línea)", font=F_BTN, fg=C_TEXT,
                 bg=C_BG).pack(anchor="w", pady=(10, 2))
        self.t_excl = tk.Text(self, height=5, width=40, font=F_MONO, bg=C_PANEL, fg=C_TEXT,
                              insertbackground=C_GOLD, relief="flat", bd=4)
        self.t_excl.insert("1.0", "\n".join(m.get("exclude") or []))
        self.t_excl.pack(fill="x")

        bar = tk.Frame(self, bg=C_BG)
        bar.pack(fill="x", pady=(14, 0))
        button(bar, "Guardar", self._save, primary=True).pack(side="right")
        button(bar, "Cancelar", self.destroy).pack(side="right", padx=6)
        button(bar, "Restaurar exclusiones", self._reset_excl).pack(side="left")
        self.grab_set()

    def _row(self, label, var, browse=None):
        tk.Label(self, text=label, font=F_BTN, fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(8, 2))
        row = tk.Frame(self, bg=C_BG)
        row.pack(fill="x")
        tk.Entry(row, textvariable=var, font=F_LABEL, width=60, bg=C_PANEL, fg=C_TEXT,
                 insertbackground=C_GOLD, relief="flat", bd=4).pack(side="left", fill="x", expand=True)
        if browse:
            button(row, "Explorar…", browse).pack(side="left", padx=(6, 0))

    def _pick_src(self):
        path = filedialog.askdirectory(parent=self, title="Carpeta origen")
        if path:
            self.v_src.set(path)
            if not self.v_name.get().strip():
                self.v_name.set(os.path.basename(path.rstrip("/\\")) or path)

    def _pick_dst(self):
        path = filedialog.askdirectory(parent=self, title="Carpeta destino")
        if path:
            self.v_dst.set(path)

    def _reset_excl(self):
        self.t_excl.delete("1.0", "end")
        self.t_excl.insert("1.0", "\n".join(DEFAULT_EXCLUDES))

    def _save(self):
        excl = [ln.strip() for ln in self.t_excl.get("1.0", "end").splitlines() if ln.strip()]
        m = dict(self.old or {}, **new_mirror(self.v_name.get(), self.v_src.get(), self.v_dst.get(),
                                              self.v_mode.get(), self.v_pin.get(), excl))
        if self.old:
            m["last_run"] = self.old.get("last_run")
        old_name = self.old["name"] if self.old else None
        others = [o for o in self.tab.store.mirrors if not old_name or o["name"].lower() != old_name.lower()]
        warn = warnings(m, others)
        if warn and not messagebox.askyesno("Aviso", "\n".join(warn) + "\n\n¿Guardar igual?", parent=self):
            return
        if m["source"] and not os.path.isdir(m["source"]):
            if not messagebox.askyesno("Origen no disponible",
                                       "La carpeta origen no existe ahora (¿disco o Drive desconectado?).\n"
                                       "¿Guardar igual?", parent=self):
                return
        try:
            self.tab.store.upsert(m, old_name=old_name)
        except ValueError as exc:
            messagebox.showerror("Revisa el espejo", str(exc), parent=self)
            return
        self.destroy()
        self.tab.saved(m, old_name)


class BatchDialog(tk.Toplevel):
    COLS = [("new", "Nuevos"), ("modified", "Modif."), ("moved", "Movidos"),
            ("archived", "A archivo"), ("bytes", "A copiar"), ("state", "Estado")]

    def __init__(self, tab: SyncTab, results):
        super().__init__(tab)
        self.tab = tab
        self.title("Espejos fijados")
        self.configure(bg=C_BG, padx=14, pady=12)
        self.transient(tab.winfo_toplevel())
        tree = ttk.Treeview(self, style="Arch.Treeview", columns=[c for c, _ in self.COLS],
                            height=min(max(len(results), 3), 12))
        tree.heading("#0", text="Espejo")
        tree.column("#0", width=200)
        for key, label in self.COLS:
            tree.heading(key, text=label)
            tree.column(key, width=170 if key == "state" else 80, anchor="w" if key == "state" else "e")
        self.ready = []
        totals = {"new": 0, "modified": 0, "moved": 0, "archived": 0, "bytes": 0}
        for name, plan, err in results:
            if err:
                tree.insert("", "end", text=name, values=("", "", "", "", "", err))
                continue
            c = plan.counts()
            state = "sin cambios" if plan.is_empty else "listo para sincronizar"
            if not plan.is_empty:
                self.ready.append(name)
            for k in ("new", "modified", "moved", "archived"):
                totals[k] += c[k]
            totals["bytes"] += plan.bytes_to_copy
            tree.insert("", "end", text=name, values=(c["new"], c["modified"], c["moved"], c["archived"],
                                                      fmt_bytes(plan.bytes_to_copy), state))
        tree.pack(fill="both", expand=True)
        tk.Label(self, text=f"Total: {totals['new']} nuevos · {totals['modified']} modificados · "
                            f"{totals['moved']} movidos · {totals['archived']} a archivo · "
                            f"{fmt_bytes(totals['bytes'])} a copiar",
                 font=F_LABEL, fg=C_MUTED, bg=C_BG).pack(anchor="w", pady=8)
        bar = tk.Frame(self, bg=C_BG)
        bar.pack(fill="x")
        run = button(bar, f"Sincronizar {len(self.ready)} espejos", self._run, primary=True)
        run.pack(side="right")
        if not self.ready:
            run.config(state="disabled")
        button(bar, "Cerrar", self.destroy).pack(side="right", padx=6)

    def _run(self):
        if self.tab.run_batch(self.ready):
            self.destroy()


class DetailDialog(tk.Toplevel):
    LIMIT = 5000
    FILTERS = ["Todos", "Nuevos", "Modificados", "Movidos", "A archivo", "Se conservan"]

    def __init__(self, tab: SyncTab, name: str, plan):
        super().__init__(tab)
        self.title(f"Detalle — {name}")
        self.configure(bg=C_BG, padx=14, pady=12)
        self.geometry("900x520")
        self.rows = (
            [("Nuevos", f.rel, f.size) for f in plan.new]
            + [("Modificados", s.rel, s.size) for s, _ in plan.modified]
            + [("Movidos", f"{o.rel}  →  {n.rel}", n.size) for o, n in plan.moved]
            + [("A archivo", f.rel, f.size) for f in plan.deleted]
            + [("Se conservan", f.rel, f.size) for f in plan.kept]
        )
        top = tk.Frame(self, bg=C_BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Mostrar:", font=F_LABEL, fg=C_TEXT, bg=C_BG).pack(side="left")
        self.v_filter = tk.StringVar(value="Todos")
        cb = ttk.Combobox(top, textvariable=self.v_filter, values=self.FILTERS, state="readonly", width=16)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self._fill())
        self.v_find = tk.StringVar()
        tk.Entry(top, textvariable=self.v_find, font=F_LABEL, bg=C_PANEL, fg=C_TEXT, insertbackground=C_GOLD,
                 relief="flat", bd=4, width=40).pack(side="left", padx=8)
        self.v_find.trace_add("write", lambda *a: self._fill())
        self.lbl = tk.Label(top, font=F_SMALL, fg=C_MUTED, bg=C_BG)
        self.lbl.pack(side="right")

        frame = tk.Frame(self, bg=C_BG)
        frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        self.tree = ttk.Treeview(frame, style="Arch.Treeview", columns=("kind", "size"),
                                 yscrollcommand=sb.set)
        sb.config(command=self.tree.yview)
        self.tree.heading("#0", text="Ruta")
        self.tree.heading("kind", text="Tipo")
        self.tree.heading("size", text="Tamaño")
        self.tree.column("#0", width=640)
        self.tree.column("kind", width=110)
        self.tree.column("size", width=100, anchor="e")
        self.tree.pack(fill="both", expand=True)
        self._fill()

    def _fill(self):
        self.tree.delete(*self.tree.get_children())
        kind, find = self.v_filter.get(), self.v_find.get().lower()
        rows = [r for r in self.rows if (kind == "Todos" or r[0] == kind) and find in r[1].lower()]
        for r in rows[: self.LIMIT]:
            self.tree.insert("", "end", text=r[1], values=(r[0], fmt_bytes(r[2])))
        more = f" (mostrando {self.LIMIT:,})" if len(rows) > self.LIMIT else ""
        self.lbl.config(text=f"{len(rows):,} archivos{more}")
