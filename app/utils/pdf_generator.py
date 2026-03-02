from __future__ import annotations

from datetime import datetime
import os
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _money(value: float | int) -> str:
    return f"{value:,.0f} so'm".replace(",", " ")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


async def generate_pdf_report(report_data: dict[str, Any], filename: str | None = None) -> str:
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/hisobot_{timestamp}.pdf"

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )
    styles = getSampleStyleSheet()
    story = []

    period = _safe_text(report_data.get("period", "Hisobot"))
    story.append(Paragraph(period, styles["Title"]))
    story.append(Spacer(1, 10))

    summary_rows = [
        ["Jami kirim", _money(float(report_data.get("total_income", 0)))],
        ["Jami xarajat", _money(float(report_data.get("total_expenses", 0)))],
        ["Balans", _money(float(report_data.get("balance", 0)))],
    ]
    summary_table = Table(summary_rows, colWidths=[180, 180])
    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 12))

    lines: list[list[str]] = [["Sana", "Turi", "Kategoriya", "Miqdor", "Izoh"]]

    for income in report_data.get("incomes", []):
        lines.append(
            [
                income.date.strftime("%d.%m.%Y"),
                "KIRIM",
                _safe_text(getattr(income, "category", "")),
                _money(float(getattr(income, "amount", 0))),
                _safe_text(getattr(income, "description", "")),
            ]
        )

    for expense in report_data.get("expenses", []):
        lines.append(
            [
                expense.date.strftime("%d.%m.%Y"),
                "XARAJAT",
                _safe_text(getattr(expense, "category", "")),
                _money(float(getattr(expense, "amount", 0))),
                _safe_text(getattr(expense, "description", "")),
            ]
        )

    if len(lines) == 1:
        lines.append(["-", "-", "-", "-", "Ma'lumot topilmadi"])

    data_table = Table(lines, colWidths=[70, 60, 110, 90, 180], repeatRows=1)
    data_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(data_table)

    category_totals = report_data.get("category_totals", {})
    if category_totals:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Kategoriyalar bo'yicha", styles["Heading3"]))
        cat_rows = [["Kategoriya", "Summa"]]
        for category, amount in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
            cat_rows.append([_safe_text(category), _money(float(amount))])

        cat_table = Table(cat_rows, colWidths=[220, 140], repeatRows=1)
        cat_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ]
            )
        )
        story.append(cat_table)

    doc.build(story)
    return filename
