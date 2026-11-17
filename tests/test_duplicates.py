"""Tests for core.duplicates — content-confirmed groups and archiving instead of deleting."""
import os
import threading
from datetime import date

from core.duplicates import archive_copy, find_duplicates
from core.sync import ARCHIVE_DIR

from tests.test_sync import make


def test_same_name_and_size_but_different_content_is_not_a_duplicate(tmp_path):
    make(tmp_path, "a/plano.dwg", b"AAAA")
    make(tmp_path, "b/plano.dwg", b"BBBB")
    make(tmp_path, "c/PLANO.dwg", b"AAAA")
    groups = find_duplicates(str(tmp_path))
    assert len(groups) == 1
    assert [os.path.relpath(p, tmp_path) for p in groups[0]["paths"]] == [
        os.path.join("a", "plano.dwg"), os.path.join("c", "PLANO.dwg")]


def test_archive_folder_is_skipped_and_stop_returns_none(tmp_path):
    make(tmp_path, "x/f.txt", b"same")
    make(tmp_path, f"{ARCHIVE_DIR}/2026-01-01/x/f.txt", b"same")
    assert find_duplicates(str(tmp_path)) == []
    stop = threading.Event()
    stop.set()
    assert find_duplicates(str(tmp_path), stop) is None


def test_archive_copy_moves_into_dated_archive_with_collision_suffix(tmp_path):
    p1 = make(tmp_path, "sub/f.txt", b"one")
    first = archive_copy(p1, str(tmp_path))
    p2 = make(tmp_path, "sub/f.txt", b"two")
    second = archive_copy(p2, str(tmp_path))
    arch = tmp_path / ARCHIVE_DIR / date.today().isoformat() / "sub"
    assert first == str(arch / "f.txt") and second == str(arch / "f__1.txt")
    assert not os.path.exists(p1)
    assert (arch / "f__1.txt").read_bytes() == b"two"
