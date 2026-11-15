"""SYMETRA color palette and UI utilities for Arch-Ive."""

COLORS = {
    # Carbon backgrounds
    "carbon_base":     "#111111",
    "carbon_elevated": "#1A1A1A",
    "carbon_hover":    "#242424",
    # Gold accents
    "gold_primary":    "#C6A85E",
    "gold_muted":      "#9A7F42",
    "gold_subtle":     "#4A3A1A",
    # Text
    "platinum":        "#F5F5F5",
    "silver":          "#AAAAAA",
    "smoke":           "#666666",
    # Status
    "success":         "#4CAF50",
    "warning":         "#FFC107",
    "error":           "#F44336",
    # Borders
    "border_idle":     "#2A2A2A",
    "border_active":   "#C6A85E",
}


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' to (R, G, B) integers."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (R, G, B) integers to '#RRGGBB' uppercase."""
    return f"#{r:02X}{g:02X}{b:02X}"


def interpolate_color(start: str, end: str, t: float) -> str:
    """Linear interpolation between two hex colors at position t ∈ [0, 1]."""
    r1, g1, b1 = hex_to_rgb(start)
    r2, g2, b2 = hex_to_rgb(end)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return rgb_to_hex(r, g, b)


def get_color(name: str) -> str:
    """Return hex color by name; raises KeyError for unknown names."""
    return COLORS[name]


def gold_gradient() -> tuple[str, str]:
    """Return (start, end) hex colors for the standard gold gradient."""
    return COLORS["gold_primary"], "#6B5320"


def with_opacity(hex_color: str, opacity: float) -> tuple[int, int, int, int]:
    """Return (R, G, B, A) with A = round(opacity * 255), for use with PIL."""
    r, g, b = hex_to_rgb(hex_color)
    a = round(opacity * 255)
    return r, g, b, a
