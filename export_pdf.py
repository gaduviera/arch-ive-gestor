"""PDF exporter for backup history reports (requires reportlab)."""
from typing import Optional
import io


def _check_reportlab():
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


def export_report_pdf(
    title: str,
    events: list[dict],
    summary: dict,
    filepath: Optional[str] = None,
) -> bytes:
    """Generate a PDF backup report.

    Parameters
    ----------
    title   : report title string
    events  : list of event dicts (shown as table)
    summary : dict with summary stats (shown as key-value block)
    filepath: if provided, also write to this path

    Returns
    -------
    PDF content as bytes

    Raises
    ------
    ImportError if reportlab is not installed
    """
    if not _check_reportlab():
        raise ImportError(
            "reportlab is required for PDF export. "
            "Install with: pip install reportlab"
        )

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )

    # SYMETRA colors
    GOLD   = colors.HexColor("#C6A85E")
    DARK   = colors.HexColor("#111111")
    PANEL  = colors.HexColor("#1A1A1A")
    LIGHT  = colors.HexColor("#F5F5F5")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SYMTitle", parent=styles["Title"],
        textColor=GOLD, backColor=DARK,
        fontSize=18, spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SYMHeading", parent=styles["Heading2"],
        textColor=GOLD, fontSize=12, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "SYMBody", parent=styles["Normal"],
        textColor=LIGHT, fontSize=9, spaceAfter=3,
    )

    story = []

    # Title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.4*cm))

    # Summary block
    if summary:
        story.append(Paragraph("Resumen", heading_style))
        for k, v in summary.items():
            story.append(Paragraph(f"<b>{k}:</b> {v}", body_style))
        story.append(Spacer(1, 0.4*cm))

    # Events table
    if events:
        story.append(Paragraph("Eventos de backup", heading_style))

        fieldnames = sorted({k for ev in events for k in ev.keys()})
        if "timestamp" in fieldnames:
            fieldnames = ["timestamp"] + [f for f in fieldnames
                                          if f != "timestamp"]

        headers = [f.replace("_", " ").title() for f in fieldnames]
        table_data = [headers]
        for ev in events[-50:]:   # last 50 events max
            row = [str(ev.get(f, "")) for f in fieldnames]
            table_data.append(row)

        col_count = len(fieldnames)
        col_w = (A4[0] - 4*cm) / col_count

        tbl = Table(table_data, colWidths=[col_w] * col_count)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PANEL),
            ("TEXTCOLOR",  (0, 0), (-1, 0), GOLD),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), DARK),
            ("TEXTCOLOR",  (0, 1), (-1, -1), LIGHT),
            ("FONTSIZE",   (0, 1), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK, PANEL]),
            ("GRID",       (0, 0), (-1, -1), 0.25, colors.HexColor("#2A2A2A")),
            ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(tbl)

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if filepath:
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


def is_pdf_available() -> bool:
    """Check whether reportlab is installed."""
    return _check_reportlab()
