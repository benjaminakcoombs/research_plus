"""PDF generator — converts L3b markdown Deep Analysis to a styled PDF using ReportLab.

Produces a clean, professional PDF matching the Pokee AI Deep Analysis house style:
- Centered cover page with company name, date, Pokee branding
- Table of contents (static, matching the 5-section structure)
- Justified body text at 10pt, section headers at 16pt, finding titles at 13pt
- Markdown tables → styled ReportLab tables with header row shading
- Superscript footnote references, collected Source Notes on final page
- Italic blocks for held-back teasers and key uncertainties
- Dark navy (#1a1a2e) accent colour throughout

Usage:
    from deep_research.pdf_generator import build_pdf
    build_pdf(md_path, output_path)           # explicit paths
    build_pdf_from_run(run, output_dir)        # from a ResearchRun
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ReportLab imports are deferred to build time so the module can be imported
# even if reportlab isn't installed (graceful degradation).


def _check_reportlab() -> bool:
    """Return True if reportlab is importable."""
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


# ── Style definitions ───────────────────────────────────────────────────────


def _build_styles():
    """Build the ParagraphStyle set for the Deep Analysis PDF."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=28,
        leading=34,
        spaceAfter=6,
        textColor=HexColor("#1a1a2e"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "CoverCompany",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        spaceAfter=12,
        textColor=HexColor("#16213e"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=4,
        textColor=HexColor("#555555"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "SectionHead",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceBefore=24,
        spaceAfter=10,
        textColor=HexColor("#1a1a2e"),
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "FindingTitle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=18,
        spaceAfter=8,
        textColor=HexColor("#16213e"),
        keepWithNext=True,
    ))
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles["BodyText"].spaceAfter = 8
    styles["BodyText"].alignment = TA_JUSTIFY

    styles.add(ParagraphStyle(
        "BodyTextItalic",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName="Helvetica-Oblique",
        textColor=HexColor("#444444"),
    ))
    styles.add(ParagraphStyle(
        "Footnote",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        spaceAfter=3,
        textColor=HexColor("#666666"),
    ))
    styles.add(ParagraphStyle(
        "TOCItem",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=2,
        textColor=HexColor("#333333"),
    ))
    return styles


# ── Markdown → ReportLab XML helpers ────────────────────────────────────────


def _clean_markdown(text: str) -> str:
    """Convert markdown inline formatting to ReportLab XML tags."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic: *text* -> <i>text</i>
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    # Footnote refs: ^N -> <super>N</super>
    text = re.sub(r"\^(\d+)", r"<super>\1</super>", text)
    # Strip remaining markdown header markers
    text = text.replace("##", "").replace("#", "")

    # Unicode subscript digits → <sub>N</sub>  (for chemical formulas like CO₂)
    subscript_map = {
        "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
        "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    }
    for uni_char, digit in subscript_map.items():
        text = text.replace(uni_char, f"<sub>{digit}</sub>")

    # Common Greek letters that appear in technical analysis
    greek = {"η": "eta", "γ": "gamma", "θ": "theta"}
    for g, name in greek.items():
        text = text.replace(g, name)

    # Escape ampersands for XML (avoiding double-escape)
    text = text.replace("&", "&amp;")
    text = text.replace("&amp;amp;", "&amp;")

    return text.strip()


def _parse_table(lines: list[str]) -> list[list[str]]:
    """Parse markdown table lines into a list of row-cell lists."""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            rows.append(cells)
    return rows


def _extract_company_name(content: str) -> str:
    """Extract company name from the markdown content.

    Looks for the first non-boilerplate, non-header line after the title.
    """
    for line in content.split("\n"):
        line = line.strip()
        if (
            line
            and line != "DEEP ANALYSIS"
            and not line.startswith("#")
            and not line.startswith("---")
            and not line.startswith("Contents")
            and not line.startswith("Prepared")
            and not line.startswith("Contact")
            and not line.startswith("I.")
            and "|" not in line
        ):
            return line
    return "Company"


# ── Core PDF builder ────────────────────────────────────────────────────────


def build_pdf(
    md_path: str | Path,
    output_path: str | Path,
    *,
    company_name: str | None = None,
    date_label: str | None = None,
) -> Path:
    """Convert an L3b Deep Analysis markdown file to a styled PDF.

    Args:
        md_path: Path to the markdown file (l3_deep_analysis.md).
        output_path: Destination path for the generated PDF.
        company_name: Override for the company name on the cover page.
            If None, extracted from the markdown content.
        date_label: Override for the date shown on the cover page.
            If None, uses the current month/year (e.g. "March 2026").

    Returns:
        The Path to the generated PDF.

    Raises:
        ImportError: If reportlab is not installed.
        FileNotFoundError: If the markdown file doesn't exist.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    md_path = Path(md_path)
    output_path = Path(output_path)

    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    content = md_path.read_text()
    styles = _build_styles()

    if company_name is None:
        company_name = _extract_company_name(content)

    if date_label is None:
        date_label = datetime.now().strftime("%B %Y")

    story: list = []

    # ── COVER PAGE ──────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("DEEP ANALYSIS", styles["CoverTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="40%", thickness=1, color=HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(company_name, styles["CoverCompany"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"{date_label} | Confidential", styles["CoverMeta"]))
    story.append(Spacer(1, 1.5 * inch))
    story.append(HRFlowable(width="60%", thickness=0.5, color=HexColor("#cccccc")))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Prepared by Pokee AI | Deep Analysis", styles["CoverMeta"]))
    story.append(Paragraph("Contact: Ben Coombs — ben@pokee.ai", styles["CoverMeta"]))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ───────────────────────────────────────────────
    story.append(Paragraph("Contents", styles["SectionHead"]))
    story.append(Spacer(1, 0.2 * inch))
    toc_items = [
        "I.    The Opportunity",
        "II.   Company Situation",
        "III.  Key Findings",
        "IV.   Deal Context",
        "V.    About This Analysis",
        "       Source Notes",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["TOCItem"]))
    story.append(PageBreak())

    # ── PARSE BODY ──────────────────────────────────────────────────────
    body_start = content.find("## I.")
    if body_start == -1:
        body_start = content.find("## I ")
    if body_start == -1:
        body_start = 0

    body = content[body_start:]
    lines = body.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal rules
        if stripped == "---":
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd")))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # Section headers: ## I. THE OPPORTUNITY, ## II. COMPANY SITUATION, etc.
        if re.match(r"^##\s+[IVX]+\.", stripped):
            title = re.sub(r"^##\s+", "", stripped)
            story.append(Paragraph(_clean_markdown(title), styles["SectionHead"]))
            i += 1
            continue

        # Finding titles (bold lines that are standalone, > 20 chars)
        if stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 20:
            title_text = stripped.strip("*").strip()
            story.append(Paragraph(_clean_markdown(title_text), styles["FindingTitle"]))
            i += 1
            continue

        # Table detection
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1

            rows = _parse_table(table_lines)
            if rows and len(rows) > 1:
                clean_rows = []
                for row in rows:
                    clean_row = [
                        Paragraph(_clean_markdown(cell), styles["BodyText"])
                        for cell in row
                    ]
                    clean_rows.append(clean_row)

                ncols = max(len(r) for r in clean_rows)
                for row in clean_rows:
                    while len(row) < ncols:
                        row.append(Paragraph("", styles["BodyText"]))

                col_width = (6.5 * inch) / ncols
                t = Table(clean_rows, colWidths=[col_width] * ncols)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f0f0f5")),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#1a1a2e")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
            continue

        # Source notes section header
        if stripped.startswith("## Source Notes") or stripped == "Source Notes":
            story.append(PageBreak())
            story.append(Paragraph("Source Notes", styles["SectionHead"]))
            i += 1
            continue

        # Footnotes: ^N text
        if re.match(r"^\^(\d+)\s", stripped):
            story.append(Paragraph(_clean_markdown(stripped), styles["Footnote"]))
            i += 1
            continue

        # Italic blocks (held-back teasers, key uncertainties)
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            text = stripped.strip("*").strip()
            story.append(Paragraph(_clean_markdown(text), styles["BodyTextItalic"]))
            i += 1
            continue

        # Key uncertainty lines
        if stripped.startswith("**Key uncertainty:**"):
            text = stripped.replace("**Key uncertainty:**", "<b>Key uncertainty:</b>")
            story.append(Paragraph(_clean_markdown(text), styles["BodyTextItalic"]))
            i += 1
            continue

        # Regular paragraph — collect contiguous non-empty, non-special lines
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (
                not next_line
                or next_line.startswith("#")
                or next_line.startswith("|")
                or next_line == "---"
                or next_line.startswith("^")
            ):
                break
            para_lines.append(next_line)
            i += 1

        para_text = " ".join(para_lines)
        story.append(Paragraph(_clean_markdown(para_text), styles["BodyText"]))

    # ── Build the PDF ───────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title=f"Deep Analysis — {company_name}",
        author="Pokee AI",
    )
    doc.build(story)
    logger.info(f"PDF generated: {output_path}")
    return output_path


def build_pdf_from_run(
    run,
    output_dir: Path,
    *,
    date_label: str | None = None,
) -> Path | None:
    """Generate a styled PDF from a completed ResearchRun.

    Looks for the L3b markdown output file in the run directory and converts it.

    Args:
        run: A ResearchRun instance with l3b_final populated.
        output_dir: The base output directory (run_dir = output_dir / run.id).
        date_label: Optional override for the cover page date.

    Returns:
        Path to the generated PDF, or None if L3b output is missing or reportlab
        is not installed.
    """
    if not _check_reportlab():
        logger.warning("reportlab not installed. Skipping PDF generation. "
                        "Install with: pip install reportlab")
        return None

    run_dir = output_dir / run.id

    # Find the markdown source
    if run.pipeline_mode == "situation_assessment":
        md_path = run_dir / "l3_deep_analysis.md"
    else:
        md_path = run_dir / "l3_executive_briefing.md"

    if not md_path.exists():
        logger.warning(f"L3b markdown not found at {md_path}. Skipping PDF generation.")
        return None

    # Build output filename: {CompanyName}_Deep_Analysis_{Month}_{Year}.pdf
    safe_name = re.sub(r"[^\w\s-]", "", run.company_name)
    safe_name = re.sub(r"\s+", "_", safe_name.strip())
    now = datetime.now()
    pdf_filename = f"{safe_name}_Deep_Analysis_{now.strftime('%B')}_{now.year}.pdf"
    pdf_path = run_dir / pdf_filename

    try:
        build_pdf(
            md_path,
            pdf_path,
            company_name=run.company_name,
            date_label=date_label,
        )
        return pdf_path
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None
