from io import BytesIO
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.interview import InterviewReportRead


def build_interview_pdf(report: InterviewReportRead) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#4338ca"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story: list = []
    story.append(Paragraph("Hack2Hire — Interview Report", title_style))
    story.append(
        Paragraph(
            f"Session: {report.session_id} · Grade: <b>{report.grade}</b>",
            body_style,
        ),
    )
    story.append(Spacer(1, 12))

    summary_data = [
        ["Overall Score", f"{report.overall_score:.0f}%"],
        ["Readiness Score", f"{report.readiness_score:.0f}%"],
        ["Questions Answered", f"{len(report.answers)}/{len(report.questions)}"],
    ]
    if report.terminated_early:
        summary_data.append(["Status", "Terminated Early"])

    summary_table = Table(summary_data, colWidths=[2.2 * inch, 3.5 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ],
        ),
    )
    story.append(summary_table)
    story.append(Spacer(1, 16))

    if report.performance_breakdown:
        story.append(Paragraph("Performance Breakdown", heading_style))
        breakdown_rows = [["Dimension", "Score"]]
        for key, value in report.performance_breakdown.items():
            breakdown_rows.append([key.replace("_", " ").title(), f"{float(value):.0f}%"])
        breakdown_table = Table(breakdown_rows, colWidths=[2.5 * inch, 1.5 * inch])
        breakdown_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ],
            ),
        )
        story.append(breakdown_table)
        story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(report.summary.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Strengths", heading_style))
    for item in report.strengths:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Paragraph("Weaknesses", heading_style))
    for item in report.weaknesses:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Paragraph("Recommendations", heading_style))
    for item in report.improvements:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Paragraph("Q&amp;A Transcript", heading_style))
    for question in report.questions:
        answer = next((a for a in report.answers if a.question_index == question.question_index), None)
        q_label = (
            f"<b>Q{question.question_index + 1}</b> "
            f"[{question.difficulty or 'medium'} · {question.category or 'general'}]"
        )
        story.append(Paragraph(q_label, body_style))
        story.append(Paragraph(question.question_text, body_style))
        if answer:
            score_text = f" — Score: {answer.score:.0f}%" if answer.score is not None else ""
            story.append(
                Paragraph(f"<b>Your answer{score_text}:</b> {answer.answer_text[:2000]}", body_style),
            )
            if answer.feedback:
                story.append(Paragraph(f"<i>Feedback: {answer.feedback}</i>", body_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buffer.getvalue()
