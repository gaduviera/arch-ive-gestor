"""Scan two folder trees and plan what a sync must do.

Stateless: every run compares the source tree against the destination tree.
Paths are matched case-insensitively (Windows). Two files are "the same" when
size matches and mtime differs by at most MTIME_TOLERANCE seconds (FAT/exFAT
store mtime with 2 s resolution).
"""
from __future__ import annotations

import fnmatch
import os
from collections import defaultdict
from dataclasses import dataclass, field

ARCHIVE_DIR = "_archivo"
TMP_SUFFIX = ".archive-tmp"
MTIME_TOLERANCE = 2.0
DEFAULT_EXCLUDES = ["~$*", "*.tmp", "desktop.ini", "Thumbs.db", ".~lock*"]
MODES = ("mirror", "add_only")


class SyncError(Exception):
    """A mirror cannot be analyzed (missing/empty source, bad config)."""


@dataclass(frozen=True)
class FileInfo:
    rel: str        # relative path with "/" separators, original casing
    size: int
    mtime: float


@dataclass
class Plan:
    new: list[FileInfo] = field(default_factory=list)                    # source files to copy
    modified: list[tuple[FileInfo, FileInfo]] = field(default_factory=list)  # (source, dest)
    moved: list[tuple[FileInfo, FileInfo]] = field(default_factory=list)     # (dest old, source new)
    deleted: list[FileInfo] = field(default_factory=list)                # dest files to archive
    kept: list[FileInfo] = field(default_factory=list)                   # dest orphans left in place
    unchanged: int = 0
    scan_errors: list[str] = field(default_factory=list)                 # unreadable source folders
    # new source files that look like several dest orphans (same size+mtime): (source, [dest candidates])
    ambiguous: list[tuple[FileInfo, list[FileInfo]]] = field(default_factory=list)

    def review_items(self) -> list[tuple[str, FileInfo, FileInfo]]:
        """Doubtful cases the user should look at first: (kind, source, dest)."""
        items = [("Modificado", s, d) for s, d in self.modified]
        items += [("Gemelo", s, o) for s, cands in self.ambiguous for o in cands]
        return items

    @property
    def review_count(self) -> int:
        return len(self.modified) + len(self.ambiguous)

    @property
    def bytes_to_copy(self) -> int:
        return sum(f.size for f in self.new) + sum(s.size for s, _ in self.modified)

    @property
    def bytes_saved(self) -> int:
        return sum(old.size for old, _ in self.moved)

    @property
    def is_empty(self) -> bool:
        return not (self.new or self.modified or self.moved or self.deleted)

    def counts(self) -> dict:
        return {
            "new": len(self.new),
            "modified": len(self.modified),
            "moved": len(self.moved),
            "archived": len(self.deleted) + len(self.modified),
            "kept": len(self.kept),
            "unchanged": self.unchanged,
            "bytes_to_copy": self.bytes_to_copy,
            "bytes_saved": self.bytes_saved,
        }


def _excluded(name: str, patterns: list[str]) -> bool:
    low = name.lower()
    return any(fnmatch.fnmatchcase(low, p.lower()) for p in patterns)


def scan(root: str, exclude: list[str], skip_archive: bool = False) -> tuple[dict[str, FileInfo], list[str]]:
    """Return ({rel.lower(): FileInfo}, [unreadable folder rels]).

    A missing root yields an empty tree (dest that does not exist yet).
    """
    files: dict[str, FileInfo] = {}
    errors: list[str] = []
    if not os.path.isdir(root):
        return files, errors
    stack = [""]
    while stack:
        rel_dir = stack.pop()
        abs_dir = os.path.join(root, rel_dir) if rel_dir else root
        try:
            with os.scandir(abs_dir) as it:
                entries = list(it)
        except OSError:
            errors.append(rel_dir)
            continue
        for e in entries:
            rel = f"{rel_dir}/{e.name}" if rel_dir else e.name
            if _excluded(e.name, exclude) or e.name.endswith(TMP_SUFFIX):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if not (skip_archive and not rel_dir and e.name.lower() == ARCHIVE_DIR):
                        stack.append(rel)
                elif e.is_file(follow_symlinks=False):
                    st = e.stat(follow_symlinks=False)
                    files[rel.lower()] = FileInfo(rel, st.st_size, st.st_mtime)
            except OSError:
                errors.append(rel)
    return files, errors


def _same(a: FileInfo, b: FileInfo) -> bool:
    return a.size == b.size and abs(a.mtime - b.mtime) <= MTIME_TOLERANCE


def _under(rel: str, folders: list[str]) -> bool:
    low = rel.lower()
    return any(f == "" or low.startswith(f.lower() + "/") for f in folders)


def build_plan(src: dict[str, FileInfo], dst: dict[str, FileInfo], mode: str = "mirror",
               src_errors: list[str] | None = None) -> Plan:
    if mode not in MODES:
        raise SyncError(f"Modo desconocido: {mode}")
    plan = Plan(scan_errors=list(src_errors or []))
    missing: list[FileInfo] = []
    for key, s in src.items():
        d = dst.get(key)
        if d is None:
            missing.append(s)
        elif _same(s, d):
            # Only the file name's case can be fixed in place; folder casing is left alone.
            if s.rel.rsplit("/", 1)[-1] != d.rel.rsplit("/", 1)[-1]:
                plan.moved.append((d, s))
            else:
                plan.unchanged += 1
        else:
            plan.modified.append((s, d))
    orphans = [d for key, d in dst.items() if key not in src]

    # Pair each missing file with exactly one orphan of same size+mtime, and
    # that orphan with exactly one missing file. Anything ambiguous is not a move.
    by_size: dict[int, list[FileInfo]] = defaultdict(list)
    for o in orphans:
        by_size[o.size].append(o)
    cand_m = {m: [o for o in by_size.get(m.size, ()) if _same(m, o)] for m in missing}
    cand_o: dict[FileInfo, list[FileInfo]] = defaultdict(list)
    for m, cs in cand_m.items():
        for o in cs:
            cand_o[o].append(m)
    paired: set[FileInfo] = set()
    for m, cs in cand_m.items():
        if len(cs) == 1 and len(cand_o[cs[0]]) == 1:
            plan.moved.append((cs[0], m))
            paired.update((m, cs[0]))

    plan.new = [m for m in missing if m not in paired]
    plan.ambiguous = [(m, cand_m[m]) for m in plan.new if cand_m[m]]
    for o in orphans:
        if o in paired:
            continue
        # Never archive what we could not see in the source (unreadable folder).
        if mode == "mirror" and not _under(o.rel, plan.scan_errors):
            plan.deleted.append(o)
        else:
            plan.kept.append(o)
    for lst in (plan.new, plan.deleted, plan.kept):
        lst.sort(key=lambda f: f.rel.lower())
    plan.modified.sort(key=lambda p: p[0].rel.lower())
    plan.moved.sort(key=lambda p: p[1].rel.lower())
    return plan


def analyze(mirror: dict) -> Plan:
    """Scan both sides of a mirror and build its plan. Raises SyncError."""
    source, dest = mirror["source"], mirror["dest"]
    if not os.path.isdir(source):
        raise SyncError(f"Origen no disponible: {source}")
    exclude = mirror.get("exclude") or []
    src, src_err = scan(source, exclude)
    if "" in src_err:
        raise SyncError(f"No se puede leer el origen: {source}")
    if not src:
        raise SyncError(f"El origen está vacío: {source}")
    dst, _ = scan(dest, exclude, skip_archive=True)
    return build_plan(src, dst, mirror.get("mode", "mirror"), src_err)
