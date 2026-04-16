"""Tests for theme.py — SYMETRA color palette and utilities."""
import pytest


class TestColorPalette:
    def test_colors_dict_exists(self):
        from theme import COLORS
        assert isinstance(COLORS, dict)

    def test_required_keys(self):
        from theme import COLORS
        required = [
            "carbon_base", "carbon_elevated", "carbon_hover",
            "gold_primary", "gold_muted", "gold_subtle",
            "platinum", "silver", "smoke",
            "success", "warning", "error",
            "border_idle", "border_active",
        ]
        for key in required:
            assert key in COLORS, f"Missing key: {key}"

    def test_color_values_are_hex(self):
        from theme import COLORS
        import re
        pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for key, val in COLORS.items():
            assert pattern.match(val), f"COLORS['{key}'] = '{val}' is not a valid hex color"

    def test_branding_values(self):
        from theme import COLORS
        assert COLORS["carbon_base"] == "#111111"
        assert COLORS["carbon_elevated"] == "#1A1A1A"
        assert COLORS["gold_primary"] == "#C6A85E"
        assert COLORS["platinum"] == "#F5F5F5"


class TestHexToRgb:
    def test_basic_conversion(self):
        from theme import hex_to_rgb
        assert hex_to_rgb("#C6A85E") == (198, 168, 94)

    def test_black(self):
        from theme import hex_to_rgb
        assert hex_to_rgb("#111111") == (17, 17, 17)

    def test_white_equivalent(self):
        from theme import hex_to_rgb
        assert hex_to_rgb("#F5F5F5") == (245, 245, 245)


class TestRgbToHex:
    def test_basic_conversion(self):
        from theme import rgb_to_hex
        assert rgb_to_hex(198, 168, 94) == "#C6A85E"

    def test_roundtrip(self):
        from theme import hex_to_rgb, rgb_to_hex
        original = "#1A1A1A"
        r, g, b = hex_to_rgb(original)
        assert rgb_to_hex(r, g, b) == original


class TestInterpolateColor:
    def test_zero_returns_start(self):
        from theme import interpolate_color
        assert interpolate_color("#000000", "#FFFFFF", 0.0) == "#000000"

    def test_one_returns_end(self):
        from theme import interpolate_color
        assert interpolate_color("#000000", "#FFFFFF", 1.0) == "#FFFFFF"

    def test_midpoint(self):
        from theme import interpolate_color
        result = interpolate_color("#000000", "#FFFFFF", 0.5)
        assert result == "#808080"


class TestGetColor:
    def test_returns_hex(self):
        from theme import get_color
        result = get_color("gold_primary")
        assert result == "#C6A85E"

    def test_unknown_key_raises(self):
        from theme import get_color
        with pytest.raises(KeyError):
            get_color("nonexistent_key")


class TestGoldGradient:
    def test_returns_two_colors(self):
        from theme import gold_gradient
        start, end = gold_gradient()
        assert start == "#C6A85E"
        assert end == "#6B5320"


class TestWithOpacity:
    def test_returns_rgba_tuple(self):
        from theme import with_opacity
        result = with_opacity("#C6A85E", 0.6)
        assert result == (198, 168, 94, 153)  # 0.6 * 255 = 153

    def test_full_opacity(self):
        from theme import with_opacity
        r, g, b, a = with_opacity("#FFFFFF", 1.0)
        assert a == 255

    def test_zero_opacity(self):
        from theme import with_opacity
        r, g, b, a = with_opacity("#FFFFFF", 0.0)
        assert a == 0
