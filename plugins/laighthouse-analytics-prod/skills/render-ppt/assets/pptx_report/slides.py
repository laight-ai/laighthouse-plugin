"""python-pptx slide builders consumed by build.py.

Each section-JSON object becomes one 16:9 slide. Unlike Word's flow layout,
slides give absolute positioning and real shapes, so the HTML report's card
UI (rounded corners, tinted page background, subtle borders) is reproduced
directly instead of approximated.
"""
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

import charts
import theme

_TOTAL_ROW_LABELS = {"합계", "총계"}
_NO_GRID_TABLE_STYLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # "No Style, No Grid"


# ── low-level helpers ──────────────────────────────────────────────────

def _rgb(hex_color):
    return RGBColor.from_string(hex_color.lstrip("#").upper())


def _style_run(run, size, color, bold=False):
    run.font.name = theme.FONT
    # Korean glyphs resolve through the eastAsia slot, not the latin one
    rpr = run._r.get_or_add_rPr()
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = rpr.makeelement(qn("a:ea"), {})
        rpr.append(ea)
    ea.set("typeface", theme.FONT)
    run.font.size = size
    run.font.color.rgb = _rgb(color)
    run.font.bold = bold
    return run


def _textbox(slide, x, y, w, h):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return box


def _add_line(tf, text, size, color, bold=False, first=False,
              align=PP_ALIGN.LEFT, space_before=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    if space_before is not None:
        p.space_before = space_before
    _style_run(p.add_run(), size, color, bold).text = str(text)
    return p


def _card(slide, x, y, w, h, fill=theme.FILL_CARD, line=theme.BORDER):
    """Rounded-corner card — the .card CSS class made of an actual shape."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shape.adjustments[0] = 0.045
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(fill)
    shape.line.color.rgb = _rgb(line)
    shape.line.width = Pt(0.75)
    shape.shadow.inherit = False
    shape.text_frame.paragraphs[0].text = ""
    return shape


def _blank_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # fully blank layout
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(theme.FILL_PAGE)
    return slide


def _footer(slide, page_no=None):
    box = _textbox(slide, theme.MARGIN, theme.FOOTER_TOP,
                   theme.CONTENT_W, Emu(274320))
    p = box.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _style_run(p.add_run(), theme.SIZE_FOOTER, theme.TEXT_FAINT).text = \
        "Engineered by Laighthouse AI"
    if page_no is not None:
        num = _textbox(slide, theme.SLIDE_W - theme.MARGIN - Emu(457200),
                       theme.FOOTER_TOP, Emu(457200), Emu(274320))
        np = num.text_frame.paragraphs[0]
        np.alignment = PP_ALIGN.RIGHT
        _style_run(np.add_run(), theme.SIZE_FOOTER, theme.TEXT_FAINT).text = str(page_no)


def _slide_title(slide, text):
    """Accent bar + bold title — the .section-title analogue."""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, theme.MARGIN, theme.TITLE_TOP,
        Emu(54864), theme.TITLE_H)  # 0.06 in wide
    bar.adjustments[0] = 0.5
    bar.fill.solid()
    bar.fill.fore_color.rgb = _rgb(theme.ACCENT)
    bar.line.fill.background()
    bar.shadow.inherit = False
    box = _textbox(slide, theme.MARGIN + Emu(137160), theme.TITLE_TOP,
                   theme.CONTENT_W - Emu(137160), theme.TITLE_H)
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    _add_line(box.text_frame, text, theme.SIZE_SLIDE_TITLE, theme.TEXT_STRONG,
              bold=True, first=True)


def _content_slide(prs, heading, page_no=None):
    slide = _blank_slide(prs)
    if heading:
        _slide_title(slide, heading)
    _footer(slide, page_no)
    return slide


# ── slides ─────────────────────────────────────────────────────────────

def add_cover_slide(prs, title, period=None):
    slide = _blank_slide(prs)
    center_y = Emu(int(theme.SLIDE_H * 0.36))
    bar = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, theme.MARGIN, center_y - Emu(137160),
        Emu(731520), Emu(54864))  # short horizontal accent line
    bar.adjustments[0] = 0.5
    bar.fill.solid()
    bar.fill.fore_color.rgb = _rgb(theme.ACCENT)
    bar.line.fill.background()
    bar.shadow.inherit = False

    box = _textbox(slide, theme.MARGIN, center_y, theme.CONTENT_W, Emu(1371600))
    tf = box.text_frame
    _add_line(tf, title, theme.SIZE_COVER_TITLE, theme.TEXT_STRONG,
              bold=True, first=True)
    if period:
        p = _add_line(tf, f"📅 {period}", theme.SIZE_COVER_PERIOD, theme.TEXT_MUTED)
        p.space_before = Pt(10)
    _footer(slide)
    return slide


def add_divider_slide(prs, text, page_no=None):
    slide = _blank_slide(prs)
    box = _textbox(slide, theme.MARGIN, Emu(int(theme.SLIDE_H * 0.42)),
                   theme.CONTENT_W, Emu(914400))
    _add_line(box.text_frame, text, theme.SIZE_DIVIDER, theme.TEXT_STRONG,
              bold=True, first=True, align=PP_ALIGN.CENTER)
    _footer(slide, page_no)
    return slide


def add_kpi_slide(prs, heading, cards, page_no=None):
    slide = _content_slide(prs, heading, page_no)
    n = len(cards)
    gap = Emu(228600)  # 0.25 in
    card_w = Emu(int((theme.CONTENT_W - gap * (n - 1)) / n))
    card_h = Emu(1600200)  # 1.75 in
    y = theme.CONTENT_TOP + Emu(int((theme.CONTENT_H - card_h) * 0.35))
    for i, card in enumerate(cards):
        x = theme.MARGIN + Emu(int((card_w + gap) * i))
        shape = _card(slide, x, y, card_w, card_h)
        tf = shape.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = Emu(182880)
        _add_line(tf, card["label"], theme.SIZE_KPI_LABEL, theme.TEXT_MUTED,
                  first=True, align=PP_ALIGN.CENTER)
        accent = card.get("accent")
        value_p = _add_line(tf, card["value"], theme.SIZE_KPI_VALUE,
                            accent.lstrip("#") if accent else theme.TEXT_STRONG,
                            bold=True, align=PP_ALIGN.CENTER)
        value_p.space_before = Pt(6)
        if card.get("diff"):
            diff_p = _add_line(tf, card["diff"], theme.SIZE_KPI_DIFF,
                               theme.diff_color(card.get("diff_value")) or theme.GRAY,
                               bold=True, align=PP_ALIGN.CENTER)
            diff_p.space_before = Pt(4)
    return slide


def _is_bar_cell(value):
    return isinstance(value, dict) and value.get("type") == "bar"


def _is_rich_cell(value):
    return isinstance(value, dict) and "text" in value


def _truncate_rows(rows, limit):
    """상위 N개 규칙: keep the first rows, always preserving a trailing
    합계/총계 row, and report how many body rows were dropped."""
    if len(rows) <= limit:
        return rows, 0
    total_row = None
    body = rows
    first_cell = rows[-1][0] if rows[-1] else ""
    if _is_rich_cell(first_cell):
        first_cell = first_cell["text"]
    if str(first_cell) in _TOTAL_ROW_LABELS:
        total_row, body = rows[-1], rows[:-1]
    keep = limit - (1 if total_row is not None else 0)
    shown = body[:keep]
    hidden = len(body) - keep
    if total_row is not None:
        shown = shown + [total_row]
    return shown, hidden


def _fill_cell(cell, text, size, color, bold=False, fill=None):
    cell.margin_left = cell.margin_right = Emu(109728)
    cell.margin_top = cell.margin_bottom = Emu(45720)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if fill:
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(fill)
    else:
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(theme.FILL_CARD)
    _add_line(cell.text_frame, text, size, color, bold, first=True)
    # bottom hairline — the HTML row's border-bottom
    tc_pr = cell._tc.get_or_add_tcPr()
    ln_b = tc_pr.makeelement(qn("a:lnB"), {"w": "6350", "cap": "flat"})
    fill_el = ln_b.makeelement(qn("a:solidFill"), {})
    clr = fill_el.makeelement(qn("a:srgbClr"), {"val": theme.BORDER_SOFT})
    fill_el.append(clr)
    ln_b.append(fill_el)
    tc_pr.append(ln_b)


def add_table_slide(prs, heading, headers, rows, page_no=None,
                    max_rows=theme.MAX_TABLE_ROWS):
    slide = _content_slide(prs, heading, page_no)
    shown, hidden = _truncate_rows(rows, max_rows)

    header_h = Emu(320040)
    row_h = Emu(292608)
    table_h = Emu(int(header_h + row_h * len(shown)))
    gf = slide.shapes.add_table(1 + len(shown), len(headers),
                                theme.MARGIN, theme.CONTENT_TOP,
                                theme.CONTENT_W, table_h)
    table = gf.table
    # drop PowerPoint's default banded blue theme entirely
    tbl_pr = table._tbl.tblPr
    tbl_pr.set("firstRow", "0")
    tbl_pr.set("bandRow", "0")
    style_el = tbl_pr.find(qn("a:tableStyleId"))
    if style_el is None:
        style_el = tbl_pr.makeelement(qn("a:tableStyleId"), {})
        tbl_pr.append(style_el)
    style_el.text = _NO_GRID_TABLE_STYLE

    table.rows[0].height = header_h
    for r in range(1, 1 + len(shown)):
        table.rows[r].height = row_h

    for c, header in enumerate(headers):
        _fill_cell(table.cell(0, c), header, theme.SIZE_TH, theme.TEXT_TH,
                   bold=True, fill=theme.FILL_HEADER)

    for r, row in enumerate(shown, start=1):
        first_cell = row[0] if row else ""
        if _is_rich_cell(first_cell):
            first_cell = first_cell["text"]
        is_total = str(first_cell) in _TOTAL_ROW_LABELS
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            fill = theme.FILL_HEADER if is_total else None
            if _is_bar_cell(value):
                _fill_cell(cell, value.get("label", f"{value['pct']}%"),
                           theme.SIZE_TD, value.get("color", theme.ACCENT),
                           bold=True, fill=fill)
            elif _is_rich_cell(value):
                _fill_cell(cell, value["text"], theme.SIZE_TD,
                           value.get("color", theme.TEXT_TABLE),
                           bold=value.get("bold", is_total), fill=fill)
            else:
                _fill_cell(cell, value, theme.SIZE_TD, theme.TEXT_TABLE,
                           bold=is_total, fill=fill)

    if hidden:
        note = _textbox(slide, theme.MARGIN,
                        theme.CONTENT_TOP + table_h + Emu(91440),
                        theme.CONTENT_W, Emu(274320))
        _add_line(note.text_frame, f"외 {hidden}행 생략 — 상위 {max_rows}개 기준",
                  theme.SIZE_TABLE_NOTE, theme.TEXT_FAINT, first=True)
    return slide


def add_text_slide(prs, heading, body, page_no=None):
    slide = _content_slide(prs, heading, page_no)
    card = _card(slide, theme.MARGIN, theme.CONTENT_TOP,
                 theme.CONTENT_W, theme.CONTENT_H)
    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Emu(274320)
    tf.margin_top = tf.margin_bottom = Emu(228600)
    for i, line in enumerate(str(body).split("\n")):
        p = _add_line(tf, line, theme.SIZE_BODY, theme.TEXT_TABLE, first=(i == 0))
        p.line_spacing = 1.3
        p.space_after = Pt(6)
    return slide


def add_chart_slide(prs, heading, categories, bar_series, line_series,
                    page_no=None):
    slide = _content_slide(prs, heading, page_no)
    _card(slide, theme.MARGIN, theme.CONTENT_TOP, theme.CONTENT_W, theme.CONTENT_H)
    pad = Emu(182880)
    charts.add_combo_chart(
        slide, prs.part.package, categories, bar_series, line_series,
        x=theme.MARGIN + pad, y=theme.CONTENT_TOP + pad,
        cx=theme.CONTENT_W - 2 * pad, cy=theme.CONTENT_H - 2 * pad,
    )
    return slide
