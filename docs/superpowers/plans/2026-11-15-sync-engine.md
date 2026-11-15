# Sync engine + espejos — Implementation Plan

> Executed inline in the same session (user asked to implement directly).
> Steps use checkbox syntax.

**Goal:** Turn Arch-Ive into a mirror-pair copier that detects new / modified / moved / deleted files and never loses data.

**Architecture:** Pure logic in `core/` (scan → plan → execute, mirrors config, history). Tkinter UI in `ui/`. Stateless comparison of source tree against dest tree; archive instead of delete.

**Tech Stack:** Python 3.11+, tkinter, stdlib only for core (`os.scandir`, `shutil.copy2`, `fnmatch`, `json`). pytest for tests. Pillow/reportlab optional (PDF export).

**Spec:** `docs/superpowers/specs/2026-11-09-sync-engine-design.md`

## Global Constraints

- No new runtime dependencies. Core has no tkinter import.
- User data only under `%APPDATA%\Arch-Ive` (`core/paths.py`).
- Never delete a user file: anything leaving dest goes to `dest/_archivo/<YYYY-MM-DD>/<relpath>`.
- mtime tolerance 2 s; path comparison case-insensitive.
- UI copy in Spanish; SYMETRA palette from `ui/theme.py`.

---

### Task 1: Reorganize into `core/` and `ui/`

Files: `git mv` paths.py→core/paths.py, reports_engine.py→core/history.py,
duplicate_finder.py→core/duplicates.py, export_{csv,json,pdf}.py→core/exporters.py (merged),
ui.py→ui/app.py, duplicates_tab.py/reports_tab.py/theme.py→ui/, reports_ui.py +
BarChart→ui/widgets.py. Delete backup_engine.py, config.py, components/, glass/frost
tests, LineChart test. Update ArchIve.spec datas.

- [ ] Move files, rewrite imports
- [ ] `pytest` green (existing suites minus deleted ones)
- [ ] Commit `refactor: split into core/ and ui/ packages`

### Task 2: `core/sync.py` — scan + plan

Interfaces (produces):
- `DEFAULT_EXCLUDES: list[str]`
- `ARCHIVE_DIR = "_archivo"`
- `scan(root: str, exclude: list[str], skip_archive: bool=False) -> dict[str, FileInfo]` — key = relpath with `/`, `FileInfo(rel, size, mtime)` (mtime float seconds).
- `build_plan(src: dict, dst: dict, mode: str) -> Plan`
- `Plan` dataclass: `new, modified, moved: list[tuple[src_rel, dst_rel]], deleted, kept_orphans, unchanged: int`; properties `bytes_to_copy`, `bytes_saved`, `is_empty`, `counts() -> dict`.
- `analyze(mirror: dict) -> Plan` — validates source exists and non-empty (raises `SyncError`).

Tests (`tests/test_sync.py`): new, modified, unchanged within 2 s, moved, renamed, ambiguous move falls back, deleted (mirror) vs kept (add_only), excludes, case-insensitive match, `_archivo` ignored, empty source raises.

### Task 3: `core/executor.py` — apply plan

Interfaces:
- `execute(plan, source, dest, on_progress=None, cancel=None) -> RunResult` — order moves → archive → copy; copy via `<file>.archive-tmp` + `os.replace`; archive with `__N` suffix on collision; remove emptied dirs; per-file errors collected.
- `RunResult` dataclass: `copied, moved, archived, errors: list[str], bytes_copied, duration_s, cancelled`.
- `check_space(plan, dest) -> bool`.

Tests (`tests/test_executor.py`): full run then re-plan empty; modified archives old version; collision suffix; empty dirs cleaned; cancel stops; mtime preserved.

### Task 4: `core/mirrors.py` — config + validation + migration

Interfaces:
- `MirrorStore(path=MIRRORS_FILE)`: `.mirrors` list, `.selected`, `get(name)`, `upsert(mirror, old_name=None)`, `delete(name)`, `pinned()`, `save()`.
- `new_mirror(name, source, dest, mode="mirror", pinned=True, exclude=None) -> dict`
- `validate(mirror, others) -> list[str]` errors; `warnings(mirror, others) -> list[str]`.
- Migration from legacy `config.json` → mirror "Principal".

Tests (`tests/test_mirrors.py`).

### Task 5: UI — `ui/sync_tab.py` + history wiring

Two-column tab per spec; mirror dialog; analyze one / analyze pinned; detail view; run with progress; history event per mirror; Reports refresh. Replace backup tab in `ui/app.py`.

### Task 6: Cleanup + docs

README rewritten to the mirror concept; CLAUDE.md structure; spec status. Full test run + launch app smoke check.
