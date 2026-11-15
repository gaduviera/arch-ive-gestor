"""Mirror pairs: one source folder synced into one destination folder.

Each mirror is an independent pair with its own name, mode and exclusions.
Stored in %APPDATA%\\Arch-Ive\\mirrors.json. The list starts empty.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from core.paths import MIRRORS_FILE
from core.sync import DEFAULT_EXCLUDES, MODES


def new_mirror(name: str, source: str, dest: str, mode: str = "mirror",
               pinned: bool = True, exclude: list[str] | None = None) -> dict:
    return {
        "name": name.strip(),
        "source": source.strip(),
        "dest": dest.strip(),
        "mode": mode,
        "pinned": pinned,
        "exclude": list(DEFAULT_EXCLUDES if exclude is None else exclude),
        "last_run": None,
        "last_summary": None,
    }


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p)).rstrip("\\/")


def _overlap(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    return a == b or a.startswith(b + os.sep) or b.startswith(a + os.sep)


def validate(m: dict, others: list[dict]) -> list[str]:
    """Blocking problems. `others` = every other mirror (not m itself)."""
    errs = []
    if not m.get("name", "").strip():
        errs.append("Ponle un nombre al espejo.")
    elif any(o["name"].lower() == m["name"].strip().lower() for o in others):
        errs.append(f"Ya existe un espejo llamado «{m['name']}».")
    if not m.get("source") or not m.get("dest"):
        errs.append("Elige carpeta origen y carpeta destino.")
        return errs
    if m.get("mode") not in MODES:
        errs.append(f"Modo desconocido: {m.get('mode')}")
    if _overlap(m["source"], m["dest"]):
        errs.append("Origen y destino no pueden ser la misma carpeta ni estar una dentro de la otra.")
    for o in others:
        if _overlap(m["dest"], o["dest"]):
            errs.append(f"El destino choca con el del espejo «{o['name']}».")
    return errs


def warnings(m: dict, others: list[dict]) -> list[str]:
    return [f"Comparte origen con el espejo «{o['name']}»."
            for o in others if m.get("source") and _norm(m["source"]) == _norm(o["source"])]


class MirrorStore:
    def __init__(self, path: Path | str = MIRRORS_FILE):
        self.path = Path(path)
        self.mirrors: list[dict] = []
        self.selected: str | None = None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.mirrors = [m for m in data.get("mirrors", []) if isinstance(m, dict) and m.get("name")]
            self.selected = data.get("selected")
        except (OSError, ValueError, AttributeError):
            pass

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"selected": self.selected, "mirrors": self.mirrors},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def get(self, name: str | None) -> dict | None:
        if not name:
            return None
        return next((m for m in self.mirrors if m["name"].lower() == name.lower()), None)

    def ordered(self) -> list[dict]:
        return sorted(self.mirrors, key=lambda m: (not m.get("pinned"), m["name"].lower()))

    def pinned(self) -> list[dict]:
        return [m for m in self.ordered() if m.get("pinned")]

    def upsert(self, mirror: dict, old_name: str | None = None) -> None:
        key = (old_name or mirror["name"]).lower()
        others = [m for m in self.mirrors if m["name"].lower() != key]
        errs = validate(mirror, others)
        if errs:
            raise ValueError("\n".join(errs))
        existing = self.get(old_name or mirror["name"])
        if existing:
            self.mirrors[self.mirrors.index(existing)] = mirror
        else:
            self.mirrors.append(mirror)
        if old_name and self.selected and self.selected.lower() == old_name.lower():
            self.selected = mirror["name"]
        self.save()

    def delete(self, name: str) -> None:
        m = self.get(name)
        if m:
            self.mirrors.remove(m)
            if self.selected and self.selected.lower() == name.lower():
                self.selected = None
            self.save()

    def record(self, name: str, summary: dict | None = None, ran: bool = False) -> None:
        m = self.get(name)
        if not m:
            return
        if summary is not None:
            m["last_summary"] = summary
        if ran:
            m["last_run"] = datetime.now().isoformat(timespec="seconds")
        self.save()
