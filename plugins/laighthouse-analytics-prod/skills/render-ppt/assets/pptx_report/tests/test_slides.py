from pptx import Presentation
from pptx.util import Emu

import slides as sl
import theme


def _prs():
    prs = Presentation()
    prs.slide_width = theme.SLIDE_W
    prs.slide_height = theme.SLIDE_H
    return prs


def _texts(slide):
    out = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            out.extend(p.text for p in shape.text_frame.paragraphs)
    return out


def test_cover_slide_title_and_period():
    prs = _prs()
    slide = sl.add_cover_slide(prs, "다형식품 MTD 보고서", "2026-05-01 ~ 2026-05-15")
    texts = _texts(slide)
    assert "다형식품 MTD 보고서" in texts
    assert any("2026-05-01" in t for t in texts)
    assert any("Engineered by Laighthouse AI" in t for t in texts)


def test_slide_background_is_page_tint():
    prs = _prs()
    slide = sl.add_cover_slide(prs, "t")
    assert str(slide.background.fill.fore_color.rgb) == theme.FILL_PAGE


def test_kpi_slide_cards_and_diff_colors():
    prs = _prs()
    slide = sl.add_kpi_slide(prs, "월 목표", [
        {"label": "월 매출 목표", "value": "₩ 250,000,000"},
        {"label": "ROAS", "value": "520%", "accent": "#3b82f6"},
        {"label": "증감", "value": "1", "diff": "▲ +2%", "diff_value": 2},
    ], page_no=2)
    texts = _texts(slide)
    assert "월 목표" in texts
    assert "₩ 250,000,000" in texts
    # find the accent-colored value run and the green diff run
    runs = [r for shape in slide.shapes if shape.has_text_frame
            for p in shape.text_frame.paragraphs for r in p.runs]
    accent_run = next(r for r in runs if r.text == "520%")
    assert str(accent_run.font.color.rgb) == "3B82F6"
    diff_run = next(r for r in runs if r.text == "▲ +2%")
    assert str(diff_run.font.color.rgb) == theme.GREEN


def test_table_slide_header_fill_and_no_default_style():
    prs = _prs()
    slide = sl.add_table_slide(prs, "캠페인별 성과", ["캠페인", "ROAS"],
                               [["브랜드검색", "727%"], ["합계", "573%"]], page_no=3)
    table = next(s for s in slide.shapes if s.has_table).table
    tbl_pr = table._tbl.tblPr
    assert tbl_pr.get("firstRow") == "0"
    assert tbl_pr.get("bandRow") == "0"
    header_cell = table.cell(0, 0)
    assert str(header_cell.fill.fore_color.rgb) == theme.FILL_HEADER
    # total row shaded + bold
    total_cell = table.cell(2, 0)
    assert str(total_cell.fill.fore_color.rgb) == theme.FILL_HEADER
    run = total_cell.text_frame.paragraphs[0].runs[0]
    assert run.font.bold is True
    assert run.font.name == theme.FONT


def test_table_slide_truncates_to_top_n_preserving_total():
    rows = [[f"항목{i}", str(i)] for i in range(30)] + [["합계", "999"]]
    prs = _prs()
    slide = sl.add_table_slide(prs, "표", ["이름", "값"], rows, max_rows=12)
    table = next(s for s in slide.shapes if s.has_table).table
    assert len(table.rows) == 1 + 12  # header + 12 body rows
    last_row_label = table.cell(12, 0).text_frame.text
    assert last_row_label == "합계"
    texts = _texts(slide)
    assert any("외 19행 생략" in t for t in texts)


def test_table_slide_rows_total_overrides_hidden_count():
    # source data was already truncated to 15 rows upstream; the caption
    # must report against the full dataset (rows_total), not the file
    rows = [[f"kw{i}", str(i)] for i in range(15)]
    prs = _prs()
    slide = sl.add_table_slide(prs, "키워드별 성과", ["키워드", "값"], rows,
                               max_rows=12, rows_total=1234)
    table = next(s for s in slide.shapes if s.has_table).table
    assert len(table.rows) == 1 + 12
    assert any("외 1222행 생략" in t for t in _texts(slide))


def test_table_slide_rows_total_with_preserved_total_row():
    rows = [[f"kw{i}", str(i)] for i in range(15)] + [["합계", "999"]]
    prs = _prs()
    slide = sl.add_table_slide(prs, "표", ["이름", "값"], rows,
                               max_rows=12, rows_total=1000)
    # 12 rows shown, one of them the 합계 row -> 11 body rows visible
    assert any("외 989행 생략" in t for t in _texts(slide))


def test_table_slide_no_truncation_note_when_small():
    prs = _prs()
    slide = sl.add_table_slide(prs, "표", ["a"], [["1"], ["2"]])
    assert not any("생략" in t for t in _texts(slide))


def test_table_slide_rich_and_bar_cells():
    prs = _prs()
    slide = sl.add_table_slide(prs, "표", ["지표", "달성률", "증감"], [
        ["매출",
         {"type": "bar", "pct": 53.0, "color": "3B82F6", "label": "53.0%"},
         {"text": "▲ +12.4%", "color": "#16a34a", "bold": True}],
    ])
    table = next(s for s in slide.shapes if s.has_table).table
    bar_run = table.cell(1, 1).text_frame.paragraphs[0].runs[0]
    assert bar_run.text == "53.0%"
    assert str(bar_run.font.color.rgb) == "3B82F6"
    rich_run = table.cell(1, 2).text_frame.paragraphs[0].runs[0]
    assert str(rich_run.font.color.rgb) == "16A34A"
    assert rich_run.font.bold is True


def test_text_slide_multiline_in_card():
    prs = _prs()
    slide = sl.add_text_slide(prs, "Executive Summary", "첫 줄.\n둘째 줄.", page_no=4)
    texts = _texts(slide)
    assert "첫 줄." in texts
    assert "둘째 줄." in texts


def test_divider_slide():
    prs = _prs()
    slide = sl.add_divider_slide(prs, "부록")
    assert "부록" in _texts(slide)
