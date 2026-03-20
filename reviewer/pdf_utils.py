from __future__ import annotations

import re
from io import BytesIO
from xml.sax.saxutils import escape


def build_pdf_report(*, title: str, action: str, language: str, answer: str, code: str) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import ListFlowable, ListItem, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("The reportlab package is not installed. Install the requirements first.") from exc

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=title,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="HeroTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=colors.HexColor("#ff6b35"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#ff6b35"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#8b5cf6"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#1a1a1a"),
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0a0805"),
            backColor=colors.HexColor("#f5f5f5"),
            borderColor=colors.HexColor("#8b5cf6"),
            borderWidth=2,
            borderPadding=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaText",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#8b5cf6"),
        )
    )

    story = []

    header_table = Table(
        [
            [Paragraph("📊 AI Code Review Report", styles["MetaText"])],
            [Paragraph(escape(title), styles["HeroTitle"])],
            [Paragraph("Comprehensive structured analysis with findings, corrections, and recommendations.", styles["ReportBody"])],
        ],
        colWidths=[document.width],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0e6ff")),
                ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#8b5cf6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ]
        )
    )
    story.extend([header_table, Spacer(1, 12)])

    meta_table = Table(
        [
            [
                Paragraph(f"<b>📝 Action</b><br/>{escape(action)}", styles["ReportBody"]),
                Paragraph(f"<b>💻 Language</b><br/>{escape(language)}", styles["ReportBody"]),
            ]
        ],
        colWidths=[document.width / 2 - 6, document.width / 2 - 6],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff5ed")),
                ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#ff6b35")),
                ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#ffc9a8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([meta_table, Spacer(1, 16)])

    story.append(Paragraph("📋 Detailed Review", styles["SectionHeading"]))
    story.extend(_build_answer_story(answer=_normalize_answer_text(answer), styles=styles, colors=colors, ListFlowable=ListFlowable, ListItem=ListItem, Paragraph=Paragraph, Preformatted=Preformatted, Spacer=Spacer))

    story.extend(
        [
            Spacer(1, 14),
            Paragraph("💾 Submitted Code", styles["SectionHeading"]),
            Spacer(1, 6),
            Preformatted(code or "No code provided.", styles["CodeBlock"]),
        ]
    )

    document.build(story)
    return buffer.getvalue()


def _build_answer_story(*, answer: str, styles: dict, colors, ListFlowable, ListItem, Paragraph, Preformatted, Spacer) -> list:
    story: list = []
    lines = answer.replace("\r\n", "\n").split("\n")
    paragraph_lines: list[str] = []
    bullet_lines: list[str] = []
    code_lines: list[str] = []
    code_language = ""
    in_code = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines if line.strip())
            if text:
                story.append(Paragraph(_format_inline(text), styles["ReportBody"]))
                story.append(Spacer(1, 4))
            paragraph_lines = []

    def flush_bullets() -> None:
        nonlocal bullet_lines
        if bullet_lines:
            items = [
                ListItem(Paragraph(_format_inline(line.replace("- ", "", 1).replace("* ", "", 1)), styles["ReportBody"]))
                for line in bullet_lines
            ]
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=18,
                    bulletColor=colors.HexColor("#ff6b35"),
                )
            )
            story.append(Spacer(1, 8))
            bullet_lines = []

    def flush_code() -> None:
        nonlocal code_lines, code_language
        label = escape(code_language or "Code")
        story.append(Paragraph(f"<b>✏️ {label}</b>", styles["SubHeading"]))
        story.append(Spacer(1, 4))
        story.append(Preformatted("\n".join(code_lines).rstrip(), styles["CodeBlock"]))
        story.append(Spacer(1, 10))
        code_lines = []
        code_language = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_bullets()
            if in_code:
                flush_code()
            else:
                code_language = stripped.replace("```", "", 1).strip()
            in_code = not in_code
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_bullets()
            continue

        if re.match(r"^#{2,4}\s+", stripped):
            flush_paragraph()
            flush_bullets()
            text = re.sub(r"^#{2,4}\s+", "", stripped)
            style_name = "SectionHeading" if stripped.startswith("## ") else "SubHeading"
            story.append(Paragraph(_format_inline(text), styles[style_name]))
            story.append(Spacer(1, 6))
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            bullet_lines.append(stripped)
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            bullet_lines.append(f"- {stripped}")
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_bullets()
    if in_code:
        flush_code()

    return story


def _format_inline(text: str) -> str:
    safe = escape(text)
    safe = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    return safe


def _normalize_answer_text(answer: str) -> str:
    trimmed = answer.strip()
    match = re.match(r"^```(?:markdown|md)?\n([\s\S]*?)\n```$", trimmed, flags=re.IGNORECASE)
    return match.group(1).strip() if match else answer
