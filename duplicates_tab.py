import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

from duplicate_finder import DuplicateFinder

C_BG    = "#111111"
C_PANEL = "#1A1A1A"
C_GOLD  = "#C6A85E"
C_TEXT  = "#F5F5F5"
C_MUTED = "#888888"

FONT_LABEL = ("Segoe UI", 9)
FONT_BTN   = ("Segoe UI", 9, "bold")
FONT_MONO  = ("Consolas", 8)


class DuplicatesTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=C_BG)
        self.finder = DuplicateFinder()
        self.folder_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Selecciona una carpeta para escanear.")
        self.summary_var = tk.StringVar(value="0 grupos  |  Espacio recuperable: 0.00 MB")

        self.duplicates = []
        self.sort_directions = {"size": True, "copies": True}
        self.expanded_groups = set()
        self.selection_vars = {}
        self._delete_btns = {}    # group idx → button widget
        self._group_widgets = {}  # gid → (lbl, body, idx)

        self._build_ui()
        self.after(150, self._poll_finder)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Folder selector row
        ctrl = tk.Frame(self, bg=C_BG, pady=12, padx=16)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Carpeta a escanear:", font=FONT_LABEL,
                 fg=C_TEXT, bg=C_BG).pack(side="left")

        tk.Entry(ctrl, textvariable=self.folder_var, font=FONT_LABEL,
                 bg=C_PANEL, fg=C_TEXT, insertbackground=C_GOLD,
                 relief="flat", bd=4).pack(side="left", fill="x", expand=True, padx=8)

        self._make_outline_btn(ctrl, "Explorar…", self._choose_folder).pack(side="left", padx=(0, 8))

        self._scan_btn = tk.Button(ctrl, text="Escanear", command=self._start_scan,
                                   font=FONT_BTN, fg=C_BG, bg=C_GOLD,
                                   activeforeground=C_BG, activebackground=C_GOLD,
                                   relief="flat", bd=0, padx=14, pady=6, cursor="hand2")
        self._scan_btn.pack(side="left")

        # Status
        tk.Label(self, textvariable=self.status_var, font=FONT_LABEL,
                 fg=C_MUTED, bg=C_BG, anchor="w").pack(fill="x", padx=16)

        # Toolbar
        toolbar = tk.Frame(self, bg=C_BG, padx=16, pady=8)
        toolbar.pack(fill="x")

        self._make_outline_btn(toolbar, "Colapsar todos", self._collapse_all).pack(side="left", padx=(0, 8))
        self._make_outline_btn(toolbar, "Expandir todos", self._expand_all).pack(side="left", padx=(0, 18))
        self._make_sort_btn(toolbar, "Por tamaño ↕", lambda: self._sort_groups("size")).pack(side="left", padx=(0, 8))
        self._make_sort_btn(toolbar, "Por copias ↕", lambda: self._sort_groups("copies")).pack(side="left")

        tk.Label(toolbar, textvariable=self.summary_var, font=FONT_BTN,
                 fg=C_GOLD, bg=C_BG).pack(side="right")

        # Scrollable results
        list_wrap = tk.Frame(self, bg=C_PANEL)
        list_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.canvas = tk.Canvas(list_wrap, bg=C_PANEL, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(list_wrap, orient="vertical", command=self.canvas.yview)
        sb.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=sb.set)

        self.results_frame = tk.Frame(self.canvas, bg=C_PANEL)
        self._cwin = self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        self.results_frame.bind("<Configure>", lambda _e: self._update_scrollregion())
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._cwin, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _make_outline_btn(self, master, text, command):
        return tk.Button(master, text=text, command=command,
                         font=FONT_BTN, fg=C_GOLD, bg=C_PANEL,
                         activeforeground=C_BG, activebackground=C_GOLD,
                         relief="solid", bd=1, padx=10, pady=5,
                         cursor="hand2", highlightthickness=0)

    def _make_sort_btn(self, master, text, command):
        """Botón de ordenamiento — estilo muted para diferenciarlo de los de vista."""
        return tk.Button(master, text=text, command=command,
                         font=FONT_BTN, fg=C_MUTED, bg=C_PANEL,
                         activeforeground=C_TEXT, activebackground=C_PANEL,
                         relief="solid", bd=1, padx=10, pady=5,
                         cursor="hand2", highlightthickness=0)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta a escanear")
        if folder:
            self.folder_var.set(folder)

    def _start_scan(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Duplicados", "Seleccioná una carpeta válida.")
            return
        self.duplicates = []
        self.expanded_groups.clear()
        self.selection_vars.clear()
        self._clear_results()
        self._update_summary()
        self.status_var.set("Iniciando escaneo…")
        self._scan_btn.config(state="disabled")
        if not self.finder.start(folder):
            self._scan_btn.config(state="normal")
            messagebox.showinfo("Duplicados", "Ya hay un escaneo en curso.")

    # ── Polling ───────────────────────────────────────────────────────────────

    def _poll_finder(self):
        try:
            while True:
                event, payload = self.finder.queue.get_nowait()
                if event == "status":
                    self.status_var.set(payload)
                elif event == "done":
                    self.duplicates = [self._normalize(item) for item in payload]
                    self.expanded_groups.clear()
                    self.selection_vars.clear()
                    self._render_results()
                    self.status_var.set("Escaneo completado.")
                    self._scan_btn.config(state="normal")
                elif event == "error":
                    self.status_var.set("Error en el escaneo.")
                    self._scan_btn.config(state="normal")
                    messagebox.showerror("Duplicados", payload)
                elif event == "cancelled":
                    self.status_var.set("Escaneo cancelado.")
                    self._scan_btn.config(state="normal")
        except Exception:
            pass
        self.after(150, self._poll_finder)

    def _normalize(self, item):
        paths = sorted(item["paths"])
        return {
            "filename": item.get("filename") or os.path.basename(paths[0]),
            "size": item["size"],
            "paths": paths,
        }

    # ── Render ────────────────────────────────────────────────────────────────

    def _render_results(self):
        self._clear_results()
        self._delete_btns.clear()
        self._group_widgets.clear()
        self._update_summary()

        if not self.duplicates:
            tk.Label(self.results_frame, text="No se encontraron archivos duplicados.",
                     bg=C_PANEL, fg=C_TEXT, font=FONT_LABEL
                     ).pack(anchor="w", padx=12, pady=16)
            self._update_scrollregion()
            return

        for idx, group in enumerate(self.duplicates):
            gid = self._gid(group)
            expanded = gid in self.expanded_groups

            card = tk.Frame(self.results_frame, bg=C_BG)
            card.pack(fill="x", padx=8, pady=5)

            # Header
            arrow = "▼" if expanded else "▶"
            header_txt = f"{arrow}  {group['filename']}  |  {self._fmt_size(group['size'])}  |  {len(group['paths'])} copias"
            hdr = tk.Frame(card, bg=C_BG, cursor="hand2")
            hdr.pack(fill="x")
            lbl = tk.Label(hdr, text=header_txt, font=FONT_BTN, fg=C_GOLD,
                           bg=C_BG, anchor="w", padx=12, pady=10, cursor="hand2")
            lbl.pack(fill="x")
            for w in (hdr, lbl):
                w.bind("<Button-1>", lambda _e, g=gid: self._toggle(g))

            tk.Frame(card, bg=C_GOLD, height=1).pack(fill="x", padx=12)

            # Body — siempre se crea, solo se packea si está expandido
            body = tk.Frame(card, bg=C_PANEL, padx=12, pady=10)
            if expanded:
                body.pack(fill="x")
            self._group_widgets[gid] = (lbl, body, card, idx)

            checked_count = 0
            for path in group["paths"]:
                var = self.selection_vars.setdefault(path, tk.BooleanVar(value=False))
                if var.get():
                    checked_count += 1

                row = tk.Frame(body, bg=C_PANEL, pady=3)
                row.pack(fill="x")

                tk.Checkbutton(row, variable=var,
                               command=lambda i=idx: self._refresh_delete_btn(i),
                               bg=C_PANEL, activebackground=C_PANEL,
                               fg=C_TEXT, selectcolor=C_PANEL,
                               highlightthickness=0, bd=0
                               ).pack(side="left", padx=(0, 8))

                tk.Label(row, text=os.path.basename(path), font=FONT_LABEL,
                         fg=C_TEXT, bg=C_PANEL, anchor="w", width=24
                         ).pack(side="left")

                tk.Label(row, text=os.path.dirname(path), font=FONT_MONO,
                         fg=C_MUTED, bg=C_PANEL, anchor="w"
                         ).pack(side="left", fill="x", expand=True, padx=(8, 12))

                self._make_outline_btn(row, "Abrir en Explorer",
                                       lambda p=path: self._open_in_explorer(p)
                                       ).pack(side="right")

            foot = tk.Frame(body, bg=C_PANEL)
            foot.pack(fill="x", pady=(6, 0))
            del_btn = tk.Button(foot, text="Eliminar seleccionados",
                                command=lambda i=idx: self._delete_selected(i),
                                font=FONT_BTN, bg=C_PANEL,
                                relief="solid", bd=1, padx=10, pady=5,
                                highlightthickness=0)
            del_btn.pack(side="right")
            self._delete_btns[idx] = del_btn
            self._apply_delete_btn_style(del_btn, checked_count > 0)

        self._update_scrollregion()

    # ── Group actions ─────────────────────────────────────────────────────────

    def _toggle(self, gid):
        widgets = self._group_widgets.get(gid)
        if not widgets:
            return
        lbl, body, card, idx = widgets
        group = self.duplicates[idx]
        header_base = f"  {group['filename']}  |  {self._fmt_size(group['size'])}  |  {len(group['paths'])} copias"
        if gid in self.expanded_groups:
            self.expanded_groups.discard(gid)
            body.pack_forget()
            lbl.config(text="▶" + header_base)
        else:
            self.expanded_groups.add(gid)
            body.pack(fill="x")
            lbl.config(text="▼" + header_base)
        self._update_scrollregion()

    def _expand_all(self):
        for gid, (lbl, body, card, idx) in self._group_widgets.items():
            if gid not in self.expanded_groups:
                self.expanded_groups.add(gid)
                group = self.duplicates[idx]
                body.pack(fill="x")
                lbl.config(text=f"▼  {group['filename']}  |  {self._fmt_size(group['size'])}  |  {len(group['paths'])} copias")
        self._update_scrollregion()

    def _collapse_all(self):
        for gid, (lbl, body, card, idx) in self._group_widgets.items():
            if gid in self.expanded_groups:
                group = self.duplicates[idx]
                body.pack_forget()
                lbl.config(text=f"▶  {group['filename']}  |  {self._fmt_size(group['size'])}  |  {len(group['paths'])} copias")
        self.expanded_groups.clear()
        self._update_scrollregion()

    def _sort_groups(self, key):
        rev = self.sort_directions[key]
        if key == "size":
            self.duplicates.sort(key=lambda g: (g["size"], len(g["paths"])), reverse=rev)
        else:
            self.duplicates.sort(key=lambda g: (len(g["paths"]), g["size"]), reverse=rev)
        self.sort_directions[key] = not rev
        # Reordenar cards sin destruirlos — sin parpadeo
        for group in self.duplicates:
            gid = self._gid(group)
            widgets = self._group_widgets.get(gid)
            if widgets:
                _, _, card, _ = widgets
                card.pack_forget()
                card.pack(fill="x", padx=8, pady=5)
        self._update_scrollregion()

    def _delete_selected(self, group_idx):
        group = self.duplicates[group_idx]
        orig_gid = self._gid(group)
        to_delete = [p for p in group["paths"]
                     if self.selection_vars.get(p) and self.selection_vars[p].get()]
        if not to_delete:
            return
        if not messagebox.askyesno(
            "Eliminar archivos",
            f"¿Eliminar {len(to_delete)} archivo(s)? Esta acción no se puede deshacer."
        ):
            return

        failed = []
        for path in to_delete:
            try:
                os.remove(path)
                self.selection_vars.pop(path, None)
            except OSError:
                failed.append(path)

        if failed:
            messagebox.showerror("Duplicados", f"No se pudieron eliminar {len(failed)} archivo(s).")

        remaining = [p for p in group["paths"] if p not in to_delete or p in failed]
        self.expanded_groups.discard(orig_gid)

        if len(remaining) <= 1:
            self.duplicates.pop(group_idx)
        else:
            group["paths"] = remaining
            self.expanded_groups.add(self._gid(group))

        self._render_results()

    def _refresh_delete_btn(self, group_idx):
        """Reconfigura solo el botón del grupo sin rerenderizar nada."""
        group = self.duplicates[group_idx]
        has_checked = any(
            self.selection_vars[p].get()
            for p in group["paths"]
            if p in self.selection_vars
        )
        btn = self._delete_btns.get(group_idx)
        if btn and btn.winfo_exists():
            self._apply_delete_btn_style(btn, has_checked)

    def _apply_delete_btn_style(self, btn, enabled: bool):
        if enabled:
            btn.config(fg="#C0504D", activeforeground=C_BG,
                       activebackground="#C0504D", cursor="hand2", state="normal")
        else:
            btn.config(fg="#555555", activeforeground="#555555",
                       activebackground=C_PANEL, cursor="", state="disabled")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clear_results(self):
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _open_in_explorer(self, path):
        try:
            norm = os.path.normpath(path)
            subprocess.Popen(f'explorer /select,"{norm}"', shell=True)
        except Exception:
            messagebox.showerror("Duplicados", f"No se pudo abrir:\n{path}")

    def _update_summary(self):
        n = len(self.duplicates)
        recoverable = sum(g["size"] * max(len(g["paths"]) - 1, 0) for g in self.duplicates)
        mb = recoverable / (1024 * 1024)
        self.summary_var.set(f"{n} grupo{'s' if n != 1 else ''}  |  Espacio recuperable: {mb:.2f} MB")

    def _update_scrollregion(self):
        self.results_frame.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _gid(self, group):
        return (group["filename"], group["size"], tuple(group["paths"]))

    def _fmt_size(self, size):
        size = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
            size /= 1024

    def _on_mousewheel(self, event):
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
