# render-report DOCX Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the HTML/Chart.js output of the `render-report` skill with a native Word `.docx` output (tables, native OOXML charts), while preserving the current HTML version on a backup git branch.

**Architecture:** A standalone Python package `docx_report` (python-docx for document structure + a hand-built OOXML module for native Word combo charts) lives under `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/`. It's invoked once per report via a CLI (`build.py`) that reads a JSON section list and produces one `.docx` file. The skill's `sections/*.md` files stop describing HTML/JS and instead describe which JSON section object(s) to emit per MCP field, using a shared schema (below).

**Tech Stack:** Python 3.12, `python-docx`, `pytest`, `lxml` (transitive dependency of python-docx, used directly for the chart XML injection).

## Global Constraints

- MCP response data must never be recalculated, re-aggregated, filtered, or "corrected" by the generator — it renders exactly what the section JSON says, verbatim (spec §3, carrying forward the existing render-report absolute rule).
- No throwaway scripts beyond the one reusable `assets/docx_report/` package — this package is the single documented exception to "no separate scripts" (spec §3).
- Charts must be real Word-native chart objects (`c:barChart`/`c:lineChart` combo), not images (spec §3, user requirement).
- All four report types (`daily`/`mtd`/`monthly`/`executive-mtd`) are the final target; `mtd` is built and verified first (spec §5).
- The current HTML skill must be fully preserved on a `backup/render-report-html` branch before any destructive edits to `SKILL.md` or `sections/` (spec §1).
- Final output is one `.docx` file at `~/Downloads/laighthouse-reports/{brand_name}_{report_type}_{기준_일자}.docx`; no Artifact/browser publishing step (spec §2).

## Section JSON Schema (shared reference for Tasks 5–8)

Every report's data file is a single JSON object:

```json
{
  "title": "다형식품 MTD 보고서",
  "period": "2026-05-01 ~ 2026-05-15",
  "sections": [ /* array of section objects, in render order */ ]
}
```

Each section object has a `"type"` field, one of:

| type | required fields | renderer |
|---|---|---|
| `heading` | `text` | `sections.add_heading` |
| `kpi_cards` | `cards`: list of `{label, value, diff?, diff_value?}` | `sections.add_kpi_cards` |
| `table` | `heading?`, `headers`: list of str, `rows`: list of list of str | `sections.add_data_table` |
| `chart` | `heading?`, `categories`: list of str, `bar_series`: list of `{name, values}`, `line_series`: `{name, values}` | `sections.add_combo_chart_section` |
| `text` | `heading?`, `body`: str | `sections.add_text_section` |

`diff_value` (numeric) drives red/green/gray coloring; `diff` is the pre-formatted display string (e.g. `"-7.1%p"`). All numeric formatting (`toLocaleString()`-style comma separators, `%`/`₩`/`$` suffixes) must already be done by the LLM before it writes the JSON — the generator only places strings, matching the "MCP 데이터 그대로 렌더링" rule.

---

### Task 1: Git branch setup

**Files:** none (git operations only)

- [ ] **Step 1: Confirm working tree is clean**

Run: `git -C "C:\Users\cliff\git\laighthouse-plugin" status --porcelain`
Expected: empty output (no uncommitted changes). If not empty, stop and report — do not proceed until the tree is clean.

- [ ] **Step 2: Create the backup branch from current main**

Run: `git -C "C:\Users\cliff\git\laighthouse-plugin" branch backup/render-report-html main`
Expected: no output (branch created silently). Verify with `git -C "C:\Users\cliff\git\laighthouse-plugin" branch --list backup/render-report-html` → shows the branch.

- [ ] **Step 3: Create and switch to the feature branch**

Run: `git -C "C:\Users\cliff\git\laighthouse-plugin" checkout -b feature/render-report-docx`
Expected: `Switched to a new branch 'feature/render-report-docx'`

All subsequent tasks happen on `feature/render-report-docx`. Do not push either branch — that's a separate, explicit user decision.

---

### Task 2: Native OOXML combo chart module

**Files:**
- Create: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/__init__.py` (empty file)
- Create: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/requirements.txt`
- Create: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/charts.py`
- Test: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/conftest.py`
- Test: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_charts.py`

**Interfaces:**
- Produces: `charts.add_combo_chart(document, categories, bar_series, line_series, title=None, width_emu=5486400, height_emu=3200400) -> str` where `document` is a `docx.Document`, `bar_series` is `list[{"name": str, "values": list[float]}]`, `line_series` is `{"name": str, "values": list[float]}`. Returns the relationship id of the inserted chart. Appends a paragraph containing the chart to the end of the document body.

- [ ] **Step 1: Set up the package directory and dependencies**

```
plugins\laighthouse-analytics-prod\skills\render-report\assets\docx_report\__init__.py
```
(empty file — just makes the directory importable as a package for tooling that expects it, even though `build.py` is invoked as a plain script, not `-m`)

`requirements.txt`:
```
python-docx>=1.1.0
```

Install it: `pip install -r "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/requirements.txt"`
Expected: `Successfully installed python-docx-...`

- [ ] **Step 2: Write the failing tests**

`tests/conftest.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

`tests/test_charts.py`:
```python
import zipfile

from docx import Document

import charts


def test_add_combo_chart_creates_chart_part_and_reference(tmp_path):
    document = Document()
    document.add_paragraph("placeholder")

    rId = charts.add_combo_chart(
        document,
        categories=["1월", "2월", "3월"],
        bar_series=[
            {"name": "광고비", "values": [100, 200, 150]},
            {"name": "매출", "values": [300, 400, 350]},
        ],
        line_series={"name": "ROAS", "values": [300, 200, 233]},
        title="월별 광고 성과",
    )

    out_path = tmp_path / "chart_test.docx"
    document.save(out_path)

    with zipfile.ZipFile(out_path) as z:
        names = z.namelist()
        assert "word/charts/chart1.xml" in names
        chart_xml = z.read("word/charts/chart1.xml").decode("utf-8")
        document_xml = z.read("word/document.xml").decode("utf-8")

    assert "광고비" in chart_xml
    assert "ROAS" in chart_xml
    assert "1월" in chart_xml
    assert "barChart" in chart_xml
    assert "lineChart" in chart_xml
    assert rId in document_xml
    assert "drawingml/2006/chart" in document_xml


def test_add_combo_chart_supports_multiple_charts_in_one_document(tmp_path):
    document = Document()

    charts.add_combo_chart(
        document,
        categories=["1월", "2월"],
        bar_series=[{"name": "광고비", "values": [10, 20]}],
        line_series={"name": "ROAS", "values": [100, 110]},
    )
    charts.add_combo_chart(
        document,
        categories=["3월", "4월"],
        bar_series=[{"name": "광고비", "values": [30, 40]}],
        line_series={"name": "ROAS", "values": [120, 130]},
    )

    out_path = tmp_path / "two_charts.docx"
    document.save(out_path)

    with zipfile.ZipFile(out_path) as z:
        names = z.namelist()
        assert "word/charts/chart1.xml" in names
        assert "word/charts/chart2.xml" in names
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_charts.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'charts'`

- [ ] **Step 4: Implement `charts.py`**

```python
"""Native OOXML chart injection for python-docx Document objects.

python-docx has no chart support built in. This module builds a chart XML
part by hand, registers it in the docx package's relationship graph, and
inserts the referencing drawing paragraph directly via lxml/python-docx's
oxml layer.
"""
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import parse_xml

CHART_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"
CHART_RELATIONSHIP_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
)

_CHART_NS = (
    'xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
)

_CAT_AX = 111111111
_BAR_VAL_AX = 222222222
_LINE_VAL_AX = 333333333


def add_combo_chart(document, categories, bar_series, line_series, title=None,
                     width_emu=5486400, height_emu=3200400):
    package = document.part.package
    partname = _next_chart_partname(package)
    xml = _build_chart_xml(categories, bar_series, line_series, title)
    chart_part = Part(partname, CHART_CONTENT_TYPE, xml.encode("utf-8"), package)
    rId = document.part.relate_to(chart_part, CHART_RELATIONSHIP_TYPE)
    _append_chart_paragraph(document, rId, width_emu, height_emu)
    return rId


def _next_chart_partname(package):
    existing = [p for p in package.iter_parts() if "/word/charts/chart" in str(p.partname)]
    return PackURI(f"/word/charts/chart{len(existing) + 1}.xml")


def _append_chart_paragraph(document, rId, width_emu, height_emu):
    doc_pr_id = _next_doc_pr_id(document)
    xml = f'''<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
        xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
        xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:r><w:drawing>
    <wp:inline distT="0" distB="0" distL="0" distR="0">
      <wp:extent cx="{width_emu}" cy="{height_emu}"/>
      <wp:docPr id="{doc_pr_id}" name="Chart {doc_pr_id}"/>
      <a:graphic>
        <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
          <c:chart r:id="{rId}"/>
        </a:graphicData>
      </a:graphic>
    </wp:inline>
  </w:drawing></w:r>
</w:p>'''.encode("utf-8")
    document.element.body.append(parse_xml(xml))


def _next_doc_pr_id(document):
    ns = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"
    return len(document.element.body.findall(f".//{ns}")) + 1


def _str_cache(values):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{v}</c:v></c:pt>' for i, v in enumerate(values))
    return f'<c:strCache><c:ptCount val="{len(values)}"/>{pts}</c:strCache>'


def _num_cache(values):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{v}</c:v></c:pt>' for i, v in enumerate(values))
    return (
        '<c:numCache><c:formatCode>General</c:formatCode>'
        f'<c:ptCount val="{len(values)}"/>{pts}</c:numCache>'
    )


def _col_letter(idx):
    return chr(66 + idx)  # B, C, D, ... (column A is reserved for categories)


def _bar_series_xml(idx, name, categories, values):
    col = _col_letter(idx)
    return f'''
    <c:ser>
      <c:idx val="{idx}"/>
      <c:order val="{idx}"/>
      <c:tx><c:strRef><c:f>Sheet1!${col}$1</c:f>{_str_cache([name])}</c:strRef></c:tx>
      <c:cat><c:strRef><c:f>Sheet1!$A$2:$A${len(categories) + 1}</c:f>{_str_cache(categories)}</c:strRef></c:cat>
      <c:val><c:numRef><c:f>Sheet1!${col}$2:${col}${len(values) + 1}</c:f>{_num_cache(values)}</c:numRef></c:val>
    </c:ser>'''


def _line_series_xml(idx, name, categories, values):
    col = _col_letter(idx)
    return f'''
    <c:ser>
      <c:idx val="{idx}"/>
      <c:order val="{idx}"/>
      <c:tx><c:strRef><c:f>Sheet1!${col}$1</c:f>{_str_cache([name])}</c:strRef></c:tx>
      <c:marker><c:symbol val="circle"/></c:marker>
      <c:cat><c:strRef><c:f>Sheet1!$A$2:$A${len(categories) + 1}</c:f>{_str_cache(categories)}</c:strRef></c:cat>
      <c:val><c:numRef><c:f>Sheet1!${col}$2:${col}${len(values) + 1}</c:f>{_num_cache(values)}</c:numRef></c:val>
    </c:ser>'''


def _build_chart_xml(categories, bar_series, line_series, title):
    bar_xml = "".join(
        _bar_series_xml(i, s["name"], categories, s["values"])
        for i, s in enumerate(bar_series)
    )
    line_idx = len(bar_series)
    line_xml = _line_series_xml(line_idx, line_series["name"], categories, line_series["values"])
    title_xml = ""
    if title:
        title_xml = (
            "<c:title><c:tx><c:rich><a:bodyPr/><a:p><a:r><a:t>"
            f"{title}</a:t></a:r></a:p></c:rich></c:tx><c:overlay val=\"0\"/></c:title>"
        )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace {_CHART_NS}>
  <c:chart>
    {title_xml}
    <c:plotArea>
      <c:layout/>
      <c:barChart>
        <c:barDir val="col"/>
        <c:grouping val="clustered"/>
        {bar_xml}
        <c:axId val="{_CAT_AX}"/>
        <c:axId val="{_BAR_VAL_AX}"/>
      </c:barChart>
      <c:lineChart>
        <c:grouping val="standard"/>
        {line_xml}
        <c:axId val="{_CAT_AX}"/>
        <c:axId val="{_LINE_VAL_AX}"/>
      </c:lineChart>
      <c:catAx>
        <c:axId val="{_CAT_AX}"/>
        <c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:delete val="0"/>
        <c:axPos val="b"/>
        <c:crossAx val="{_BAR_VAL_AX}"/>
      </c:catAx>
      <c:valAx>
        <c:axId val="{_BAR_VAL_AX}"/>
        <c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:delete val="0"/>
        <c:axPos val="l"/>
        <c:crossAx val="{_CAT_AX}"/>
      </c:valAx>
      <c:valAx>
        <c:axId val="{_LINE_VAL_AX}"/>
        <c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:delete val="0"/>
        <c:axPos val="r"/>
        <c:crossAx val="{_CAT_AX}"/>
        <c:crosses val="max"/>
      </c:valAx>
    </c:plotArea>
    <c:legend><c:legendPos val="b"/></c:legend>
    <c:plotVisOnly val="1"/>
  </c:chart>
</c:chartSpace>'''
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_charts.py" -v`
Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/__init__.py \
        plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/requirements.txt \
        plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/charts.py \
        plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/conftest.py \
        plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_charts.py
git commit -m "feat: add native OOXML combo chart module for docx reports"
```

---

### Task 3: Section renderers (`sections.py`)

**Files:**
- Create: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/sections.py`
- Test: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_sections.py`

**Interfaces:**
- Consumes: `charts.add_combo_chart(document, categories, bar_series, line_series, title=None)` from Task 2.
- Produces:
  - `sections.add_title(document, title, period=None)`
  - `sections.add_heading(document, text)`
  - `sections.add_kpi_cards(document, cards)` where `cards` is `list[{"label": str, "value": str, "diff": str|None, "diff_value": float|None}]`
  - `sections.add_data_table(document, heading, headers, rows)` where `heading` may be `None`, `headers` is `list[str]`, `rows` is `list[list[str]]`
  - `sections.add_text_section(document, heading, body)` where `heading` may be `None`
  - `sections.add_combo_chart_section(document, heading, categories, bar_series, line_series)` where `heading` may be `None`

- [ ] **Step 1: Write the failing tests**

`tests/test_sections.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_sections.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sections'`

- [ ] **Step 3: Implement `sections.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_sections.py" -v`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/sections.py \
        plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_sections.py
git commit -m "feat: add docx section renderers (kpi cards, tables, text, chart wrapper)"
```

---

### Task 4: Build CLI (`build.py`)

**Files:**
- Create: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/build.py`
- Test: `plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_build.py`

**Interfaces:**
- Consumes: all `sections.add_*` functions from Task 3.
- Produces: `build.build_document(data: dict) -> docx.Document` and `build.main()` (CLI entrypoint reading `--data <json path>` / `--out <docx path>`).

- [ ] **Step 1: Write the failing tests**

`tests/test_build.py`:
```python
import json
import sys

from docx import Document

import build


SAMPLE_DATA = {
    "title": "다형식품 MTD 보고서",
    "period": "2026-05-01 ~ 2026-05-15",
    "sections": [
        {"type": "heading", "text": "목표 달성 현황"},
        {
            "type": "kpi_cards",
            "cards": [
                {"label": "월 예산대비 소진율", "value": "62.3%", "diff": "-7.1%p", "diff_value": -7.1},
                {"label": "월 누적 ROAS", "value": "506%", "diff": "+42%p", "diff_value": 42},
            ],
        },
        {
            "type": "chart",
            "heading": "월별 광고 성과",
            "categories": ["25년 11월", "25년 12월", "26년 1월"],
            "bar_series": [
                {"name": "광고비", "values": [1000000, 1100000, 1200000]},
                {"name": "매출", "values": [5000000, 5200000, 5400000]},
            ],
            "line_series": {"name": "ROAS", "values": [500, 473, 450]},
        },
        {
            "type": "table",
            "heading": "캠페인별 성과",
            "headers": ["캠페인", "매출", "ROAS"],
            "rows": [["05_GT케이(SPBR)_MO", "1,320,543", "1017%"]],
        },
        {
            "type": "text",
            "heading": "Executive Summary",
            "body": "ROAS가 목표 대비 118% 달성되었습니다.",
        },
    ],
}


def test_build_document_creates_all_section_types():
    document = build.build_document(SAMPLE_DATA)
    assert len(document.tables) == 2  # kpi_cards + table
    full_text = "\n".join(p.text for p in document.paragraphs)
    assert "다형식품 MTD 보고서" in full_text
    assert "Executive Summary" in full_text


def test_build_document_rejects_unknown_section_type():
    bad_data = {"title": "t", "sections": [{"type": "nope"}]}
    try:
        build.build_document(bad_data)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "nope" in str(e)


def test_main_writes_docx_file(tmp_path):
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(SAMPLE_DATA, ensure_ascii=False), encoding="utf-8")
    out_path = tmp_path / "out.docx"

    old_argv = sys.argv
    sys.argv = ["build.py", "--data", str(data_path), "--out", str(out_path)]
    try:
        build.main()
    finally:
        sys.argv = old_argv

    assert out_path.exists()
    reopened = Document(out_path)
    assert len(reopened.tables) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_build.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 3: Implement `build.py`**

```python
"""CLI entrypoint: JSON section list -> .docx file.

Invoked directly as a script (not via -m), so it adds its own directory to
sys.path to resolve the sibling `sections`/`charts` modules regardless of
the caller's working directory.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx import Document  # noqa: E402

import sections as sec  # noqa: E402

_RENDERERS = {
    "heading": lambda doc, s: sec.add_heading(doc, s["text"]),
    "kpi_cards": lambda doc, s: sec.add_kpi_cards(doc, s["cards"]),
    "table": lambda doc, s: sec.add_data_table(doc, s.get("heading"), s["headers"], s["rows"]),
    "chart": lambda doc, s: sec.add_combo_chart_section(
        doc, s.get("heading"), s["categories"], s["bar_series"], s["line_series"]
    ),
    "text": lambda doc, s: sec.add_text_section(doc, s.get("heading"), s["body"]),
}


def build_document(data):
    document = Document()
    sec.add_title(document, data["title"], data.get("period"))
    for section in data["sections"]:
        stype = section["type"]
        renderer = _RENDERERS.get(stype)
        if renderer is None:
            raise ValueError(f"unknown section type: {stype}")
        renderer(document, section)
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="path to the section-list JSON file")
    parser.add_argument("--out", required=True, help="path to write the .docx file to")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    document = build_document(data)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(out_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_build.py" -v`
Expected: `3 passed`

- [ ] **Step 5: Run the full test suite for the package**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/" -v`
Expected: `8 passed`

- [ ] **Step 6: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/build.py \
        plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/test_build.py
git commit -m "feat: add build.py CLI entrypoint for docx report generation"
```

---

### Task 5: Convert `mtd` section files + SKILL.md

**Files:**
- Modify: `plugins/laighthouse-analytics-prod/skills/render-report/SKILL.md`
- Modify (all 11): `plugins/laighthouse-analytics-prod/skills/render-report/sections/mtd/mtd-section-1-kpi-goals.md` through `mtd-section-11-keyword-performance.md`

**Conversion rule:** In every section file, delete the `## HTML` and `## Script` blocks (and any pagination/search JS description in `## 렌더링 규칙`) and replace them with a `## DOCX 섹션` block containing one JSON section object (or array, for files that emit more than one section — e.g. mtd-section-1+2 together emit a `kpi_cards` section) following the shared schema above, using the same field names already documented in that file's `## 필요 데이터 (MCP)` block. Keep `## 필요 데이터 (MCP)` and the MCP tool-call docs untouched — only the output markup changes.

Worked example — `mtd-section-9-campaign-performance.md`'s `## HTML`/`## Script`/`## 렌더링 규칙` blocks become:

```markdown
## DOCX 섹션

```json
{
  "type": "table",
  "heading": "캠페인별 성과",
  "headers": ["캠페인", "네이버 광고 채널명", "매출", "광고비", "ROAS", "노출", "클릭", "CTR", "CPC", "구매", "평균단가"],
  "rows": [
    ["{campaign}", "{channel}", "{revenue_fmt}", "{ad_cost_fmt}", "{roas}%", "{impressions_fmt}", "{clicks_fmt}", "{ctr}%", "{cpc_fmt}", "{purchases}", "{avg_price_fmt}"]
  ]
}
```

`rows`에는 `campaign_performance` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로 넣는다
(검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한 표에 다 낸다).

### 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.
```

- [ ] **Step 1: Apply the conversion rule to all 11 `sections/mtd/*.md` files**

Use the worked example above as the pattern. For KPI/card-style files (`mtd-section-1-kpi-goals.md`, `mtd-section-2-achievement.md`) emit a `kpi_cards` section (one card per metric already listed in that file's HTML, using the file's own diff-sign/color rules to compute `diff`/`diff_value` strings). For the chart file (`mtd-section-4-monthly-chart.md`) emit a `chart` section with `bar_series` = `[{"name": "광고비", "values": monthly_chart.ad_cost}, {"name": "매출", "values": monthly_chart.revenue}]` and `line_series` = `{"name": "ROAS", "values": monthly_chart.roas}`. For text-only files (executive summary, product/campaign/group deep-dive prose) emit a `text` section. For remaining table files (`mtd-section-6`, `7`, `10`, `11`) emit `table` sections with `headers`/`rows` matching each file's existing HTML `<th>`/`<td>` mapping.

- [ ] **Step 2: Update `SKILL.md`**

- Replace the "보고서 골격 (Scaffold)" HTML template section with a description of the docx assembly order: build one JSON object with `title`, `period`, and a `sections` array populated by concatenating each imported section file's `## DOCX 섹션` JSON object(s) in the documented order, write it to a temp JSON file, then run:
  `python "<skill_dir>/assets/docx_report/build.py" --data <temp.json> --out "~/Downloads/laighthouse-reports/{brand_name}_{report_type}_{기준_일자}.docx"`
- In "실행 방식 절대 지침", change the "별도 스크립트 생성 금지" wording to explicitly exempt `assets/docx_report/build.py` as the one reusable script this skill invokes.
- In step 7 of "실행 순서", remove the Artifact-publish instruction (docx can't be shown in an Artifact) — the only output is the saved `.docx` file.
- Remove the Chart.js CDN/inline-script warning (`assets/chart.umd.min.js` is no longer used).
- Update the 완료 메시지 형식 example to reference the `.docx` path instead of `.html`.

- [ ] **Step 3: Verify by hand-building a sample mtd docx**

Take the JSON section list the converted files describe (using placeholder numbers, not live MCP calls) and run:
`python "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/build.py" --data sample_mtd.json --out sample_mtd.docx`
Expected: exits 0, `sample_mtd.docx` exists. Confirm it opens: `python -c "from docx import Document; Document('sample_mtd.docx'); print('ok')"` → prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/SKILL.md \
        plugins/laighthouse-analytics-prod/skills/render-report/sections/mtd/
git commit -m "feat: convert mtd report sections and SKILL.md to docx output"
```

---

### Task 6: Convert `daily` section files

**Files:**
- Modify (all 6): `plugins/laighthouse-analytics-prod/skills/render-report/sections/daily/daily-section-1-kpi-goals.md` through `daily-section-6-adgroup-keyword-performance.md`

**Conversion rule:** Same rule as Task 5. Each `daily` file has two branches (Google/Meta 분기 A, naver 분기 B) — convert **both** branches' HTML/Script blocks into their own `## DOCX 섹션 (분기 A)` / `## DOCX 섹션 (분기 B)` JSON blocks using the same field names each branch's `## 필요 데이터` already lists (e.g. daily-section-2's 분기 A → `kpi_cards` from `sales.*` fields; 분기 B → `kpi_cards` from `overview.*` fields, matching the worked mtd-section-1/2 pattern from Task 5).

- [ ] **Step 1: Apply the conversion rule to all 6 `sections/daily/*.md` files**, converting both branches in each file per the rule above.

- [ ] **Step 2: Verify with a sample daily docx** (same method as Task 5 Step 3, using a sample JSON built from one 분기 A file and one 분기 B file to confirm both branches produce valid section JSON).

- [ ] **Step 3: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/sections/daily/
git commit -m "feat: convert daily report sections to docx output"
```

---

### Task 7: Convert `monthly` section files

**Files:**
- Modify (all 8): `plugins/laighthouse-analytics-prod/skills/render-report/sections/Monthly/monthly-section-1-kpi-goals.md` through `monthly-section-8-media-comparison-table.md`

**Conversion rule:** Same rule as Task 5. `monthly-section-6-category-monthly-comparison.md` and `monthly-section-8-media-comparison-table.md` do their own MoM aggregation in prose (per spec §4/§5 — this is LLM-side data prep, unchanged) before emitting a `table` section; only their output markup changes to the JSON schema.

- [ ] **Step 1: Apply the conversion rule to all 8 `sections/Monthly/*.md` files.**

- [ ] **Step 2: Verify with a sample monthly docx** (same method as Task 5 Step 3).

- [ ] **Step 3: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/sections/Monthly/
git commit -m "feat: convert monthly report sections to docx output"
```

---

### Task 8: Convert `executive-mtd` section files

**Files:**
- Modify (all 5): `plugins/laighthouse-analytics-prod/skills/render-report/sections/executive-mtd/executive-mtd-section-1-achievement.md` through `executive-mtd-section-5-media-roas-comparison.md`

**Conversion rule:** Same rule as Task 5.

- [ ] **Step 1: Apply the conversion rule to all 5 `sections/executive-mtd/*.md` files.**

- [ ] **Step 2: Verify with a sample executive-mtd docx** (same method as Task 5 Step 3).

- [ ] **Step 3: Commit**

```bash
git add plugins/laighthouse-analytics-prod/skills/render-report/sections/executive-mtd/
git commit -m "feat: convert executive-mtd report sections to docx output"
```

---

### Task 9: End-to-end verification and user sign-off

**Files:** none (verification only)

- [ ] **Step 1: Run the full docx_report test suite one more time**

Run: `pytest "plugins/laighthouse-analytics-prod/skills/render-report/assets/docx_report/tests/" -v`
Expected: all tests pass.

- [ ] **Step 2: Generate one real mtd report end-to-end**

Using the `render-report` skill's normal MCP-call flow (real brand/date), produce one actual `mtd` `.docx` report and save it to `~/Downloads/laighthouse-reports/`.

- [ ] **Step 3: Ask the user to open and visually confirm the mtd docx**

Do not proceed to claim the daily/monthly/executive-mtd conversions (already done in Tasks 6–8) are final until the user confirms the mtd docx renders correctly in Word — per spec §6, this is the one manual visual checkpoint in the whole plan.

- [ ] **Step 4: Confirm branch state**

Run: `git -C "C:\Users\cliff\git\laighthouse-plugin" branch --list`
Expected: shows `backup/render-report-html`, `feature/render-report-docx` (current), and `main` untouched. Do not merge to `main` until the user explicitly asks for it.
