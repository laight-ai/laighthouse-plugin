from docx import Document
from lxml import etree

import charts
import sections as sec
import theme

_C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

_BARS = [
    {"name": "광고비", "values": [1, 2, 3], "color": "94A3B8"},
    {"name": "전환매출", "values": [4, 5, 6], "color": "93C5FD"},
]
_LINE = {"name": "ROAS(%)", "values": [7, 8, 9], "color": "EF4444"}


def _chart_root():
    d = Document()
    sec.setup_document(d)
    charts.add_combo_chart(d, ["1월", "2월", "3월"], _BARS, _LINE)
    part = next(p for p in d.part.package.iter_parts()
                if "charts/chart" in str(p.partname))
    return d, etree.fromstring(part.blob)


def test_chart_part_created_and_referenced():
    d, root = _chart_root()
    assert root.tag == f"{_C}chartSpace"
    drawings = d.element.body.findall(
        ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr")
    assert len(drawings) == 1


def test_series_child_order_is_schema_valid():
    _, root = _chart_root()
    for ser in root.iter(f"{_C}ser"):
        tags = [etree.QName(ch).localname for ch in ser]
        assert tags.index("tx") < tags.index("spPr")
        assert tags.index("spPr") < tags.index("cat") < tags.index("val")


def test_series_colors_and_axis_numfmt():
    _, root = _chart_root()
    bar_chart = root.find(f".//{_C}barChart")
    fills = [el.get("val") for el in bar_chart.iter(f"{_A}srgbClr")]
    assert "94A3B8" in fills and "93C5FD" in fills
    left_ax = root.findall(f".//{_C}valAx")[0]
    assert left_ax.find(f"{_C}numFmt").get("formatCode") == "#,##0"
    assert left_ax.find(f"{_C}majorGridlines") is not None
    def_rpr = left_ax.find(f"{_C}txPr").find(f".//{_A}defRPr")
    assert def_rpr.find(f"{_A}latin").get("typeface") == theme.FONT


def test_legend_bottom_and_distinct_partnames():
    d = Document()
    charts.add_combo_chart(d, ["a"], [{"name": "b", "values": [1]}],
                           {"name": "l", "values": [2]})
    charts.add_combo_chart(d, ["a"], [{"name": "b", "values": [1]}],
                           {"name": "l", "values": [2]})
    names = sorted(str(p.partname) for p in d.part.package.iter_parts()
                   if "charts/chart" in str(p.partname))
    assert names == ["/word/charts/chart1.xml", "/word/charts/chart2.xml"]
    root = etree.fromstring(
        next(p for p in d.part.package.iter_parts()
             if str(p.partname).endswith("chart1.xml")).blob)
    assert root.find(f".//{_C}legend/{_C}legendPos").get("val") == "b"
