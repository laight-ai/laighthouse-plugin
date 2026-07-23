"""python-docx section renderers consumed by build.py."""
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Pt, RGBColor

import charts


def add_title(document, title, period=None):
    document.add_heading(title, level=1)
    if period:
        p = document.add_paragraph(f"기간: {period}")
        p.runs[0].font.size = Pt(10)
        p.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)


def add_heading(document, text):
    document.add_heading(text, level=2)


def _diff_color(diff_value):
    if diff_value is None:
        return None
    if diff_value > 0:
        return RGBColor(0x16, 0xA3, 0x4A)
    if diff_value < 0:
        return RGBColor(0xDC, 0x26, 0x26)
    return RGBColor(0x6B, 0x72, 0x80)


def add_kpi_cards(document, cards):
    table = document.add_table(rows=2, cols=len(cards))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for col, card in enumerate(cards):
        table.cell(0, col).text = card["label"]

        value_cell = table.cell(1, col)
        value_text = card["value"]
        if card.get("diff"):
            value_text += f"  ({card['diff']})"
        value_cell.text = value_text

        value_run = value_cell.paragraphs[0].runs[0]
        value_run.font.size = Pt(14)
        value_run.font.bold = True
        color = _diff_color(card.get("diff_value"))
        if color is not None:
            value_run.font.color.rgb = color


def add_data_table(document, heading, headers, rows):
    if heading:
        add_heading(document, heading)
    table = document.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = header
        cell.paragraphs[0].runs[0].font.bold = True
    for row_idx, row in enumerate(rows, start=1):
        for col, value in enumerate(row):
            table.cell(row_idx, col).text = str(value)


def add_text_section(document, heading, body):
    if heading:
        add_heading(document, heading)
    document.add_paragraph(body)


def add_combo_chart_section(document, heading, categories, bar_series, line_series):
    if heading:
        add_heading(document, heading)
    charts.add_combo_chart(document, categories, bar_series, line_series)
