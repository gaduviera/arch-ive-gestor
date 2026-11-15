import os
import threading
import queue
from collections import defaultdict


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
        self._thread = threading.Thread(
            target=self._scan_worker,
            args=(folder_path,),
            daemon=True,
        )
        self._thread.start()
        return True

    def _scan_worker(self, folder_path):
        try:
            self._queue.put(("status", "Escaneando archivos..."))
            groups = defaultdict(list)
            scanned = 0

            for root, _, files in os.walk(folder_path):
                if self._stop_event.is_set():
                    self._queue.put(("cancelled", None))
                    return
                for name in files:
                    if self._stop_event.is_set():
                        self._queue.put(("cancelled", None))
                        return
                    path = os.path.join(root, name)
                    try:
                        size = os.path.getsize(path)
                        groups[(name.lower(), size)].append(path)
                        scanned += 1
                        if scanned % 250 == 0:
                            self._queue.put(("status", f"Escaneando… {scanned} archivos"))
                    except OSError:
                        continue

            duplicates = []
            for (filename, size), paths in groups.items():
                if len(paths) > 1:
                    duplicates.append({
                        "filename": os.path.basename(paths[0]),
                        "size": size,
                        "paths": sorted(paths),
                    })

            duplicates.sort(key=lambda item: (item["filename"].lower(), item["size"]))
            self._queue.put(("done", duplicates))
        except Exception as exc:
            self._queue.put(("error", str(exc)))
