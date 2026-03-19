"""Generate a clean, readable PDF from the Brimstone L3b Deep Analysis markdown."""

import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=28, leading=34, spaceAfter=6,
        textColor=HexColor('#1a1a2e'), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'CoverCompany', parent=styles['Title'],
        fontSize=22, leading=28, spaceAfter=12,
        textColor=HexColor('#16213e'), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'CoverMeta', parent=styles['Normal'],
        fontSize=11, leading=14, spaceAfter=4,
        textColor=HexColor('#555555'), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'SectionHead', parent=styles['Heading1'],
        fontSize=16, leading=20, spaceBefore=24, spaceAfter=10,
        textColor=HexColor('#1a1a2e'), keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        'FindingTitle', parent=styles['Heading2'],
        fontSize=13, leading=16, spaceBefore=18, spaceAfter=8,
        textColor=HexColor('#16213e'), keepWithNext=True,
    ))
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 8
    styles['BodyText'].alignment = TA_JUSTIFY
    styles.add(ParagraphStyle(
        'BodyTextItalic', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=8,
        alignment=TA_JUSTIFY, fontName='Helvetica-Oblique',
        textColor=HexColor('#444444'),
    ))
    styles.add(ParagraphStyle(
        'Footnote', parent=styles['Normal'],
        fontSize=8, leading=10, spaceAfter=3,
        textColor=HexColor('#666666'),
    ))
    styles.add(ParagraphStyle(
        'TOCItem', parent=styles['Normal'],
        fontSize=11, leading=16, spaceAfter=2,
        textColor=HexColor('#333333'),
    ))
    return styles


def clean_markdown(text):
    """Convert markdown formatting to reportlab XML tags."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* -> <i>text</i>
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # Footnote refs: ^N or ^i, ^ii, ^iii, ^iv, ^v, ^vi, ^vii, ^viii, ^ix, ^x -> <super>N</super>
    text = re.sub(r'\^(\w+)', r'<super>\1</super>', text)
    # Clean up any remaining markdown artifacts
    text = text.replace('##', '').replace('#', '')
    # Replace Unicode subscript/superscript characters with ReportLab tags
    # Chemical formulas: Al₂O₃ → Al<sub>2</sub>O<sub>3</sub>, etc.
    subscript_map = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
                     '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'}
    for uni_char, digit in subscript_map.items():
        text = text.replace(uni_char, f'<sub>{digit}</sub>')
    # Greek letters that may appear
    text = text.replace('η-', 'eta-')
    text = text.replace('γ/', 'gamma/')
    text = text.replace('θ-', 'theta-')
    text = text.replace('γ', 'gamma')
    text = text.replace('θ', 'theta')
    text = text.replace('η', 'eta')
    # CO₂ special case (already handled by subscript_map above)
    # Escape ampersands for XML
    text = text.replace('&', '&amp;')
    # Fix double-escaped
    text = text.replace('&amp;amp;', '&amp;')
    return text.strip()


def parse_table(lines):
    """Parse a markdown table into rows."""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith('|') and not re.match(r'^\|[\s\-|]+\|$', line):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            rows.append(cells)
    return rows


def build_pdf(md_path, output_path):
    with open(md_path, 'r') as f:
        content = f.read()

    styles = build_styles()
    story = []

    # ── COVER PAGE ──
    # Extract company name from markdown (line after "DEEP ANALYSIS")
    company_name = "Company"
    for line in content.split('\n'):
        line = line.strip()
        if line and line != "DEEP ANALYSIS" and not line.startswith('#') and not line.startswith('---') and not line.startswith('Contents') and not line.startswith('Prepared') and not line.startswith('Contact') and not line.startswith('I.') and '|' not in line:
            company_name = line
            break

    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("DEEP ANALYSIS", styles['CoverTitle']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="40%", thickness=1, color=HexColor('#1a1a2e')))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(company_name, styles['CoverCompany']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("March 2026 | Confidential", styles['CoverMeta']))
    story.append(Spacer(1, 1.5 * inch))
    story.append(HRFlowable(width="60%", thickness=0.5, color=HexColor('#cccccc')))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Prepared by Pokee AI | Deep Analysis", styles['CoverMeta']))
    story.append(Paragraph("Contact: Ben Coombs — ben@pokee.ai", styles['CoverMeta']))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ──
    story.append(Paragraph("Contents", styles['SectionHead']))
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
        story.append(Paragraph(item, styles['TOCItem']))
    story.append(PageBreak())

    # ── PARSE BODY CONTENT ──
    # Skip the markdown cover page / TOC — start from "## I. THE OPPORTUNITY"
    body_start = content.find('## I.')
    if body_start == -1:
        body_start = content.find('## I ')
    if body_start == -1:
        body_start = 0

    body = content[body_start:]

    # Split into lines for processing
    lines = body.split('\n')
    i = 0
    in_table = False
    table_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal rules
        if stripped == '---':
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#dddddd')))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # Section headers: ## I. THE OPPORTUNITY or ## V. About
        if re.match(r'^##\s+[IVX]+\.', stripped):
            title = re.sub(r'^##\s+', '', stripped)
            story.append(Paragraph(clean_markdown(title), styles['SectionHead']))
            i += 1
            continue

        # Calculation Notes section header
        if stripped in ('### Calculation Notes', '## Calculation Notes', 'Calculation Notes') and i > 20:
            story.append(Spacer(1, 12))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#dddddd')))
            story.append(Spacer(1, 6))
            story.append(Paragraph("Calculation Notes", styles['SectionHead']))
            i += 1
            continue

        # Finding titles: ### lines in the Key Findings section (not Calculation/Source Notes)
        if stripped.startswith('### ') and not stripped.startswith('### Calc') and not stripped.startswith('### Source') and not stripped.startswith('### Coherency'):
            title_text = stripped[4:].strip()
            story.append(Paragraph(clean_markdown(title_text), styles['FindingTitle']))
            i += 1
            continue

        # Finding titles (bold lines that are standalone)
        if stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 20:
            title_text = stripped.strip('*').strip()
            story.append(Paragraph(clean_markdown(title_text), styles['FindingTitle']))
            i += 1
            continue

        # Table detection
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1

            rows = parse_table(table_lines)
            if rows and len(rows) > 1:
                # Build table
                # Clean cell content
                clean_rows = []
                for row in rows:
                    clean_row = [Paragraph(clean_markdown(cell), styles['BodyText']) for cell in row]
                    clean_rows.append(clean_row)

                ncols = max(len(r) for r in clean_rows)
                # Pad short rows
                for row in clean_rows:
                    while len(row) < ncols:
                        row.append(Paragraph('', styles['BodyText']))

                col_width = (6.5 * inch) / ncols
                t = Table(clean_rows, colWidths=[col_width] * ncols)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f0f5')),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#1a1a2e')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
            continue

        # Source notes section
        if stripped.startswith('## Source Notes') or stripped.startswith('### Source Notes') or stripped == 'Source Notes':
            story.append(PageBreak())
            story.append(Paragraph("Source Notes", styles['SectionHead']))
            i += 1
            continue

        # Bullet points (Open Questions, etc.)
        if stripped.startswith('- '):
            bullet_text = stripped[2:]
            story.append(Paragraph(clean_markdown(bullet_text), ParagraphStyle(
                'Bullet', parent=styles['BodyText'],
                fontSize=10, leading=14, spaceAfter=4,
                leftIndent=24, bulletIndent=12,
                bulletFontName='Helvetica', bulletFontSize=10,
            ), bulletText='\u2022'))
            i += 1
            continue

        # Bold sub-headers within findings (e.g., "**Open Questions:**", "**The Observation.**")
        if re.match(r'^\*\*[A-Za-z].*[:.]?\*\*$', stripped) or stripped in ('**Open Questions:**',):
            text = stripped.strip('*').strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(f'<b>{clean_markdown(text)}</b>', styles['BodyText']))
            i += 1
            continue

        # Footnotes: ^N text (Arabic or Roman numeral)
        if re.match(r'^\^(\w+)\s', stripped):
            story.append(Paragraph(clean_markdown(stripped), styles['Footnote']))
            i += 1
            continue

        # Italic blocks (held-back teasers, key uncertainties)
        if stripped.startswith('*') and stripped.endswith('*') and not stripped.startswith('**'):
            text = stripped.strip('*').strip()
            story.append(Paragraph(clean_markdown(text), styles['BodyTextItalic']))
            i += 1
            continue

        # Key uncertainty lines
        if stripped.startswith('**Key uncertainty:**'):
            text = stripped.replace('**Key uncertainty:**', '<b>Key uncertainty:</b>')
            story.append(Paragraph(clean_markdown(text), styles['BodyTextItalic']))
            i += 1
            continue

        # Regular paragraph — collect contiguous non-empty lines
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line or next_line.startswith('#') or next_line.startswith('|') or next_line == '---' or next_line.startswith('^') or next_line.startswith('- ') or re.match(r'^\*\*[A-Za-z].*[:.]?\*\*$', next_line) or next_line == '**Open Questions:**':
                break
            para_lines.append(next_line)
            i += 1

        para_text = ' '.join(para_lines)
        story.append(Paragraph(clean_markdown(para_text), styles['BodyText']))

    # Build the PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title="Deep Analysis — Brimstone Energy",
        author="Pokee AI",
    )
    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        build_pdf(sys.argv[1], sys.argv[2])
    else:
        build_pdf(
            "/sessions/kind-bold-planck/mnt/research-banking-boutique/outputs/run_523046f1/l3_deep_analysis.md",
            "/sessions/kind-bold-planck/mnt/research-banking-boutique/Brimstone_Deep_Analysis_March_2026.pdf",
        )
