"""Tests for core.sync — scanning and planning."""
import os

import pytest

from core.sync import ARCHIVE_DIR, SyncError, analyze, build_plan, scan


def make(root, rel, data=b"x", mtime=1_700_000_000):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    os.utime(path, (mtime, mtime))
    return path


def plan_for(src, dst, mode="mirror", exclude=()):
    s, s_err = scan(str(src), list(exclude))
    d, _ = scan(str(dst), list(exclude), skip_archive=True)
    return build_plan(s, d, mode, s_err)


def rels(items):
    return sorted(i.rel for i in items)


def test_new_file(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "a/new.txt")
    dst.mkdir()
    p = plan_for(src, dst)
    assert rels(p.new) == ["a/new.txt"]
    assert p.bytes_to_copy == 1


def test_unchanged_within_tolerance(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "f.txt", mtime=1_700_000_000)
    make(dst, "f.txt", mtime=1_700_000_002)
    p = plan_for(src, dst)
    assert p.unchanged == 1 and p.is_empty


def test_modified_by_size_or_mtime(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "size.txt", b"longer")
    make(dst, "size.txt", b"x")
    make(src, "time.txt", mtime=1_700_000_100)
    make(dst, "time.txt", mtime=1_700_000_000)
    p = plan_for(src, dst)
    assert sorted(s.rel for s, _ in p.modified) == ["size.txt", "time.txt"]


def test_moved_file_detected(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "nuevo/lugar/plano.rvt", b"12345", mtime=1_600_000_000)
    make(dst, "viejo/plano.rvt", b"12345", mtime=1_600_000_000)
    p = plan_for(src, dst)
    assert [(old.rel, new.rel) for old, new in p.moved] == [("viejo/plano.rvt", "nuevo/lugar/plano.rvt")]
    assert not p.new and not p.deleted
    assert p.bytes_saved == 5 and p.bytes_to_copy == 0


def test_renamed_file_detected(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "carpeta/v2.pdf", b"abc", mtime=1_650_000_000)
    make(dst, "carpeta/v1.pdf", b"abc", mtime=1_650_000_000)
    p = plan_for(src, dst)
    assert [(o.rel, n.rel) for o, n in p.moved] == [("carpeta/v1.pdf", "carpeta/v2.pdf")]


def test_ambiguous_move_falls_back(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "x/a.txt", b"same", mtime=1_650_000_000)
    make(src, "x/b.txt", b"same", mtime=1_650_000_000)
    make(dst, "y/a.txt", b"same", mtime=1_650_000_000)
    make(dst, "y/b.txt", b"same", mtime=1_650_000_000)
    p = plan_for(src, dst)
    assert not p.moved
    assert rels(p.new) == ["x/a.txt", "x/b.txt"]
    assert rels(p.deleted) == ["y/a.txt", "y/b.txt"]


def test_deleted_archived_in_mirror_mode(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "keep.txt")
    make(dst, "keep.txt")
    make(dst, "gone.txt", b"zz")
    p = plan_for(src, dst, mode="mirror")
    assert rels(p.deleted) == ["gone.txt"] and not p.kept


def test_deleted_kept_in_add_only_mode(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "keep.txt")
    make(dst, "keep.txt")
    make(dst, "gone.txt", b"zz")
    p = plan_for(src, dst, mode="add_only")
    assert not p.deleted and rels(p.kept) == ["gone.txt"]


def test_excludes_apply_both_sides(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "~$lock.docx")
    make(src, "Thumbs.db")
    make(src, "real.docx")
    make(dst, "trash.TMP")
    p = plan_for(src, dst, exclude=["~$*", "thumbs.db", "*.tmp"])
    assert rels(p.new) == ["real.docx"] and not p.deleted


def test_case_insensitive_match(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "Carpeta/Plano.DWG")
    make(dst, "carpeta/plano.dwg")
    p = plan_for(src, dst)
    assert p.unchanged == 1 and p.is_empty


def test_archive_dir_ignored_in_dest(tmp_path):
    src, dst = tmp_path / "s", tmp_path / "d"
    make(src, "a.txt")
    make(dst, "a.txt")
    make(dst, f"{ARCHIVE_DIR}/2026-01-01/old.txt")
    p = plan_for(src, dst)
    assert p.is_empty


def test_analyze_rejects_missing_or_empty_source(tmp_path):
    with pytest.raises(SyncError):
        analyze({"source": str(tmp_path / "nope"), "dest": str(tmp_path / "d"), "mode": "mirror", "exclude": []})
    (tmp_path / "empty").mkdir()
    with pytest.raises(SyncError):
        analyze({"source": str(tmp_path / "empty"), "dest": str(tmp_path / "d"), "mode": "mirror", "exclude": []})


def test_analyze_with_missing_dest_plans_everything_new(tmp_path):
    src = tmp_path / "s"
    make(src, "a.txt")
    p = analyze({"source": str(src), "dest": str(tmp_path / "d"), "mode": "mirror", "exclude": []})
    assert rels(p.new) == ["a.txt"]


def test_orphans_under_unreadable_source_folder_are_kept():
    from core.sync import FileInfo
    dst = {"locked/a.txt": FileInfo("locked/a.txt", 1, 1.0), "free/b.txt": FileInfo("free/b.txt", 1, 1.0)}
    p = build_plan({}, dst, "mirror", src_errors=["locked"])
    assert rels(p.kept) == ["locked/a.txt"] and rels(p.deleted) == ["free/b.txt"]
