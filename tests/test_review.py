"""Tests for core.review — text detection and diff."""
from core.review import MAX_TEXT, diff_text, is_text

from tests.test_sync import make


def test_is_text_by_extension_and_size(tmp_path):
    t = make(tmp_path, "a.txt", b"hola")
    d = make(tmp_path, "a.dwg", b"hola")
    big = make(tmp_path, "big.csv", b"x" * (MAX_TEXT + 1))
    assert is_text(t) and not is_text(d) and not is_text(big)
    assert not is_text(str(tmp_path / "missing.txt"))


def test_diff_text_shows_changes_and_identical_is_empty(tmp_path):
    old = make(tmp_path, "old.txt", b"uno\ndos\n")
    new = make(tmp_path, "new.txt", b"uno\ntres\n")
    same = make(tmp_path, "same.txt", b"uno\ndos\n")
    d = diff_text(old, new)
    assert "-dos" in d and "+tres" in d
    assert diff_text(old, same) == ""


def test_diff_text_truncates(tmp_path):
    old = make(tmp_path, "o.txt", b"\n".join(b"a%d" % i for i in range(50)))
    new = make(tmp_path, "n.txt", b"\n".join(b"b%d" % i for i in range(50)))
    out = diff_text(old, new, max_lines=10)
    assert out.splitlines()[-1].startswith("…") and len(out.splitlines()) == 11
