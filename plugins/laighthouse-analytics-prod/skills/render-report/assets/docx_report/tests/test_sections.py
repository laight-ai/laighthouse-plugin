import time

from docx import Document

import sections as sec


def test_add_kpi_cards_renders_label_and_value(tmp_path):
    document = Document()
    sec.add_kpi_cards(document, [
        {"label": "월 예산대비 소진율", "value": "62.3%", "diff": "-7.1%p", "diff_value": -7.1},
        {"label": "월 목표 매출 대비 달성률", "value": "96.6%", "diff": "+3.3%p", "diff_value": 3.3},
    ])

    out_path = tmp_path / "kpi.docx"
    document.save(out_path)

    reopened = Document(out_path)
    table = reopened.tables[0]
    assert table.cell(0, 0).text == "월 예산대비 소진율"
    assert "62.3%" in table.cell(1, 0).text
    assert "-7.1%p" in table.cell(1, 0).text


def test_add_data_table_renders_headers_and_rows(tmp_path):
    document = Document()
    sec.add_data_table(
        document,
        heading="캠페인별 성과",
        headers=["캠페인", "매출", "ROAS"],
        rows=[["05_GT케이(SPBR)_MO", "1,320,543", "1017%"]],
    )

    out_path = tmp_path / "table.docx"
    document.save(out_path)

    reopened = Document(out_path)
    table = reopened.tables[0]
    assert table.cell(0, 0).text == "캠페인"
    assert table.cell(1, 0).text == "05_GT케이(SPBR)_MO"
    assert table.cell(1, 2).text == "1017%"


def test_add_data_table_stays_fast_for_large_tables(tmp_path):
    # Regression guard: table.cell(r, c) rescans the whole table on every
    # call, making it O(n^2) for large tables (e.g. keyword performance with
    # 1000+ rows took effectively forever). row.cells access must stay row-
    # scoped for this to remain linear.
    headers = ["키워드", "노출", "클릭", "광고비", "CPC", "클릭율", "CPM", "구매건수", "매출", "ROAS"]
    rows = [[f"keyword-{i}", i, i, i, i, i, i, i, i, i] for i in range(1500)]

    document = Document()
    started = time.monotonic()
    sec.add_data_table(document, heading="키워드별 성과", headers=headers, rows=rows)
    elapsed = time.monotonic() - started

    assert elapsed < 5, f"add_data_table took {elapsed:.1f}s for 1500 rows, expected a few seconds"
    table = document.tables[0]
    assert table.rows[1].cells[0].text == "keyword-0"
    assert table.rows[1500].cells[0].text == "keyword-1499"


def test_add_text_section_renders_heading_and_body(tmp_path):
    document = Document()
    sec.add_text_section(document, "Executive Summary", "ROAS가 목표 대비 118% 달성되었습니다.")

    out_path = tmp_path / "text.docx"
    document.save(out_path)

    reopened = Document(out_path)
    full_text = "\n".join(p.text for p in reopened.paragraphs)
    assert "Executive Summary" in full_text
    assert "ROAS가 목표 대비 118% 달성되었습니다." in full_text
