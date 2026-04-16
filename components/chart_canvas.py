import tkinter as tk

from theme import COLORS, interpolate_color, gold_gradient


class BarChart(tk.Canvas):
    def __init__(self, parent, data=None, labels=None, width=400, height=200, **kwargs):
        self.data = data if data else []
        self.labels = labels if labels else []
        super().__init__(
            parent,
            bg="#111111",
            highlightthickness=0,
            bd=0,
            width=width,
            height=height,
            **kwargs,
        )
        self.draw()

    def update_data(self, data, labels=None):
        self.data = data
        self.labels = labels if labels else []
        self.draw()

    def draw(self):
        self.delete("chart")
        if not self.data:
            return

        canvas_width = int(self["width"])
        canvas_height = int(self["height"])
        padding_x = 20
        padding_top = 10
        padding_bottom = 30
        n = len(self.data)
        max_val = max(self.data) if self.data else 1
        usable_width = canvas_width - 2 * padding_x
        slot_width = usable_width / n
        bar_width = slot_width * 0.7
        gap = slot_width * 0.3
        max_bar_height = (canvas_height - padding_top - padding_bottom) * 0.8

        for i, v in enumerate(self.data):
            color = interpolate_color("#C6A85E", "#6B5320", i / max(n - 1, 1))
            bar_height = (v / max_val) * max_bar_height
            x0 = padding_x + i * slot_width + gap / 2
            x1 = x0 + bar_width
            y1 = canvas_height - padding_bottom
            y0 = y1 - bar_height

            self.create_rectangle(x0, y0, x1, y1, fill=color, outline="", tags="chart")

            cx = (x0 + x1) / 2
            self.create_text(
                cx,
                y0 - 4,
                text=f"{v:.1f}",
                font=("Segoe UI", 8),
                fill="#F5F5F5",
                tags="chart",
            )

            if self.labels and i < len(self.labels):
                self.create_text(
                    cx,
                    canvas_height - padding_bottom + 10,
                    text=self.labels[i],
                    font=("Segoe UI", 8),
                    fill="#AAAAAA",
                    tags="chart",
                )


class LineChart(tk.Canvas):
    def __init__(self, parent, data=None, labels=None, width=400, height=200, **kwargs):
        self.data = data if data else []
        self.labels = labels if labels else []
        super().__init__(
            parent,
            bg="#111111",
            highlightthickness=0,
            bd=0,
            width=width,
            height=height,
            **kwargs,
        )
        self.draw()

    def update_data(self, data, labels=None):
        self.data = data
        self.labels = labels if labels else []
        self.draw()

    def draw(self):
        self.delete("chart")
        if not self.data:
            return

        canvas_width = int(self["width"])
        canvas_height = int(self["height"])
        padding_x = 20
        padding_top = 10
        padding_bottom = 30

        if len(self.data) == 1:
            v = self.data[0]
            min_val = min(self.data)
            max_val = max(self.data)
            value_range = max_val - min_val if max_val != min_val else 1
            usable_height = (canvas_height - padding_top - padding_bottom) * 0.8
            y_top = padding_top + (canvas_height - padding_top - padding_bottom) * 0.1
            x = padding_x + (canvas_width - 2 * padding_x) / 2
            y = y_top + (1 - (v - min_val) / value_range) * usable_height
            self.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#C6A85E", outline="", tags="chart")
            return

        n = len(self.data)
        min_val = min(self.data)
        max_val = max(self.data)
        value_range = max_val - min_val if max_val != min_val else 1
        usable_height = (canvas_height - padding_top - padding_bottom) * 0.8
        y_top = padding_top + (canvas_height - padding_top - padding_bottom) * 0.1

        points = []
        for i, v in enumerate(self.data):
            x = padding_x + i * (canvas_width - 2 * padding_x) / (n - 1)
            y = y_top + (1 - (v - min_val) / value_range) * usable_height
            points.append((x, y))

        flatten = [coord for pt in points for coord in pt]
        self.create_line(*flatten, fill="#C6A85E", width=2, tags="chart")

        for x, y in points:
            self.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#C6A85E", outline="", tags="chart")

        if self.labels and len(self.labels) == n:
            for i, label in enumerate(self.labels):
                x = padding_x + i * (canvas_width - 2 * padding_x) / (n - 1)
                self.create_text(
                    x,
                    canvas_height - padding_bottom + 10,
                    text=label,
                    font=("Segoe UI", 8),
                    fill="#AAAAAA",
                    tags="chart",
                )
