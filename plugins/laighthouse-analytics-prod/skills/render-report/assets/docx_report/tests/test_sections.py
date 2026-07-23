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


def test_add_text_section_renders_heading_and_body(tmp_path):
    document = Document()
    sec.add_text_section(document, "Executive Summary", "ROAS가 목표 대비 118% 달성되었습니다.")

    out_path = tmp_path / "text.docx"
    document.save(out_path)

    reopened = Document(out_path)
    full_text = "\n".join(p.text for p in reopened.paragraphs)
    assert "Executive Summary" in full_text
    assert "ROAS가 목표 대비 118% 달성되었습니다." in full_text
