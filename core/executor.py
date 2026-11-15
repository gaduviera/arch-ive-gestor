"""Apply a sync Plan to the destination folder.

Order: moves -> archive deleted -> copies. A modified file is copied to a temp name
first; its old version is archived only right before the swap, so a failed or
cancelled run never leaves the destination without a copy.
Nothing is ever deleted: files leaving the destination go to
dest/_archivo/<YYYY-MM-DD>/<relpath>. Copies are written to a temp name and
renamed, so a cancelled or crashed run never leaves a half-written file.
"""
from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import date

from core.sync import ARCHIVE_DIR, TMP_SUFFIX, Plan


@dataclass
class RunResult:
    copied: int = 0
    moved: int = 0
    archived: int = 0
    errors: list[str] = field(default_factory=list)
    bytes_copied: int = 0
    duration_s: float = 0.0
    cancelled: bool = False


def _long(path: str) -> str:
    """Allow paths over 260 chars on Windows."""
    if os.name == "nt" and len(path) >= 240 and not path.startswith("\\\\?\\"):
        path = os.path.abspath(path)
        return "\\\\?\\UNC\\" + path[2:] if path.startswith("\\\\") else "\\\\?\\" + path
    return path


def _join(root: str, rel: str) -> str:
    return os.path.join(root, *rel.split("/"))


def _free_target(path: str) -> str:
    """Return path, or path with __1, __2... before the extension if taken."""
    if not os.path.exists(_long(path)):
        return path
    base, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(_long(f"{base}__{n}{ext}")):
        n += 1
    return f"{base}__{n}{ext}"


def _move(src: str, dst: str) -> None:
    os.makedirs(_long(os.path.dirname(dst)), exist_ok=True)
    os.replace(_long(src), _long(dst))


def _prune_empty(start_dir: str, stop: str) -> None:
    """Remove start_dir and empty parents, never `stop` itself."""
    stop = os.path.normcase(os.path.abspath(stop))
    d = os.path.abspath(start_dir)
    while os.path.normcase(d) != stop and os.path.normcase(d).startswith(stop):
        try:
            os.rmdir(_long(d))
        except OSError:
            return
        d = os.path.dirname(d)


def check_space(plan: Plan, dest: str) -> bool:
    probe = os.path.abspath(dest)
    while not os.path.exists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            return False
        probe = parent
    return shutil.disk_usage(probe).free >= plan.bytes_to_copy


def execute(plan: Plan, source: str, dest: str, on_progress=None, cancel=None) -> RunResult:
    """Apply plan. on_progress(done, total, rel); cancel has .is_set()."""
    res = RunResult()
    started = time.monotonic()
    archive_root = os.path.join(dest, ARCHIVE_DIR, date.today().isoformat())
    total = len(plan.moved) + len(plan.deleted) + len(plan.new) + len(plan.modified)
    done = 0
    emptied: set[str] = set()

    def step(rel: str) -> bool:
        nonlocal done
        done += 1
        if on_progress:
            on_progress(done, total, rel)
        return bool(cancel and cancel.is_set())

    def stopped() -> bool:
        if cancel and cancel.is_set():
            res.cancelled = True
        return res.cancelled

    os.makedirs(_long(dest), exist_ok=True)

    for old, new in plan.moved:
        if stopped():
            break
        try:
            target = _join(dest, new.rel)
            src_path = _join(dest, old.rel)
            if old.rel.lower() == new.rel.lower():
                # Case-only rename: same file on Windows, so go via a temp name (never archive it).
                tmp = src_path + TMP_SUFFIX
                _move(src_path, tmp)
                try:
                    _move(tmp, target)
                except OSError:
                    _move(tmp, src_path)  # put it back under its old name
                    raise
            else:
                if os.path.exists(_long(target)):  # should not happen; never overwrite
                    _move(target, _free_target(_join(archive_root, new.rel)))
                    res.archived += 1
                _move(src_path, target)
                emptied.add(os.path.dirname(src_path))
            res.moved += 1
        except OSError as exc:
            res.errors.append(f"Mover {old.rel} -> {new.rel}: {exc}")
        step(new.rel)

    for f in plan.deleted:
        if stopped():
            break
        try:
            src_path = _join(dest, f.rel)
            _move(src_path, _free_target(_join(archive_root, f.rel)))
            emptied.add(os.path.dirname(src_path))
            res.archived += 1
        except OSError as exc:
            res.errors.append(f"Archivar {f.rel}: {exc}")
        step(f.rel)

    olds = {s.rel: d for s, d in plan.modified}
    for f in list(plan.new) + [s for s, _ in plan.modified]:
        if stopped():
            break
        target = _join(dest, f.rel)
        tmp = target + TMP_SUFFIX
        archived_to = None
        try:
            os.makedirs(_long(os.path.dirname(target)), exist_ok=True)
            shutil.copy2(_long(_join(source, f.rel)), _long(tmp))
            if f.rel in olds:  # archive the old version only now that the new one is safe
                archived_to = _free_target(_join(archive_root, f.rel))
                _move(target, archived_to)
            os.replace(_long(tmp), _long(target))
            if archived_to:
                res.archived += 1
            res.copied += 1
            res.bytes_copied += f.size
        except OSError as exc:
            res.errors.append(f"Copiar {f.rel}: {exc}")
            if archived_to and not os.path.exists(_long(target)):
                try:  # swap failed after archiving: put the old version back
                    _move(archived_to, target)
                except OSError:
                    pass
            try:
                os.remove(_long(tmp))
            except OSError:
                pass
        step(f.rel)

    for d in sorted(emptied, key=len, reverse=True):
        _prune_empty(d, dest)
    res.duration_s = round(time.monotonic() - started, 2)
    return res
