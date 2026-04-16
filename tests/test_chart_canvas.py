"""Tests for BarChart and LineChart components."""
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
class TestBarChart:
    def test_import(self, root):
        from components.chart_canvas import BarChart
        assert BarChart is not None

    def test_is_canvas_subclass(self, root):
        import tkinter as tk
        from components.chart_canvas import BarChart
        assert issubclass(BarChart, tk.Canvas)

    def test_instantiates_empty(self, root):
        from components.chart_canvas import BarChart
        chart = BarChart(root)
        assert chart.data == []
        chart.destroy()

    def test_instantiates_with_data(self, root):
        from components.chart_canvas import BarChart
        chart = BarChart(root, data=[1, 2, 3], labels=["a", "b", "c"])
        assert chart.data == [1, 2, 3]
        assert chart.labels == ["a", "b", "c"]
        chart.destroy()

    def test_update_data(self, root):
        from components.chart_canvas import BarChart
        chart = BarChart(root)
        chart.update_data([10, 20, 30], ["x", "y", "z"])
        assert chart.data == [10, 20, 30]
        assert chart.labels == ["x", "y", "z"]
        chart.destroy()

    def test_draw_runs_without_error(self, root):
        from components.chart_canvas import BarChart
        chart = BarChart(root, width=300, height=150)
        chart.pack()
        root.update_idletasks()
        chart.draw()
        chart.pack_forget()
        chart.destroy()

    def test_draw_with_data_no_error(self, root):
        from components.chart_canvas import BarChart
        chart = BarChart(root, data=[5, 10, 3], labels=["A", "B", "C"], width=300, height=150)
        chart.pack()
        root.update_idletasks()
        chart.draw()
        chart.pack_forget()
        chart.destroy()


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display for tkinter")
class TestLineChart:
    def test_import(self, root):
        from components.chart_canvas import LineChart
        assert LineChart is not None

    def test_is_canvas_subclass(self, root):
        import tkinter as tk
        from components.chart_canvas import LineChart
        assert issubclass(LineChart, tk.Canvas)

    def test_instantiates_empty(self, root):
        from components.chart_canvas import LineChart
        chart = LineChart(root)
        assert chart.data == []
        chart.destroy()

    def test_update_data(self, root):
        from components.chart_canvas import LineChart
        chart = LineChart(root)
        chart.update_data([1, 4, 2, 8], ["Jan", "Feb", "Mar", "Apr"])
        assert chart.data == [1, 4, 2, 8]
        chart.destroy()

    def test_draw_runs_without_error(self, root):
        from components.chart_canvas import LineChart
        chart = LineChart(root, width=300, height=150)
        chart.pack()
        root.update_idletasks()
        chart.draw()
        chart.pack_forget()
        chart.destroy()

    def test_draw_with_data_no_error(self, root):
        from components.chart_canvas import LineChart
        chart = LineChart(root, data=[10, 20, 15, 30], width=300, height=150)
        chart.pack()
        root.update_idletasks()
        chart.draw()
        chart.pack_forget()
        chart.destroy()
