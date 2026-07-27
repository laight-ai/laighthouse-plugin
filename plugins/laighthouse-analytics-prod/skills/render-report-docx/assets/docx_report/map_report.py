"""CLI: one combined raw-MCP JSON -> fully assembled sections JSON + digests.

Replaces the per-group map_section.py round-trips: the orchestrator saves
every group's raw MCP response into ONE file ({"A": <raw>, "B": <raw>, ...}),
runs this script once, and never re-reads the mapped DATA sections into its
context — only the small digests file. ANALYSIS sections are emitted as
`analysis_slot` placeholders that build.py fills from a separate (small)
analysis JSON written by the LLM.

Usage:
  python map_report.py --report-type mtd --data combined.json \
      --out sections.json --digests digests.json \
      --title "다형식품 MTD 보고서" --period "2026-05-01 ~ 2026-05-15" \
      [--branch google_meta|naver]   # daily only
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from section_mapping import MAPPERS  # noqa: E402

# Document order per report type: ("group", key) inlines that group's mapped
# sections; ("analysis", key, heading) becomes an analysis_slot placeholder
# the LLM fills via build.py --analysis. Orders mirror the per-type section
# tables in SKILL.md.
ORDERS = {
    "creative": [
        ("group", "A"),
        ("group", "B"),
        ("analysis", "section4", "소재 분석 (Executive Summary)"),
    ],
    "mtd": [
        ("group", "A"),
        ("analysis", "section3", "Executive Summary"),
        ("group", "B"),
        ("analysis", "section5", "제품 판매 성과의 심층 분석"),
        ("group", "C"),
        ("group", "D"),
        ("analysis", "section8", "캠페인별 성과 심층 분석"),
        ("group", "E"),
        ("group", "F"),
        ("group", "G"),
    ],
    "daily": [
        ("group", "A"),
        ("analysis", "section3", "성과요약 (Executive Summary)"),
        ("group", "B"),
        ("group", "C"),
        ("group", "D"),
    ],
    "monthly": [
        ("group", "A"),
        ("analysis", "section3", "Executive Summary"),
        ("group", "B"),
        ("analysis", "section5", "제품 판매 트렌드 분석"),
        ("group", "C"),
        ("group", "D"),
    ],
    "executive-mtd": [
        ("group", "A"),
        ("group", "B"),
        ("analysis", "section3", "Executive Summary"),
        ("group", "C"),
        ("group", "D"),
    ],
}

_PLACEHOLDER_BODY = "데이터 준비 중"


def assemble(report_type, groups_raw, branch=None):
    """Return (sections, digests). A group that is missing or whose mapper
    raises becomes a single '데이터 준비 중' text section — other groups
    proceed normally, per SKILL.md's 데이터 부족 시 rule."""
    order = ORDERS.get(report_type)
    if order is None:
        raise ValueError(f"unknown report type: {report_type}")

    sections, digests = [], {}
    for entry in order:
        if entry[0] == "analysis":
            _, key, heading = entry
            sections.append({"type": "analysis_slot", "key": key, "heading": heading})
            continue
        group = entry[1]
        mapper_key = (report_type, f"{group}_{branch}" if report_type == "daily" else group)
        mapper = MAPPERS.get(mapper_key)
        if mapper is None:
            raise ValueError(f"no mapper registered for {mapper_key}")
        raw = groups_raw.get(group)
        if raw is None:
            sections.append({"type": "text", "heading": _PLACEHOLDER_BODY,
                             "body": _PLACEHOLDER_BODY})
            digests[group] = None
            continue
        try:
            result = mapper(raw)
        except Exception as exc:  # broken/partial MCP payload — degrade, don't die
            print(f"warning: group {group} mapping failed: {exc}", file=sys.stderr)
            sections.append({"type": "text", "heading": _PLACEHOLDER_BODY,
                             "body": _PLACEHOLDER_BODY})
            digests[group] = None
            continue
        sections.extend(result["sections"])
        digests[group] = result["digest"]
    return sections, digests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-type", required=True, choices=sorted(ORDERS))
    parser.add_argument("--data", required=True, help="combined raw JSON: {\"A\": <raw>, ...}")
    parser.add_argument("--out", required=True, help="assembled sections JSON for build.py")
    parser.add_argument("--digests", required=True, help="per-group digest JSON for the LLM")
    parser.add_argument("--title", required=True)
    parser.add_argument("--period", default=None)
    parser.add_argument("--branch", choices=["google_meta", "naver"],
                        help="daily only: brand branch determined once by the orchestrator")
    args = parser.parse_args()

    if args.report_type == "daily" and not args.branch:
        parser.error("--branch is required for report-type daily")

    groups_raw = json.loads(Path(args.data).read_text(encoding="utf-8"))
    sections, digests = assemble(args.report_type, groups_raw, args.branch)

    doc = {"title": args.title, "period": args.period, "sections": sections}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    Path(args.digests).write_text(json.dumps(digests, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
