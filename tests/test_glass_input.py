"""Tests for GlassInput component."""
import pytest

try:
    import tkinter as tk
    _root = tk.Tk()
    _root.withdraw()
    HAS_DISPLAY = True
except Exception:
    HAS_DISPLAY = False


@pytest.fixture(scope="module")
def root():
    if not HAS_DISPLAY:
        pytest.skip("No display for tkinter")
    return _root


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display for tkinter")
class TestGlassInput:
    def test_import(self, root):
        from components.glass_input import GlassInput
        assert GlassInput is not None

    def test_is_frame_subclass(self, root):
        import tkinter as tk
        from components.glass_input import GlassInput
        assert issubclass(GlassInput, tk.Frame)

    def test_instantiates(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root)
        assert inp is not None
        inp.destroy()

    def test_has_entry(self, root):
        import tkinter as tk
        from components.glass_input import GlassInput
        inp = GlassInput(root)
        assert hasattr(inp, "_entry")
        assert isinstance(inp._entry, tk.Entry)
        inp.destroy()

    def test_placeholder_stored(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root, placeholder="Search...")
        assert inp.placeholder == "Search..."
        inp.destroy()

    def test_get_returns_empty_when_placeholder_active(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root, placeholder="Type here")
        assert inp.get() == ""
        inp.destroy()

    def test_insert_and_get(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root)
        inp.insert(0, "hello")
        assert inp.get() == "hello"
        inp.destroy()

    def test_clear_resets_value(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root)
        inp.insert(0, "data")
        inp.clear()
        assert inp.get() == ""
        inp.destroy()

    def test_delete_range(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root)
        inp.insert(0, "hello")
        inp.delete(0, 3)
        assert inp.get() == "lo"
        inp.destroy()

    def test_focused_default_false(self, root):
        from components.glass_input import GlassInput
        inp = GlassInput(root)
        assert inp._focused is False
        inp.destroy()
