import json
import subprocess
import sys
from pathlib import Path

import pytest

import build
import map_report


def _target_progress_raw():
    return {
        "target_cost": 100, "target_revenue": 200, "target_roas": 4.0,
        "actual_cost": 50, "actual_revenue": 120, "actual_roas": 4.8,
        "cost_progress_ratio": 0.5, "revenue_progress_ratio": 0.6,
    }


def test_assemble_mtd_orders_sections_and_slots():
    keyword_item = {"keyword": "k", "impressions": 1, "clicks": 1, "ad_cost": 1,
                    "cpc": 1, "ctr": 1.0, "cpm": 1, "purchases": 1,
                    "revenue": 1, "roas": 100.0}
    groups = {
        "A": _target_progress_raw(),
        "G": {"items": [keyword_item], "items_total": 999},
        # B, C, D, E, F intentionally missing
    }
    sections, digests = map_report.assemble("mtd", groups)

    slot_keys = [s["key"] for s in sections if s.get("type") == "analysis_slot"]
    assert slot_keys == ["section3", "section5", "section8"]
    # group A yields two sections (kpi cards + achievement) before section3 slot
    assert sections[0]["type"] == "kpi_cards"
    assert sections[2] == {"type": "analysis_slot", "key": "section3",
                           "heading": "Executive Summary"}
    # missing groups degrade to 데이터 준비 중 text sections, not errors
    assert sum(1 for s in sections
               if s.get("type") == "text" and s.get("body") == "데이터 준비 중") == 5
    # keyword table survives with rows_total from items_total
    keyword_table = next(s for s in sections if s.get("heading") == "키워드별 성과")
    assert keyword_table["rows_total"] == 999
    assert "A" in digests and digests["G"] is None


def test_assemble_broken_group_degrades_not_raises():
    sections, digests = map_report.assemble("mtd", {"A": {"garbage": True}})
    assert sections[0] == {"type": "text", "heading": "데이터 준비 중",
                           "body": "데이터 준비 중"}
    assert digests["A"] is None


def test_assemble_daily_requires_branch_mapper():
    with pytest.raises(ValueError):
        map_report.assemble("daily", {}, branch=None)  # (daily, A_None) unregistered


def test_build_fills_analysis_slots_and_defaults():
    data = {"title": "t", "sections": [
        {"type": "analysis_slot", "key": "section3", "heading": "Executive Summary"},
        {"type": "analysis_slot", "key": "section5", "heading": "제품 분석"},
    ]}
    analysis = {"section3": {"heading": "Executive Summary", "body": "요약 본문."}}
    prs = build.build_presentation(data, analysis)
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                texts.extend(p.text for p in shape.text_frame.paragraphs)
    assert "요약 본문." in texts          # filled slot
    assert "데이터 준비 중" in texts       # unfilled slot degrades


def test_cli_end_to_end(tmp_path):
    combined = tmp_path / "combined.json"
    combined.write_text(json.dumps({"A": _target_progress_raw()}), encoding="utf-8")
    out = tmp_path / "sections.json"
    digests = tmp_path / "digests.json"
    subprocess.run(
        [sys.executable, str(Path(map_report.__file__)),
         "--report-type", "mtd", "--data", str(combined),
         "--out", str(out), "--digests", str(digests),
         "--title", "다형식품 MTD 보고서", "--period", "2026-05-01 ~ 2026-05-15"],
        check=True,
    )
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["title"] == "다형식품 MTD 보고서"
    assert any(s.get("type") == "analysis_slot" for s in doc["sections"])
    assert "A" in json.loads(digests.read_text(encoding="utf-8"))

    analysis = tmp_path / "analysis.json"
    analysis.write_text(json.dumps(
        {"section3": {"heading": "Executive Summary", "body": "요약."}},
        ensure_ascii=False), encoding="utf-8")
    pptx_out = tmp_path / "report.pptx"
    subprocess.run(
        [sys.executable, str(Path(build.__file__)),
         "--data", str(out), "--analysis", str(analysis), "--out", str(pptx_out)],
        check=True,
    )
    assert pptx_out.exists()
