"""CSV exporter for backup history reports."""
import csv
import io
from typing import Optional


def export_events_csv(events: list[dict], filepath: Optional[str] = None) -> str:
    """Export a list of backup event dicts to CSV.

    Parameters
    ----------
    events : list of dicts (each event has at minimum a 'timestamp' key)
    filepath : if provided, write to this path; otherwise return CSV string

    Returns
    -------
    CSV content as string (also written to file if filepath given)
    """
    if not events:
        return ""

    fieldnames = sorted({k for ev in events for k in ev.keys()})
    # Put timestamp first
    if "timestamp" in fieldnames:
        fieldnames = ["timestamp"] + [f for f in fieldnames if f != "timestamp"]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames,
                            extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(events)
    content = output.getvalue()

    if filepath:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.write(content)

    return content


def export_monthly_totals_csv(totals: dict[str, int], filepath: Optional[str] = None) -> str:
    """Export monthly totals dict {'YYYY-MM': count} to CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["month", "count"])
    for month, count in sorted(totals.items()):
        writer.writerow([month, count])
    content = output.getvalue()

    if filepath:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.write(content)

    return content
