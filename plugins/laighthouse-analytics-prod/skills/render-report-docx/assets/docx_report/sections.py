"""python-docx section renderers consumed by build.py.

Written fresh for this skill (no reuse of the reverted first-generation
renderer): every component styles itself from theme.py — banner section
headers with an accent bar, tinted KPI cards, borderless header-band tables
with content-proportional column widths, and a footer with live page
numbers. Display rounding happens once in _prettify(), and large tables
drop 매출(gross) 0원 rows before rendering.
"""
import re

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor

import charts
import theme

_TOTAL_ROW_LABELS = {"합계", "총계"}
_GROSS_HEADERS = {"매출", "전환매출", "매출액"}
_BAR_WIDTH_EMU = Emu(914400)  # 1 inch, matches the fixed-width CSS bar track


# ── text helpers ───────────────────────────────────────────────────────

def _rgb(hex_color):
    return RGBColor.from_string(hex_color.lstrip("#").upper())


_LONG_DECIMAL = re.compile(r"(\d+)\.(\d{3,})")


def _prettify(text):
    """Round runaway float precision for display: 55.88918788518661 → 55.89.
    Only decimal runs of 3+ places are touched, so pre-formatted values
    (2,449.08 / 727% / dates) pass through unchanged."""
    def _round(match):
        rounded = round(float(f"{match.group(1)}.{match.group(2)}"), 2)
        return f"{rounded:.2f}".rstrip("0").rstrip(".")
    return _LONG_DECIMAL.sub(_round, str(text))


def _style_run(run, size=None, color=None, bold=None):
    run.font.name = theme.FONT
    # Korean glyphs resolve through the eastAsia slot, not the latin one
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), theme.FONT)
    if size is not None:
        run.font.size = size
    if color is not None:
        run.font.color.rgb = _rgb(color)
    if bold is not None:
        run.font.bold = bold
    return run


def _para(container, text="", size=None, color=None, bold=None,
          space_before=Pt(0), space_after=Pt(0), align=None, first=False):
    if first and container.paragraphs and not container.paragraphs[0].runs:
        p = container.paragraphs[0]
    else:
        p = container.add_paragraph()
    p.paragraph_format.space_before = space_before
    p.paragraph_format.space_after = space_after
    if align is not None:
        p.alignment = align
    if text != "":
        _style_run(p.add_run(), size=size, color=color, bold=bold).text = _prettify(text)
    return p


# ── oxml helpers ───────────────────────────────────────────────────────

def _edge(name, val="single", sz=4, color="auto"):
    el = OxmlElement(f"w:{name}")
    el.set(qn("w:val"), val)
    if val != "nil":
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
    return el


def _shade_cell(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#").upper())
    cell._tc.get_or_add_tcPr().append(shd)


def _set_table_borders(table, **edges):
    borders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        spec = edges.get(name, "nil")
        if spec == "nil":
            borders.append(_edge(name, "nil"))
        else:
            val, sz, color = spec
            borders.append(_edge(name, val, sz, color))
    table._tbl.tblPr.append(borders)


def _set_cell_border(cell, name, val="single", sz=4, color="auto"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    borders.append(_edge(name, val, sz, color))


def _set_cell_margins(table, top=80, bottom=80, left=110, right=110):
    mar = OxmlElement("w:tblCellMar")
    for name, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    table._tbl.tblPr.append(mar)


def _fixed_layout(table, col_widths):
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)
    for idx, width in enumerate(col_widths):
        table.columns[idx].width = width
        for cell in table.columns[idx].cells:
            cell.width = width


# ── document scaffold ──────────────────────────────────────────────────

def setup_document(document):
    section = document.sections[0]
    section.page_width = theme.PAGE_W
    section.page_height = theme.PAGE_H
    section.top_margin = section.bottom_margin = theme.MARGIN
    section.left_margin = section.right_margin = theme.MARGIN

    normal = document.styles["Normal"]
    normal.font.name = theme.FONT
    normal.font.size = theme.SIZE_BODY
    normal.font.color.rgb = _rgb(theme.TEXT)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), theme.FONT)
    normal.paragraph_format.space_after = Pt(0)


def add_title(document, title, period=None):
    _para(document, title, size=theme.SIZE_TITLE, color=theme.TEXT_STRONG,
          bold=True, first=True)
    p = _para(document, f"📅 {period}" if period else "",
              size=theme.SIZE_PERIOD, color=theme.TEXT_MUTED,
              space_before=Pt(2), space_after=Pt(8))
    # thick accent rule closing the header block
    pbdr = OxmlElement("w:pBdr")
    pbdr.append(_edge("bottom", "single", 18, theme.ACCENT))
    p.paragraph_format.element.get_or_add_pPr().append(pbdr)


def add_heading(document, text):
    """Section header: full-width tinted banner with an accent left bar —
    the .section-title translated into a print-document device."""
    p = _para(document, text, size=theme.SIZE_SECTION, color=theme.TEXT_STRONG,
              bold=True, space_before=Pt(18), space_after=Pt(10))
    ppr = p.paragraph_format.element.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), theme.FILL_BANNER)
    ppr.append(shd)
    pbdr = OxmlElement("w:pBdr")
    pbdr.append(_edge("left", "single", 20, theme.ACCENT))
    ppr.append(pbdr)
    p.paragraph_format.left_indent = Pt(6)
    p.paragraph_format.keep_with_next = True
    return p


def add_footer(document):
    """Centered brand line + live page number at the right edge."""
    footer = document.sections[0].footer
    p = footer.paragraphs[0]
    p.paragraph_format.tab_stops.add_tab_stop(Emu(int(theme.CONTENT_W) // 2),
                                              WD_TAB_ALIGNMENT.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Emu(int(theme.CONTENT_W)),
                                              WD_TAB_ALIGNMENT.RIGHT)
    _style_run(p.add_run("\t"), size=theme.SIZE_FOOTER)
    _style_run(p.add_run("Engineered by Laighthouse AI"),
               size=theme.SIZE_FOOTER, color=theme.TEXT_FAINT)
    _style_run(p.add_run("\t"), size=theme.SIZE_FOOTER)
    fld = parse_xml(
        '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        ' w:instr=" PAGE "><w:r><w:rPr><w:color w:val="94A3B8"/>'
        '<w:sz w:val="17"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>')
    p._p.append(fld)


# ── KPI cards ──────────────────────────────────────────────────────────

def add_kpi_cards(document, cards):
    """Tinted, bordered card cells separated by spacer columns — the HTML
    flex card row."""
    n = len(cards)
    cols = 2 * n - 1
    gap = Cm(0.25)
    card_w = Emu(int((theme.CONTENT_W - gap * (n - 1)) / n))
    table = document.add_table(rows=1, cols=cols)
    _set_table_borders(table)  # all nil; card edges are per-cell
    _set_cell_margins(table, top=130, bottom=130, left=110, right=110)
    _fixed_layout(table, [card_w if i % 2 == 0 else gap for i in range(cols)])

    for i, card in enumerate(cards):
        cell = table.rows[0].cells[2 * i]
        _shade_cell(cell, theme.FILL_CARD)
        for edge_name in ("top", "left", "bottom", "right"):
            _set_cell_border(cell, edge_name, "single", 4, theme.BORDER)

        _para(cell, card["label"], size=theme.SIZE_KPI_LABEL,
              color=theme.TEXT_MUTED, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_after=Pt(3), first=True)
        accent = card.get("accent")
        _para(cell, card["value"], size=theme.SIZE_KPI_VALUE, bold=True,
              color=accent.lstrip("#") if accent else theme.TEXT_STRONG,
              align=WD_ALIGN_PARAGRAPH.CENTER)
        if card.get("diff"):
            _para(cell, card["diff"], size=theme.SIZE_KPI_DIFF, bold=True,
                  color=theme.diff_color(card.get("diff_value")) or theme.GRAY,
                  align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(3))
    _para(document, "", space_after=Pt(4))  # breathing room below the row


# ── data tables ────────────────────────────────────────────────────────

def _is_bar_cell(value):
    return isinstance(value, dict) and value.get("type") == "bar"


def _is_rich_cell(value):
    return isinstance(value, dict) and "text" in value


def _cell_text(value):
    if _is_bar_cell(value):
        return str(value.get("label", ""))
    if _is_rich_cell(value):
        return str(value["text"])
    return str(value)


def _display_width(value):
    """Rendered width in half-width character units — CJK glyphs count
    double, so Korean name columns get the room they need."""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in _prettify(_cell_text(value)))


def _column_widths(headers, rows):
    """Content-proportional widths with the header's own width as the floor,
    so short columns never wrap their header vertically."""
    scores = []
    for c, header in enumerate(headers):
        header_width = _display_width(header)
        longest = header_width
        for row in rows:
            if c < len(row):
                longest = max(longest, _display_width(row[c]))
        scores.append(min(max(longest, header_width + 2, 8), 40))
    total_score = sum(scores)
    widths = [Emu(int(int(theme.CONTENT_W) * s / total_score)) for s in scores]
    widths[-1] = Emu(int(theme.CONTENT_W) - sum(int(w) for w in widths[:-1]))
    return widths


def _is_total_row(row):
    return bool(row) and _cell_text(row[0]) in _TOTAL_ROW_LABELS


def _is_zero_amount(value):
    text = _cell_text(value).replace("₩", "").replace(",", "").replace("원", "").strip()
    try:
        return float(text) == 0
    except ValueError:
        return False


def filter_zero_gross(headers, rows):
    """대용량 표에서 매출(gross) 0원 행 제외 — only kicks in above
    ZERO_GROSS_FILTER_MIN_ROWS so small summary tables stay complete.
    합계/총계 rows are always kept. Returns (rows, removed_count)."""
    if len(rows) <= theme.ZERO_GROSS_FILTER_MIN_ROWS:
        return rows, 0
    gross_col = next((i for i, h in enumerate(headers)
                      if str(h).strip() in _GROSS_HEADERS), None)
    if gross_col is None:
        return rows, 0
    kept = [row for row in rows
            if _is_total_row(row)
            or gross_col >= len(row)
            or not _is_zero_amount(row[gross_col])]
    return kept, len(rows) - len(kept)


def _truncate_rows(rows, limit):
    """Keep the first rows, always preserving a trailing 합계/총계 row."""
    if len(rows) <= limit:
        return rows, 0
    total_row = None
    body = rows
    if _is_total_row(rows[-1]):
        total_row, body = rows[-1], rows[:-1]
    keep = limit - (1 if total_row is not None else 0)
    shown = body[:keep]
    hidden = len(body) - keep
    if total_row is not None:
        shown = shown + [total_row]
    return shown, hidden


def _set_repeat_header_row(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def _render_bar_cell(cell, pct, color, label):
    """Approximate a CSS `width:{pct}%` progress bar with a 2-cell nested
    table (filled + track); Word has no native proportional-width bar."""
    pct = max(0.0, min(float(pct), 100.0))
    cell.text = ""
    bar_table = cell.add_table(rows=1, cols=2)
    bar_table.autofit = False
    filled_width = Emu(int(_BAR_WIDTH_EMU * pct / 100))
    track_width = _BAR_WIDTH_EMU - filled_width
    filled_cell, track_cell = bar_table.rows[0].cells
    bar_table.columns[0].width = filled_width
    bar_table.columns[1].width = track_width
    filled_cell.width = filled_width
    track_cell.width = track_width
    _shade_cell(filled_cell, color)
    _shade_cell(track_cell, theme.BORDER)
    _para(cell, label, size=Pt(8), color=theme.TEXT_MUTED, space_before=Pt(2))


def add_data_table(document, heading, headers, rows, rows_total=None):
    if heading:
        add_heading(document, heading)

    original_count = rows_total if rows_total is not None \
        else sum(1 for row in rows if not _is_total_row(row))
    rows, zero_removed = filter_zero_gross(headers, rows)
    shown, _ = _truncate_rows(rows, theme.MAX_TABLE_ROWS)
    body_shown = sum(1 for row in shown if not _is_total_row(row))
    hidden = max(original_count - zero_removed - body_shown, 0)

    table = document.add_table(rows=1 + len(shown), cols=len(headers))
    _set_table_borders(
        table,
        bottom=("single", 4, theme.BORDER),
        insideH=("single", 4, theme.BORDER_SOFT),
    )
    _set_cell_margins(table)
    _fixed_layout(table, _column_widths(headers, shown))

    header_row = table.rows[0]
    _set_repeat_header_row(header_row)
    for col, header in enumerate(headers):
        cell = header_row.cells[col]
        _shade_cell(cell, theme.FILL_HEADER)
        _set_cell_border(cell, "bottom", "single", 6, theme.BORDER)
        _para(cell, str(header), size=theme.SIZE_TH, color=theme.TEXT_TH,
              bold=True, first=True)

    for row_idx, row in enumerate(shown, start=1):
        row_cells = table.rows[row_idx].cells
        is_total = _is_total_row(row)
        for col, value in enumerate(row):
            cell = row_cells[col]
            if _is_bar_cell(value):
                _render_bar_cell(cell, value["pct"], value.get("color", theme.ACCENT),
                                 value.get("label", f"{value['pct']}%"))
            elif _is_rich_cell(value):
                _para(cell, value["text"], size=theme.SIZE_TD,
                      color=value.get("color", theme.TEXT_TABLE),
                      bold=value.get("bold", is_total), first=True)
            else:
                _para(cell, value, size=theme.SIZE_TD, color=theme.TEXT_TABLE,
                      bold=is_total or None, first=True)
            if is_total:
                _shade_cell(cell, theme.FILL_HEADER)

    notes = []
    if zero_removed:
        notes.append(f"매출 0원 {zero_removed}행 제외")
    if hidden:
        notes.append(f"상위 {body_shown}행 표시 · 외 {hidden}행 생략")
    if notes:
        _para(document, " · ".join(notes), size=theme.SIZE_CAPTION,
              color=theme.TEXT_FAINT, space_before=Pt(3))
    return table


# ── text & chart sections ──────────────────────────────────────────────

def _is_subheading(line):
    """Short label lines between paragraphs (Overview / 국내분유 / 커피)
    render as bold subheadings — sentence lines end with a stop."""
    text = line.strip()
    return bool(text) and _display_width(text) <= 30 \
        and not text.endswith((".", "!", "?", "%"))


def add_text_section(document, heading, body):
    if heading:
        add_heading(document, heading)
    lines = str(body).split("\n")
    for i, line in enumerate(lines):
        if _is_subheading(line):
            _para(document, line, size=theme.SIZE_SUBHEAD, color=theme.TEXT_STRONG,
                  bold=True, space_before=Pt(10) if i else Pt(0), space_after=Pt(2))
        else:
            p = _para(document, line, size=theme.SIZE_BODY, color=theme.TEXT_TABLE,
                      space_after=Pt(5))
            p.paragraph_format.line_spacing = 1.3


def add_combo_chart_section(document, heading, categories, bar_series, line_series):
    if heading:
        add_heading(document, heading)
    charts.add_combo_chart(document, categories, bar_series, line_series)
