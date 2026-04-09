"""
Arch-Ive by SYMETRA — CDE Backup Tool
Entry point.
"""
import sys
import os

# Ensure the package root is on sys.path when run as a script
sys.path.insert(0, os.path.dirname(__file__))

from ui import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
