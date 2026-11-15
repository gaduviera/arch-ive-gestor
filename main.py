"""Arch-Ive by SYMETRA — mirror folder pairs. Entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import App  # noqa: E402


def main():
    if sys.platform == "win32":
        try:  # crisp text on scaled displays
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    App().mainloop()


if __name__ == "__main__":
    main()
