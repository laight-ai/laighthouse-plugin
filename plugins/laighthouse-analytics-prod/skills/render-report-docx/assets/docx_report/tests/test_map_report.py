import json
import subprocess
import sys
from pathlib import Path

import build
import map_report


def _target_progress_raw():
    return {
        "target_cost": 100, "target_revenue": 200, "target_roas": 4.0,
        "actual_cost": 50, "actual_revenue": 120, "actual_roas": 4.8,
        "cost_progress_ratio": 0.5, "revenue_progress_ratio": 0.6,
    }


def test_assemble_mtd_slots_and_degradation():
    sections, digests = map_report.assemble("mtd", {"A": _target_progress_raw()})
    slot_keys = [s["key"] for s in sections if s.get("type") == "analysis_slot"]
    assert slot_keys == ["section3", "section5", "section8"]
    assert sections[0]["type"] == "kpi_cards"
    assert sum(1 for s in sections
               if s.get("type") == "text" and s.get("body") == "데이터 준비 중") == 6
    assert digests["A"] is not None


def test_map_report_cli_feeds_docx_build(tmp_path):
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
    doc_data = json.loads(out.read_text(encoding="utf-8"))
    document = build.build_document(
        doc_data, {"section3": {"heading": "Executive Summary", "body": "요약."}})
    texts = [p.text for p in document.paragraphs]
    assert "다형식품 MTD 보고서" in texts and "요약." in texts
