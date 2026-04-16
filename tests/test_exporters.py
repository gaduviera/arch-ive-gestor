"""Tests for export_csv.py, export_json.py, and export_pdf.py."""
import pytest
import json
import csv
import io
import os
import tempfile


EVENTS = [
    {"timestamp": "2026-01-01T10:00:00", "files_copied": 5, "size_bytes": 1024},
    {"timestamp": "2026-02-15T14:30:00", "files_copied": 12, "size_bytes": 4096},
]


class TestExportCsv:
    def test_returns_csv_string(self):
        from export_csv import export_events_csv
        result = export_events_csv(EVENTS)
        assert isinstance(result, str)
        assert "timestamp" in result

    def test_empty_events_returns_empty_string(self):
        from export_csv import export_events_csv
        assert export_events_csv([]) == ""

    def test_csv_has_header_and_rows(self):
        from export_csv import export_events_csv
        result = export_events_csv(EVENTS)
        reader = list(csv.reader(io.StringIO(result)))
        assert len(reader) == 3   # header + 2 rows
        assert "timestamp" in reader[0]

    def test_writes_to_file(self, tmp_path):
        from export_csv import export_events_csv
        path = str(tmp_path / "out.csv")
        export_events_csv(EVENTS, filepath=path)
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "files_copied" in content

    def test_monthly_totals_csv(self):
        from export_csv import export_monthly_totals_csv
        totals = {"2026-01": 3, "2026-02": 7}
        result = export_monthly_totals_csv(totals)
        assert "month" in result
        assert "2026-01" in result
        assert "3" in result


class TestExportJson:
    def test_returns_json_string(self):
        from export_json import export_events_json
        result = export_events_json(EVENTS)
        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_roundtrip(self):
        from export_json import export_events_json
        result = export_events_json(EVENTS)
        parsed = json.loads(result)
        assert parsed[0]["files_copied"] == 5

    def test_writes_to_file(self, tmp_path):
        from export_json import export_events_json
        path = str(tmp_path / "out.json")
        export_events_json(EVENTS, filepath=path)
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 2

    def test_summary_json(self):
        from export_json import export_summary_json
        summary = {"total_events": 10, "first_event": "2026-01-01"}
        result = export_summary_json(summary)
        parsed = json.loads(result)
        assert parsed["total_events"] == 10


class TestExportPdf:
    def test_is_pdf_available_returns_bool(self):
        from export_pdf import is_pdf_available
        result = is_pdf_available()
        assert isinstance(result, bool)

    def test_raises_if_no_reportlab(self, monkeypatch):
        import export_pdf
        monkeypatch.setattr(export_pdf, "_check_reportlab", lambda: False)
        with pytest.raises(ImportError, match="reportlab"):
            export_pdf.export_report_pdf("Test", [], {})

    @pytest.mark.skipif(
        not __import__("export_pdf").is_pdf_available(),
        reason="reportlab not installed"
    )
    def test_generates_pdf_bytes(self):
        from export_pdf import export_report_pdf
        result = export_report_pdf("Test Report", EVENTS, {"key": "val"})
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"  # PDF magic bytes
