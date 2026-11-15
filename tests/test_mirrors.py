"""Tests for core.mirrors — mirror pair config and validation."""
import pytest

from core.mirrors import MirrorStore, new_mirror, validate, warnings
from core.sync import DEFAULT_EXCLUDES


def test_store_starts_empty(tmp_path):
    store = MirrorStore(tmp_path / "mirrors.json")
    assert store.mirrors == [] and store.selected is None


def test_upsert_persists_and_reloads(tmp_path):
    path = tmp_path / "mirrors.json"
    store = MirrorStore(path)
    store.upsert(new_mirror("CDE", str(tmp_path / "a"), str(tmp_path / "b")))
    again = MirrorStore(path)
    m = again.get("cde")
    assert m["name"] == "CDE" and m["mode"] == "mirror" and m["pinned"] is True
    assert m["exclude"] == DEFAULT_EXCLUDES


def test_rename_and_delete(tmp_path):
    store = MirrorStore(tmp_path / "m.json")
    store.upsert(new_mirror("Uno", str(tmp_path / "a"), str(tmp_path / "b")))
    store.selected = "Uno"
    edited = dict(store.get("Uno"), name="Dos")
    store.upsert(edited, old_name="Uno")
    assert store.get("Uno") is None and store.get("Dos") and store.selected == "Dos"
    store.delete("Dos")
    assert store.mirrors == [] and store.selected is None


def test_ordered_puts_pinned_first(tmp_path):
    store = MirrorStore(tmp_path / "m.json")
    store.upsert(new_mirror("b-suelto", str(tmp_path / "1"), str(tmp_path / "2"), pinned=False))
    store.upsert(new_mirror("z-fijo", str(tmp_path / "3"), str(tmp_path / "4")))
    store.upsert(new_mirror("a-fijo", str(tmp_path / "5"), str(tmp_path / "6")))
    assert [m["name"] for m in store.ordered()] == ["a-fijo", "z-fijo", "b-suelto"]
    assert [m["name"] for m in store.pinned()] == ["a-fijo", "z-fijo"]


def test_validate_rejects_bad_pairs(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    assert validate(new_mirror("", a, b), [])
    assert validate(new_mirror("x", a, a), [])
    assert validate(new_mirror("x", a, str(tmp_path / "a" / "inside")), [])
    assert validate(new_mirror("x", str(tmp_path / "b" / "inside"), b), [])
    assert validate(dict(new_mirror("x", a, b), mode="weird"), [])
    assert validate(new_mirror("x", a, b), []) == []


def test_validate_against_other_mirrors(tmp_path):
    other = new_mirror("Otro", str(tmp_path / "s1"), str(tmp_path / "dest"))
    dup_name = new_mirror("otro", str(tmp_path / "s2"), str(tmp_path / "d2"))
    nested_dest = new_mirror("N", str(tmp_path / "s3"), str(tmp_path / "dest" / "sub"))
    assert validate(dup_name, [other])
    assert validate(nested_dest, [other])
    same_source = new_mirror("S", str(tmp_path / "s1"), str(tmp_path / "d3"))
    assert validate(same_source, [other]) == []
    assert warnings(same_source, [other])


def test_upsert_raises_on_invalid(tmp_path):
    store = MirrorStore(tmp_path / "m.json")
    with pytest.raises(ValueError):
        store.upsert(new_mirror("x", str(tmp_path), str(tmp_path)))


def test_record_run_updates_status(tmp_path):
    store = MirrorStore(tmp_path / "m.json")
    store.upsert(new_mirror("A", str(tmp_path / "a"), str(tmp_path / "b")))
    store.record("A", summary={"new": 3}, ran=True)
    m = MirrorStore(tmp_path / "m.json").get("A")
    assert m["last_summary"] == {"new": 3} and m["last_run"]


def test_corrupt_file_starts_empty(tmp_path):
    path = tmp_path / "m.json"
    path.write_text("{not json", encoding="utf-8")
    assert MirrorStore(path).mirrors == []
