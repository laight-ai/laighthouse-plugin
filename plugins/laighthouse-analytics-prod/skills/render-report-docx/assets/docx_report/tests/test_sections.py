from docx import Document
from docx.oxml.ns import qn

import sections as sec
import theme


def _doc():
    d = Document()
    sec.setup_document(d)
    return d


def test_setup_document_a4_and_korean_font():
    d = _doc()
    s = d.sections[0]
    assert abs(s.page_width - theme.PAGE_W) < 1000   # twips round-trip
    assert abs(s.page_height - theme.PAGE_H) < 1000
    normal = d.styles["Normal"]
    assert normal.font.name == theme.FONT
    rfonts = normal.element.get_or_add_rPr().get_or_add_rFonts()
    assert rfonts.get(qn("w:eastAsia")) == theme.FONT


def test_title_block_with_accent_rule():
    d = _doc()
    sec.add_title(d, "다형식품 MTD 보고서", "2026-05-01 ~ 2026-05-15")
    texts = [p.text for p in d.paragraphs]
    assert "다형식품 MTD 보고서" in texts
    assert any("2026-05-01" in t for t in texts)


def test_heading_banner_shading_and_accent_bar():
    d = _doc()
    p = sec.add_heading(d, "목표 달성 현황")
    ppr = p.paragraph_format.element.get_or_add_pPr()
    shd = ppr.find(qn("w:shd"))
    assert shd.get(qn("w:fill")) == theme.FILL_BANNER
    left = ppr.find(qn("w:pBdr")).find(qn("w:left"))
    assert left.get(qn("w:color")) == theme.ACCENT
    assert p.paragraph_format.keep_with_next is True


def test_footer_brand_and_page_field():
    d = _doc()
    sec.add_footer(d)
    footer = d.sections[0].footer
    assert "Engineered by Laighthouse AI" in footer.paragraphs[0].text
    assert footer.paragraphs[0]._p.find(qn("w:fldSimple")) is not None


def test_kpi_cards_layout_colors():
    d = _doc()
    sec.add_kpi_cards(d, [
        {"label": "월 예산 목표", "value": "127,636,364"},
        {"label": "기간 누적 ROAS", "value": "559.62%", "accent": "#7c3aed",
         "diff": "목표 425.43%"},
        {"label": "증감", "value": "1", "diff": "▲ +2%", "diff_value": 2},
    ])
    table = d.tables[0]
    assert len(table.columns) == 5  # 3 cards + 2 spacers
    card0 = table.rows[0].cells[0]
    assert card0.paragraphs[0].text == "월 예산 목표"
    assert card0._tc.find(qn("w:tcPr")).find(qn("w:shd")) is not None
    accent_run = table.rows[0].cells[2].paragraphs[1].runs[0]
    assert str(accent_run.font.color.rgb) == "7C3AED"
    diff_run = table.rows[0].cells[4].paragraphs[2].runs[0]
    assert str(diff_run.font.color.rgb) == theme.GREEN


def test_table_header_band_repeat_and_no_vertical_borders():
    d = _doc()
    table = sec.add_data_table(d, "캠페인별 성과", ["캠페인", "ROAS"],
                               [["브랜드검색", "727%"], ["합계", "573%"]])
    header_row = table.rows[0]
    assert header_row._tr.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None
    shd = header_row.cells[0]._tc.find(qn("w:tcPr")).find(qn("w:shd"))
    assert shd.get(qn("w:fill")) == theme.FILL_HEADER
    borders = table._tbl.tblPr.find(qn("w:tblBorders"))
    assert borders.find(qn("w:insideV")).get(qn("w:val")) == "nil"
    total_run = table.rows[2].cells[0].paragraphs[0].runs[0]
    assert total_run.font.bold is True


def test_table_prettifies_raw_floats():
    d = _doc()
    table = sec.add_data_table(d, None, ["매체", "소진율"],
                               [["브랜드검색", "55.88918788518661%"]])
    assert table.rows[1].cells[1].paragraphs[0].text == "55.89%"


def test_column_widths_proportional_with_header_floor():
    headers = ["광고그룹", "노출", "광고비"]
    rows = [["012_브랜드_공통_분유_견과류음료_견과류천국", "1,204,331", "808"]]
    widths = sec._column_widths(headers, rows)
    assert widths[0] > widths[1] > 0
    assert abs(sum(int(w) for w in widths) - int(theme.CONTENT_W)) <= 3


def test_zero_gross_filter_on_large_tables():
    headers = ["키워드", "노출", "매출"]
    rows = [[f"kw{i}", "1", "0" if i % 2 else "1,000"] for i in range(30)]
    rows.append(["합계", "30", "15,000"])
    kept, removed = sec.filter_zero_gross(headers, rows)
    assert removed == 15
    assert all(not sec._is_zero_amount(r[2]) or sec._is_total_row(r) for r in kept)
    assert sec._is_total_row(kept[-1])  # 합계 row survives even if checked


def test_zero_gross_filter_skips_small_tables():
    headers = ["지표", "매출"]
    rows = [["a", "0"], ["b", "100"]]
    kept, removed = sec.filter_zero_gross(headers, rows)
    assert removed == 0 and len(kept) == 2


def test_zero_gross_filter_needs_gross_column():
    headers = ["키워드", "노출"]
    rows = [[f"kw{i}", "0"] for i in range(30)]
    kept, removed = sec.filter_zero_gross(headers, rows)
    assert removed == 0 and len(kept) == 30


def test_large_table_notes_mention_filter_and_truncation():
    d = _doc()
    rows = [[f"kw{i}", "0" if i % 2 else "1,000"] for i in range(150)]
    sec.add_data_table(d, "키워드별 성과", ["키워드", "매출"], rows)
    notes = [p.text for p in d.paragraphs if "제외" in p.text or "생략" in p.text]
    assert notes and "매출 0원 75행 제외" in notes[0]
    assert "생략" in notes[0]  # 75 kept > MAX_TABLE_ROWS(50) → also truncated


def test_text_section_subheadings_bold():
    d = _doc()
    sec.add_text_section(d, "카테고리별 성과 분석",
                         "국내분유\n누적 매출 1위이며 성장했습니다.")
    runs = [r for p in d.paragraphs for r in p.runs]
    subhead = next(r for r in runs if r.text == "국내분유")
    assert subhead.font.bold is True
    body = next(r for r in runs if "누적 매출" in r.text)
    assert not body.font.bold
