"""Duplicate finder: same name + size, confirmed by content hash. Nothing is deleted:
removed copies go to <folder>/_archivo/<date>/ like the mirror engine does."""
import hashlib
import os
import queue
import threading
from collections import defaultdict
from datetime import date

from core.executor import _free_target, _long, _move
from core.sync import ARCHIVE_DIR


def file_hash(path, stop=None, chunk=1 << 20):
    h = hashlib.blake2b(digest_size=16)
    with open(_long(path), "rb") as f:
        while block := f.read(chunk):
            if stop is not None and stop.is_set():
                return None
            h.update(block)
    return h.hexdigest()


def find_duplicates(folder, stop=None, status=None):
    """Return [{filename, size, paths}] of files with same name, size and content.
    Returns None if stopped. The _archivo folder at the root is skipped."""
    status = status or (lambda _msg: None)
    candidates = defaultdict(list)
    scanned = 0
    for root, dirs, files in os.walk(folder):
        if os.path.normcase(os.path.abspath(root)) == os.path.normcase(os.path.abspath(folder)):
            dirs[:] = [d for d in dirs if d.lower() != ARCHIVE_DIR]
        for name in files:
            if stop is not None and stop.is_set():
                return None
            path = os.path.join(root, name)
            try:
                candidates[(name.lower(), os.path.getsize(path))].append(path)
            except OSError:
                continue
            scanned += 1
            if scanned % 250 == 0:
                status(f"Escaneando… {scanned} archivos")

    to_check = [(k, p) for k, p in candidates.items() if len(p) > 1]
    duplicates = []
    for i, ((_, size), paths) in enumerate(to_check, 1):
        status(f"Comparando contenido… grupo {i} de {len(to_check)}")
        by_hash = defaultdict(list)
        for path in paths:
            try:
                digest = file_hash(path, stop)
            except OSError:
                continue
            if digest is None:
                return None
            by_hash[digest].append(path)
        for same in by_hash.values():
            if len(same) > 1:
                same.sort()
                duplicates.append({"filename": os.path.basename(same[0]), "size": size, "paths": same})

    duplicates.sort(key=lambda item: (item["filename"].lower(), item["size"]))
    return duplicates


def archive_copy(path, folder):
    """Move one copy to <folder>/_archivo/<today>/<relative path>. Returns the new path."""
    rel = os.path.relpath(path, folder)
    target = _free_target(os.path.join(folder, ARCHIVE_DIR, date.today().isoformat(), rel))
    _move(path, target)
    return target


class DuplicateFinder:
    def __init__(self):
        self._thread = None
        self._queue = queue.Queue()
        self._stop_event = threading.Event()

    @property
    def queue(self):
        return self._queue

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        self._stop_event.set()

    def start(self, folder_path):
        if self.is_running():
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scan_worker, args=(folder_path,), daemon=True)
        self._thread.start()
        return True

    def _scan_worker(self, folder_path):
        try:
            self._queue.put(("status", "Escaneando archivos..."))
            result = find_duplicates(folder_path, self._stop_event,
                                     lambda msg: self._queue.put(("status", msg)))
            self._queue.put(("cancelled", None) if result is None else ("done", result))
        except Exception as exc:
            self._queue.put(("error", str(exc)))
