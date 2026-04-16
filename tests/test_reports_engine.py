"""Tests for BackupHistoryManager and ReportsCalculator."""
import pytest
import json
import tempfile
import os
from datetime import datetime


@pytest.fixture
def tmp_log(tmp_path):
    return str(tmp_path / "backup_history.json")


class TestBackupHistoryManager:
    def test_init_creates_empty_history(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        assert mgr._history == []

    def test_append_adds_timestamp(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        mgr.append_event({"files_copied": 5})
        assert len(mgr._history) == 1
        assert "timestamp" in mgr._history[0]

    def test_append_persists_to_disk(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        mgr.append_event({"action": "backup"})
        with open(tmp_log, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["action"] == "backup"

    def test_reload_from_disk(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr1 = BackupHistoryManager(tmp_log)
        mgr1.append_event({"x": 1})
        mgr2 = BackupHistoryManager(tmp_log)
        assert len(mgr2._history) == 1

    def test_get_events_no_filter_returns_all(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        mgr.append_event({"n": 1})
        mgr.append_event({"n": 2})
        assert len(mgr.get_events()) == 2

    def test_get_events_date_filter(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        mgr._history = [
            {"timestamp": "2026-01-10T10:00:00", "n": 1},
            {"timestamp": "2026-02-15T10:00:00", "n": 2},
            {"timestamp": "2026-03-20T10:00:00", "n": 3},
        ]
        result = mgr.get_events(
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 2, 28)
        )
        assert len(result) == 1
        assert result[0]["n"] == 2

    def test_get_summary_empty(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        s = mgr.get_summary()
        assert s["total_events"] == 0
        assert s["first_event"] is None
        assert s["last_event"] is None

    def test_get_summary_counts(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        mgr._history = [
            {"timestamp": "2026-01-01T00:00:00"},
            {"timestamp": "2026-06-15T00:00:00"},
        ]
        s = mgr.get_summary()
        assert s["total_events"] == 2
        assert "2026-01-01" in s["first_event"]
        assert "2026-06-15" in s["last_event"]


class TestReportsCalculator:
    @pytest.fixture
    def hm_with_data(self, tmp_log):
        from reports_engine import BackupHistoryManager
        mgr = BackupHistoryManager(tmp_log)
        mgr._history = [
            {"timestamp": "2026-03-01T10:00:00", "files": 10},
            {"timestamp": "2026-03-01T14:00:00", "files": 5},
            {"timestamp": "2026-03-15T09:00:00", "files": 20},
            {"timestamp": "2026-04-10T10:00:00", "files": 8},
            {"timestamp": "2026-02-20T10:00:00", "files": 3},
        ]
        return mgr

    def test_compute_heatmap_correct_counts(self, hm_with_data):
        from reports_engine import ReportsCalculator
        calc = ReportsCalculator(hm_with_data)
        result = calc.compute_heatmap(2026, 3)
        assert result["2026-03-01"] == 2
        assert result["2026-03-15"] == 1
        assert "2026-04-10" not in result

    def test_compute_heatmap_empty_month(self, hm_with_data):
        from reports_engine import ReportsCalculator
        calc = ReportsCalculator(hm_with_data)
        result = calc.compute_heatmap(2025, 1)
        assert result == {}

    def test_compute_monthly_totals(self, hm_with_data):
        from reports_engine import ReportsCalculator
        calc = ReportsCalculator(hm_with_data)
        result = calc.compute_monthly_totals(2026)
        assert result.get("2026-02") == 1
        assert result.get("2026-03") == 3   # 2026-03-01×2 + 2026-03-15×1
        assert result.get("2026-04") == 1
        assert "2025-12" not in result

    def test_compute_comparison_delta(self, hm_with_data):
        from reports_engine import ReportsCalculator
        calc = ReportsCalculator(hm_with_data)
        result = calc.compute_comparison(
            event_key="files",
            period_a_start=datetime(2026, 2, 1),
            period_a_end=datetime(2026, 2, 28),
            period_b_start=datetime(2026, 3, 1),
            period_b_end=datetime(2026, 3, 31),
        )
        assert result["period_a"]["total"] == 3.0
        assert result["period_b"]["total"] == 35.0
        assert result["delta"] == 32.0
        assert abs(result["delta_pct"] - (32/3*100)) < 0.01

    def test_compute_comparison_zero_period_a(self, tmp_log):
        from reports_engine import BackupHistoryManager, ReportsCalculator
        mgr = BackupHistoryManager(tmp_log)
        calc = ReportsCalculator(mgr)
        result = calc.compute_comparison(
            "files",
            datetime(2025, 1, 1), datetime(2025, 1, 31),
            datetime(2025, 2, 1), datetime(2025, 2, 28),
        )
        assert result["delta_pct"] == 0.0

    def test_recoverable_space(self, tmp_log):
        from reports_engine import BackupHistoryManager, ReportsCalculator
        mgr  = BackupHistoryManager(tmp_log)
        calc = ReportsCalculator(mgr)
        groups = [
            {"size": 1000, "paths": ["a", "b", "c"]},   # 2000
            {"size": 500,  "paths": ["x", "y"]},         # 500
            {"size": 300,  "paths": ["z"]},               # 0 (single copy)
        ]
        assert calc.recoverable_space(groups) == 2500

    def test_recoverable_space_empty(self, tmp_log):
        from reports_engine import BackupHistoryManager, ReportsCalculator
        mgr  = BackupHistoryManager(tmp_log)
        calc = ReportsCalculator(mgr)
        assert calc.recoverable_space([]) == 0
