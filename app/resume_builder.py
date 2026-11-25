import re
from pathlib import Path
from xml.sax.saxutils import escape

import fitz  # PyMuPDF
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "outputs"

import os

_PERSONAL_LINKS = {
    "LINKEDIN": "https://www.linkedin.com/in/aehsanalisunasara",
    "GITHUB": "https://github.com/Aahesan-412",
    "PORTFOLIO": "https://your-portfolio-link-here",
}
LINKS = {} if os.getenv("DEMO_MODE", "false").lower() == "true" else _PERSONAL_LINKS


def clean(text: str) -> str:
    """Remove characters that break the PDF (special hyphens, markdown symbols)."""
    replacements = {
        "\u2011": "-", "\u2010": "-", "\u2012": "-",
        "\u00a0": " ", "\u200b": "", "**": "", "__": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def make_filename(candidate: str, company: str = "") -> str:
    """Short file name, for example: Aehsanali_Novastaf.pdf"""
    name = "".join(candidate.split()[:2]).capitalize()
    company_word = company.split()[0].capitalize() if company.split() else ""
    base = "_".join(p for p in (name, company_word) if p)
    base = re.sub(r"[^A-Za-z0-9_]+", "", base)
    return f"{base}.pdf"


def _styles(size: float) -> dict:
    base = dict(fontName="Helvetica", fontSize=size, leading=size * 1.25)
    return {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=size + 8,
                               leading=size + 11, alignment=TA_CENTER),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=size + 1,
                                leading=size + 4, alignment=TA_CENTER),
        "contact": ParagraphStyle("contact", **base, alignment=TA_CENTER, spaceAfter=2),
        "heading": ParagraphStyle("heading", fontName="Helvetica-Bold", fontSize=size + 1,
                                  leading=size + 4, spaceBefore=6),
        "body": ParagraphStyle("body", **base),
        "bullet": ParagraphStyle("bullet", **base, leftIndent=12, bulletIndent=2),
    }


def _contact_markup(line: str) -> str:
    out = []
    for part in [p.strip() for p in line.split("|")]:
        safe = escape(part)
        if "@" in part:
            out.append(f'<a href="mailto:{part}" color="#0563C1"><u>{safe}</u></a>')
        elif part.upper() in LINKS:
            out.append(f'<a href="{LINKS[part.upper()]}" color="#0563C1"><u>{safe}</u></a>')
        else:
            out.append(safe)
    return " &nbsp;|&nbsp; ".join(out)


def _build_pdf(lines: list[str], path: Path, size: float) -> None:
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    st = _styles(size)
    story = []

    for i, line in enumerate(lines):
        if i == 0:                                   # name
            story.append(Paragraph(escape(line), st["name"]))
        elif i == 1:                                 # title
            story.append(Paragraph(escape(line), st["title"]))
        elif i == 2:                                 # contact line with links
            story.append(Paragraph(_contact_markup(line), st["contact"]))
        elif line.isupper() and len(line) < 45:      # section heading
            story.append(Paragraph(escape(line), st["heading"]))
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.black,
                                    spaceBefore=1, spaceAfter=3))
        elif line.startswith(("-", "•", "●")):       # bullet
            story.append(Paragraph(escape(line.lstrip("-•● ").strip()),
                                   st["bullet"], bulletText="•"))
        else:                                        # normal line
            story.append(Paragraph(escape(line), st["body"]))

    doc.build(story)


def save_resume_pdf(text: str, filename: str = "resume.pdf") -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    lines = [clean(l) for l in text.splitlines() if clean(l)]

    # Shrink the font a little until the resume fits on exactly one page
    for size in (10, 9.5, 9, 8.5, 8):
        _build_pdf(lines, path, size)
        with fitz.open(path) as pdf:
            pages = pdf.page_count
        if pages == 1:
            return str(path)

    print("Warning: resume is still longer than one page. Shorten the content.")
    return str(path)