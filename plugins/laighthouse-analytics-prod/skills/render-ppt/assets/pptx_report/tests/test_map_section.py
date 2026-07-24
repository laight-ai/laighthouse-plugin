import json
import sys

import map_section


def test_main_writes_sections_and_digest_json(tmp_path):
    data_path = tmp_path / "raw.json"
    data_path.write_text(
        json.dumps({"items": [{"group": "g1", "impressions": 1, "clicks": 1, "cpc": 1, "ad_cost": 1, "revenue": 1}]}),
        encoding="utf-8",
    )
    out_path = tmp_path / "out.json"

    old_argv = sys.argv
    sys.argv = [
        "map_section.py",
        "--report-type", "mtd",
        "--group", "F",
        "--data", str(data_path),
        "--out", str(out_path),
    ]
    try:
        map_section.main()
    finally:
        sys.argv = old_argv

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["digest"] is None
    assert result["sections"][0]["heading"] == "광고그룹별 성과"


def test_main_rejects_unknown_group(tmp_path):
    data_path = tmp_path / "raw.json"
    data_path.write_text("{}", encoding="utf-8")
    out_path = tmp_path / "out.json"

    old_argv = sys.argv
    sys.argv = [
        "map_section.py",
        "--report-type", "mtd",
        "--group", "Z",
        "--data", str(data_path),
        "--out", str(out_path),
    ]
    try:
        try:
            map_section.main()
            assert False, "expected ValueError"
        except ValueError:
            pass
    finally:
        sys.argv = old_argv
