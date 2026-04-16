import tkinter as tk
import sys
import os

# Allow importing theme from root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from theme import COLORS, rgb_to_hex, hex_to_rgb

# Background fills (approximated, no alpha in Canvas)
_BG_NORMAL   = '#2A2010'
_BG_HOVER    = '#3D3018'
_BG_ACTIVE   = COLORS.get('gold_primary', '#C6A85E')
_BG_DISABLED = COLORS.get('carbon_base', '#111111')

_BORDER_NORMAL   = COLORS.get('gold_primary', '#C6A85E')
_BORDER_HOVER    = COLORS.get('gold_primary', '#C6A85E')
_BORDER_ACTIVE   = COLORS.get('gold_primary', '#C6A85E')
_BORDER_DISABLED = '#242424'

_TEXT_NORMAL   = COLORS.get('platinum', '#F5F5F5')
_TEXT_DISABLED = '#888888'

_FONT = ('Segoe UI', 10)


class GlassButton(tk.Canvas):
    """Glassmorphic button using SYMETRA branding."""

    def __init__(self, parent, text='Click', command=None,
                 width=120, height=36, **kwargs):
        kwargs.setdefault('bg', COLORS.get('carbon_elevated', '#1A1A1A'))
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bd', 0)
        super().__init__(parent, width=width, height=height, **kwargs)

        self.text = text
        self.command = command
        self._state = 'normal'

        self.bind('<Enter>',          self._on_enter)
        self.bind('<Leave>',          self._on_leave)
        self.bind('<ButtonPress-1>',  self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)

        self.draw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        self.delete('all')
        w = int(self['width'])
        h = int(self['height'])

        state = self._state

        if state == 'normal':
            fill   = _BG_NORMAL
            border = _BORDER_NORMAL
            text_color = _TEXT_NORMAL
        elif state == 'hover':
            fill   = _BG_HOVER
            border = _BORDER_HOVER
            text_color = _TEXT_NORMAL
        elif state == 'active':
            fill   = _BG_ACTIVE
            border = _BORDER_ACTIVE
            text_color = COLORS.get('carbon_base', '#111111')
        else:  # disabled
            fill   = _BG_DISABLED
            border = _BORDER_DISABLED
            text_color = _TEXT_DISABLED

        # Background rectangle
        self.create_rectangle(
            0, 0, w, h,
            fill=fill, outline=border, width=1,
            tags='btn_bg'
        )

        # Centered label
        self.create_text(
            w // 2, h // 2,
            text=self.text,
            fill=text_color,
            font=_FONT,
            tags='btn_text'
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_enter(self, event=None):
        if self._state != 'disabled':
            self._state = 'hover'
            self.draw()

    def _on_leave(self, event=None):
        if self._state != 'disabled':
            self._state = 'normal'
            self.draw()

    def _on_press(self, event=None):
        if self._state != 'disabled':
            self._state = 'active'
            self.draw()
            if self.command is not None:
                self.command()

    def _on_release(self, event=None):
        if self._state != 'disabled':
            self._state = 'hover'
            self.draw()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def configure_text(self, text):
        """Update button label and redraw."""
        self.text = text
        self.draw()

    def set_state(self, state):
        """Set button state: 'normal', 'hover', 'active', or 'disabled'."""
        valid = {'normal', 'hover', 'active', 'disabled'}
        if state not in valid:
            raise ValueError(f'Invalid state {state!r}. Must be one of {valid}.')
        self._state = state
        self.draw()
