"""Tests for GlassButton component."""
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
class TestGlassButton:
    def test_import(self, root):
        from components.glass_button import GlassButton
        assert GlassButton is not None

    def test_is_canvas_subclass(self, root):
        import tkinter as tk
        from components.glass_button import GlassButton
        assert issubclass(GlassButton, tk.Canvas)

    def test_instantiates_with_text(self, root):
        from components.glass_button import GlassButton
        btn = GlassButton(root, text="Test")
        assert btn.text == "Test"
        btn.destroy()

    def test_default_state_is_normal(self, root):
        from components.glass_button import GlassButton
        btn = GlassButton(root, text="X")
        assert btn._state == "normal"
        btn.destroy()

    def test_command_callable(self, root):
        from components.glass_button import GlassButton
        called = []
        btn = GlassButton(root, text="X", command=lambda: called.append(1))
        btn._on_press(None)
        assert called == [1]
        btn.destroy()

    def test_command_none_no_error(self, root):
        from components.glass_button import GlassButton
        btn = GlassButton(root, text="X", command=None)
        btn._on_press(None)  # must not raise
        btn.destroy()

    def test_set_state_changes_state(self, root):
        from components.glass_button import GlassButton
        btn = GlassButton(root, text="X")
        btn.set_state("disabled")
        assert btn._state == "disabled"
        btn.destroy()

    def test_configure_text(self, root):
        from components.glass_button import GlassButton
        btn = GlassButton(root, text="Old")
        btn.configure_text("New")
        assert btn.text == "New"
        btn.destroy()

    def test_disabled_no_command(self, root):
        from components.glass_button import GlassButton
        called = []
        btn = GlassButton(root, text="X", command=lambda: called.append(1))
        btn.set_state("disabled")
        btn._on_press(None)
        assert called == []
        btn.destroy()

    def test_draw_runs_without_error(self, root):
        from components.glass_button import GlassButton
        btn = GlassButton(root, text="Draw Test")
        btn.pack()
        root.update_idletasks()
        btn.draw()
        btn.pack_forget()
        btn.destroy()
