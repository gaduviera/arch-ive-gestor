import subprocess
import threading
from datetime import datetime
from pathlib import Path

from paths import LOGS_DIR


def build_robocopy_cmd(source: str, dest: str, days: int, dry_run: bool = False) -> list[str]:
    cmd = [
        "robocopy",
        source,
        dest,
        "/E",
        f"/MAXAGE:{days}",
        "/XO",
        "/MT:8",
        "/NP",
        "/UNICODE",
    ]
    if dry_run:
        cmd.append("/L")
    return cmd


def run_backup(
    source: str,
    dest: str,
    days: int,
    dry_run: bool,
    on_line,
    on_done,
) -> threading.Thread:
    """Launch robocopy in a background thread.

    on_line(line: str) is called for each output line.
    on_done(success: bool, log_path: str) is called when finished.
    """
    cmd = build_robocopy_cmd(source, dest, days, dry_run)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "dryrun" if dry_run else "backup"
    log_path = LOGS_DIR / f"{mode}_{timestamp}.log"

    def _worker():
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            lines = []
            for line in proc.stdout:
                stripped = line.rstrip()
                if stripped:
                    lines.append(stripped)
                    on_line(stripped)
            proc.wait()
            # Robocopy exit codes 0-7 are success/informational
            success = proc.returncode < 8
            log_path.write_text("\n".join(lines), encoding="utf-8")
            on_done(success, str(log_path))
        except FileNotFoundError:
            on_line("[ERROR] robocopy no encontrado. Asegurate de ejecutar en Windows.")
            on_done(False, "")
        except Exception as exc:
            on_line(f"[ERROR] {exc}")
            on_done(False, "")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
