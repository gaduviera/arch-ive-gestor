"""Tests for core.executor — applying a plan on real temp folders."""
import os
import threading
from datetime import date

from core.executor import check_space, execute
from core.sync import ARCHIVE_DIR, analyze

from tests.test_sync import make


def mirror(src, dst, mode="mirror"):
    return {"source": str(src), "dest": str(dst), "mode": mode, "exclude": []}


def read(path):
    with open(path, "rb") as f:
        return f.read()


def archive_root(dst):
    return dst / ARCHIVE_DIR / date.today().isoformat()


def test_full_run_then_second_plan_is_empty(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "a/1.txt", b"one")
    make(src, "b/2.txt", b"two")
    m = mirror(src, dst)
    res = execute(analyze(m), m["source"], m["dest"])
    assert res.copied == 2 and not res.errors
    assert read(dst / "a" / "1.txt") == b"one"
    assert analyze(m).is_empty


def test_mtime_preserved_and_no_tmp_left(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "f.bin", b"data", mtime=1_600_000_000)
    m = mirror(src, dst)
    execute(analyze(m), m["source"], m["dest"])
    assert int(os.path.getmtime(dst / "f.bin")) == 1_600_000_000
    assert os.listdir(dst) == ["f.bin"]


def test_move_applied_without_copy(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "new/place/p.rvt", b"12345", mtime=1_600_000_000)
    make(dst, "old/p.rvt", b"12345", mtime=1_600_000_000)
    m = mirror(src, dst)
    res = execute(analyze(m), m["source"], m["dest"])
    assert res.moved == 1 and res.copied == 0 and res.bytes_copied == 0
    assert (dst / "new" / "place" / "p.rvt").exists()
    assert not (dst / "old").exists()  # emptied folder removed


def test_modified_archives_old_version(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "doc.txt", b"version 2", mtime=1_700_000_100)
    make(dst, "doc.txt", b"v1", mtime=1_700_000_000)
    m = mirror(src, dst)
    res = execute(analyze(m), m["source"], m["dest"])
    assert res.archived == 1 and res.copied == 1
    assert read(dst / "doc.txt") == b"version 2"
    assert read(archive_root(dst) / "doc.txt") == b"v1"


def test_deleted_archived_with_collision_suffix(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "keep.txt")
    make(dst, "keep.txt")
    make(dst, "sub/gone.txt", b"new orphan")
    make(dst, f"{ARCHIVE_DIR}/{date.today().isoformat()}/sub/gone.txt", b"earlier")
    m = mirror(src, dst)
    res = execute(analyze(m), m["source"], m["dest"])
    assert res.archived == 1
    arch = archive_root(dst) / "sub"
    assert read(arch / "gone.txt") == b"earlier"
    assert read(arch / "gone__1.txt") == b"new orphan"
    assert not (dst / "sub").exists()


def test_add_only_keeps_orphans(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "a.txt")
    make(dst, "extra.txt", b"different size")
    m = mirror(src, dst, mode="add_only")
    res = execute(analyze(m), m["source"], m["dest"])
    assert res.archived == 0 and (dst / "extra.txt").exists()


def test_cancel_stops_before_work(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    for i in range(5):
        make(src, f"f{i}.txt")
    m = mirror(src, dst)
    cancel = threading.Event()
    cancel.set()
    res = execute(analyze(m), m["source"], m["dest"], cancel=cancel)
    assert res.cancelled and res.copied == 0


def test_progress_reports_every_step(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "a.txt")
    make(src, "b.txt")
    m = mirror(src, dst)
    seen = []
    execute(analyze(m), m["source"], m["dest"], on_progress=lambda d, t, rel: seen.append((d, t)))
    assert seen[-1] == (2, 2)


def test_check_space(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "a.txt")
    assert check_space(analyze(mirror(src, dst)), str(dst))


def test_failed_copy_of_modified_keeps_old_version_in_place(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "doc.txt", b"version 2", mtime=1_700_000_100)
    make(dst, "doc.txt", b"v1", mtime=1_700_000_000)
    m = mirror(src, dst)
    plan = analyze(m)
    os.remove(src / "doc.txt")  # source vanishes between analyze and sync
    res = execute(plan, m["source"], m["dest"])
    assert len(res.errors) == 1 and res.copied == 0 and res.archived == 0
    assert read(dst / "doc.txt") == b"v1"
    assert not archive_root(dst).exists()
    assert not any(n.endswith(".archive-tmp") for n in os.listdir(dst))


def test_cancel_midway_leaves_unprocessed_modified_in_place(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    for n in "abc":
        make(src, f"{n}.txt", b"new!", mtime=1_700_000_100)
        make(dst, f"{n}.txt", b"old", mtime=1_700_000_000)
    m = mirror(src, dst)
    ev = threading.Event()
    res = execute(analyze(m), m["source"], m["dest"],
                  on_progress=lambda d, t, rel: ev.set(), cancel=ev)
    assert res.cancelled and res.copied == 1
    assert sorted(os.listdir(dst)) == ["_archivo", "a.txt", "b.txt", "c.txt"]
