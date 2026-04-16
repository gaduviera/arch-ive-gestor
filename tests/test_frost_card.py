"""Tests for FrostCard component."""
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
    """Shared Tk root — created once per module, never destroyed mid-suite."""
    if not HAS_DISPLAY:
        pytest.skip("No display for tkinter")
    return _root


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display for tkinter")
class TestFrostCardExists:
    def test_import(self, root):
        from components.frost_card import FrostCard
        assert FrostCard is not None

    def test_is_canvas_subclass(self, root):
        import tkinter as tk
        from components.frost_card import FrostCard
        assert issubclass(FrostCard, tk.Canvas)

    def test_instantiates(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100)
        assert card is not None
        card.destroy()

    def test_default_background(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100)
        bg = card.cget("background")
        assert bg.lower() in ("#1a1a1a", "1a1a1a", "#1A1A1A")
        card.destroy()

    def test_has_draw_method(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100)
        assert hasattr(card, "draw") and callable(card.draw)
        card.destroy()

    def test_has_add_widget_method(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100)
        assert hasattr(card, "add_widget") and callable(card.add_widget)
        card.destroy()

    def test_padding_parameter(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100, padding=20)
        assert card.padding == 20
        card.destroy()

    def test_default_padding(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100)
        assert card.padding == 12
        card.destroy()

    def test_draw_runs_without_error(self, root):
        from components.frost_card import FrostCard
        card = FrostCard(root, width=200, height=100)
        card.pack()
        root.update_idletasks()
        card.draw()  # must not raise
        card.pack_forget()
        card.destroy()
