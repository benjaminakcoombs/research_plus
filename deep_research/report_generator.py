"""Report generator — converts markdown outputs to PDF/DOCX."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_pdf(markdown_path: Path, output_path: Path | None = None) -> Path | None:
    """Convert a markdown file to PDF using pandoc.

    Returns the output path, or None if pandoc is not available.
    """
    if not _check_pandoc():
        logger.warning("pandoc not found. Skipping PDF generation.")
        return None

    if output_path is None:
        output_path = markdown_path.with_suffix(".pdf")

    try:
        subprocess.run(
            [
                "pandoc",
                str(markdown_path),
                "-o", str(output_path),
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",
                "-V", "fontsize=11pt",
                "--toc",
                "--toc-depth=2",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Generated PDF: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.warning(f"PDF generation failed: {e.stderr}")
        # Try without xelatex
        try:
            subprocess.run(
                [
                    "pandoc",
                    str(markdown_path),
                    "-o", str(output_path),
                    "-V", "geometry:margin=1in",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info(f"Generated PDF (basic): {output_path}")
            return output_path
        except subprocess.CalledProcessError as e2:
            logger.error(f"PDF generation failed: {e2.stderr}")
            return None


def generate_docx(markdown_path: Path, output_path: Path | None = None) -> Path | None:
    """Convert a markdown file to DOCX using pandoc.

    Returns the output path, or None if pandoc is not available.
    """
    if not _check_pandoc():
        logger.warning("pandoc not found. Skipping DOCX generation.")
        return None

    if output_path is None:
        output_path = markdown_path.with_suffix(".docx")

    try:
        subprocess.run(
            [
                "pandoc",
                str(markdown_path),
                "-o", str(output_path),
                "--toc",
                "--toc-depth=2",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Generated DOCX: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"DOCX generation failed: {e.stderr}")
        return None


def generate_reports(run_dir: Path, fmt: str = "markdown") -> list[Path]:
    """Generate reports in the requested format from a completed run directory.

    Args:
        run_dir: Path to the run output directory.
        fmt: Output format — "markdown", "pdf", "docx", or "all".

    Returns:
        List of generated file paths.
    """
    outputs = []

    # The markdown files are already saved by the orchestrator
    briefing_md = run_dir / "l3_executive_briefing.md"
    report_md = run_dir / "l3_full_report.md"

    for md_path in [briefing_md, report_md]:
        if md_path.exists():
            outputs.append(md_path)

            if fmt in ("pdf", "all"):
                pdf = generate_pdf(md_path)
                if pdf:
                    outputs.append(pdf)

            if fmt in ("docx", "all"):
                docx = generate_docx(md_path)
                if docx:
                    outputs.append(docx)

    return outputs


def _check_pandoc() -> bool:
    """Check if pandoc is available on the system."""
    return shutil.which("pandoc") is not None
