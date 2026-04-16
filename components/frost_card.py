"""FrostCard — glassmorphic card container (tkinter Canvas subclass)."""
import tkinter as tk
from theme import COLORS, hex_to_rgb, with_opacity

try:
    from PIL import Image, ImageFilter, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

_BG = COLORS["carbon_elevated"]   # #1A1A1A
_BORDER = COLORS["gold_primary"]   # #C6A85E
_RADIUS = 10


class FrostCard(tk.Canvas):
    """Frosted-glass card with rounded border and optional PIL blur overlay.

    Parameters
    ----------
    parent : tk widget
    width, height : int  — initial size
    padding : int        — inner content padding (default 12)
    blur_radius : int    — GaussianBlur radius for frost effect (default 4)
    """

    def __init__(self, parent, width: int = 300, height: int = 200,
                 padding: int = 12, blur_radius: int = 4, **kwargs):
        kwargs.setdefault("bg", _BG)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, width=width, height=height, **kwargs)

        self.padding = padding
        self.blur_radius = blur_radius
        self._photo = None   # keep PIL PhotoImage alive

        self.bind("<Configure>", lambda _e: self.draw())

    # ------------------------------------------------------------------
    def draw(self):
        """Redraw the card background and border."""
        self.delete("frost_bg")
        w = self.winfo_width() or int(self.cget("width"))
        h = self.winfo_height() or int(self.cget("height"))

        if _PIL_AVAILABLE:
            self._draw_pil(w, h)
        else:
            self._draw_fallback(w, h)

    def _draw_pil(self, w: int, h: int):
        """Render frosted overlay using PIL blur + semi-transparent fill."""
        try:
            # Base: dark semi-transparent overlay
            r, g, b, a = with_opacity(_BG, 0.60)
            overlay = Image.new("RGBA", (w, h), (r, g, b, a))
            blurred = overlay.filter(ImageFilter.GaussianBlur(self.blur_radius))
            draw_img = blurred.copy()
            self._photo = ImageTk.PhotoImage(draw_img, master=self)
            self.create_image(0, 0, anchor="nw", image=self._photo, tags="frost_bg")
        except Exception:
            # Fallback for headless/test environments
            self._draw_fallback(w, h)
            return

        # Rounded-rect border
        self._draw_rounded_border(w, h)

    def _draw_fallback(self, w: int, h: int):
        """Simple fallback when PIL is unavailable."""
        self.create_rectangle(0, 0, w, h, fill=_BG, outline="", tags="frost_bg")
        self._draw_rounded_border(w, h)

    def _draw_rounded_border(self, w: int, h: int):
        r = _RADIUS
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90,
                        outline=_BORDER, style="arc", tags="frost_bg")
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90,
                        outline=_BORDER, style="arc", tags="frost_bg")
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90,
                        outline=_BORDER, style="arc", tags="frost_bg")
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90,
                        outline=_BORDER, style="arc", tags="frost_bg")
        self.create_line(r, 0, w-r, 0, fill=_BORDER, tags="frost_bg")
        self.create_line(r, h, w-r, h, fill=_BORDER, tags="frost_bg")
        self.create_line(0, r, 0, h-r, fill=_BORDER, tags="frost_bg")
        self.create_line(w, r, w, h-r, fill=_BORDER, tags="frost_bg")

    # ------------------------------------------------------------------
    def add_widget(self, widget: tk.Widget, x: int = None, y: int = None):
        """Place a child widget inside the card at (x, y) or at padding offset."""
        if x is None:
            x = self.padding
        if y is None:
            y = self.padding
        self.create_window(x, y, anchor="nw", window=widget)
