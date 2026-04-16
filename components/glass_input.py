import tkinter as tk

from theme import COLORS


class GlassInput(tk.Frame):
    """Glassmorphic text entry with placeholder support."""

    def __init__(self, parent, placeholder="", width=200, **kwargs):
        kwargs.setdefault("bg", COLORS["carbon_elevated"])
        kwargs.setdefault("highlightbackground", COLORS["border_idle"])
        kwargs.setdefault("highlightthickness", 1)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, width=width, **kwargs)

        self.placeholder = placeholder
        self._focused = False
        self._placeholder_active = bool(placeholder)

        self._entry = tk.Entry(
            self,
            bg=COLORS["carbon_elevated"],
            fg=COLORS["smoke"] if self._placeholder_active else COLORS["platinum"],
            insertbackground=COLORS["gold_primary"],
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self._entry.pack(fill="both", expand=True, padx=10, pady=8)

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)

        if self._placeholder_active:
            self._show_placeholder()

    def _show_placeholder(self):
        if not self.placeholder:
            self._placeholder_active = False
            return

        self._entry.delete(0, tk.END)
        self._entry.insert(0, self.placeholder)
        self._entry.configure(fg=COLORS["smoke"])
        self._placeholder_active = True

    def _hide_placeholder(self):
        if not self._placeholder_active:
            return

        self._entry.delete(0, tk.END)
        self._entry.configure(fg=COLORS["platinum"])
        self._placeholder_active = False

    def _on_focus_in(self, _event=None):
        self._focused = True
        self.configure(highlightbackground=COLORS["gold_primary"])
        if self._placeholder_active:
            self._hide_placeholder()

    def _on_focus_out(self, _event=None):
        self._focused = False
        self.configure(highlightbackground=COLORS["border_idle"])
        if not self._entry.get():
            self._show_placeholder()

    def get(self) -> str:
        if self._placeholder_active:
            return ""
        return self._entry.get()

    def insert(self, index, text):
        if self._placeholder_active:
            self._hide_placeholder()
        self._entry.insert(index, text)

    def delete(self, first, last=None):
        if self._placeholder_active:
            self._hide_placeholder()
        self._entry.delete(first, last)
        if not self._focused and not self._entry.get():
            self._show_placeholder()

    def clear(self):
        self._entry.delete(0, tk.END)
        self._entry.configure(fg=COLORS["platinum"])
        self._placeholder_active = False
        if self.placeholder:
            self._show_placeholder()
