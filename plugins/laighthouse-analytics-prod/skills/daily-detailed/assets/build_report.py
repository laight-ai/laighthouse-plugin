#!/usr/bin/env python3
"""daily-detailed 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/브리즘_daily-detailed_2026-08-10.html",  # 필수
  "title": "브리즘 데일리 보고서",                                                  # 필수
  "target_date": "2026-08-10",                                                     # 필수 (D-0)
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)

  "s1": {                    # 목표 달성 현황 — 숫자(원본 수치) 또는 표시 문자열, 없으면 null
    "소진율": 33.13,          # 숫자면 % 소수점 1자리로 포맷, null이면 "N/A"
    "목표_예산": 168110000,   # 숫자면 ₩+천단위 콤마로 포맷
    "소진액": 55700000,
    "매출_달성률": null,
    "목표_매출": null,
    "기간_매출": 123456789,
    "실제_ROAS": 221.7,
    "목표_ROAS": null,
    "footnote": true          # 목표(예산/매출) 없는 매체가 하나라도 있으면 true → 고정 각주 표시
  },
  "s2": { "executive_summary": "문장1\n문장2\n⚠ 주의 문장..." },  # \n 구분, ⚠ 시작 줄은 주황색
  "s3": {                    # 최근 7일 성과 — 배열은 전부 7개(기준일-6일 ~ 기준일 순)
    "ad_cost": [..7개..], "revenue": [..7개..], "roas": [..7개, 광고비 0인 날은 null..],
    "labels": ["8/4(화)", ...],   # 선택 — 생략하면 target_date 기준으로 자동 생성
    "promotions": [               # 선택 — list_promotions 응답의 원본 날짜를 그대로 넘기면
      {"title": "여름 세일", "date_begin": "2026-08-01", "date_end": "2026-08-31"}
    ]                             # 빌더가 인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리.
                                  # (이미 계산된 {title, start_idx, end_idx, range_label}도 허용)
  },
  "s4": { "rows_file": "/tmp/s4.json" },   # dxd_table_rows.py 출력(level:"campaign") 파일 경로
  "s5": { "rows_file": "/tmp/s5.json" }    # dxd_table_rows.py 출력(level:"ad") 파일 경로
                                           # (파일 대신 "rows": [...] 직접 전달도 허용)
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...}}
"""
import io
import json
import os
import sys
from datetime import date, timedelta

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ASSETS_DIR, "report-template.html")
CHART_JS = os.path.join(ASSETS_DIR, "chart.umd.min.js")

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]
PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'
S1_FOOTNOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
               "* 매체별 예산 및 목표 매출이 등록되지 않은 경우, 현황이 제대로 표시되지 않을 수 있습니다.</p>")

MONEY_FIELDS = {"목표_예산", "소진액", "목표_매출", "기간_매출"}
PCT_FIELDS = {"소진율", "매출_달성률", "실제_ROAS", "목표_ROAS"}


def fmt_won(v):
    return f"₩{round(v):,}"


def fmt_pct(v):
    return f"{v:.1f}%"


def fmt_value(field, v):
    """숫자면 필드 종류에 맞게 포맷, 문자열이면 그대로, None이면 N/A."""
    if v is None:
        return "N/A"
    if isinstance(v, str):
        return v
    if field in MONEY_FIELDS:
        return fmt_won(v)
    if field in PCT_FIELDS:
        return fmt_pct(v)
    return str(v)


def js_json(value):
    """<script> 안에 삽입할 JSON — </script> 조기 종료 방지."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def swap_section(html, key, replacement):
    begin = f"<!--SECTION:{key}:BEGIN-->"
    end = f"<!--SECTION:{key}:END-->"
    i = html.index(begin)
    j = html.index(end) + len(end)
    return html[:i] + replacement + html[j:]


def build_labels(target):
    return [f"{d.month}/{d.day}({WEEKDAY_KO[d.weekday()]})"
            for d in (target - timedelta(days=6 - i) for i in range(7))]


def build_promotions(promos, target):
    """list_promotions 원본(date_begin/date_end) 또는 사전 계산본을 받아
    인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리한다."""
    if not promos:
        return []
    first = target - timedelta(days=6)
    out = []
    for p in promos:
        if "start_idx" in p and "end_idx" in p:
            out.append({"title": p.get("title", ""), "start_idx": max(0, min(6, p["start_idx"])),
                        "end_idx": max(0, min(6, p["end_idx"])),
                        "range_label": p.get("range_label", "")})
            continue
        begin = date.fromisoformat(str(p["date_begin"])[:10])
        end = date.fromisoformat(str(p["date_end"])[:10])
        raw_s = (begin - first).days
        raw_e = (end - first).days
        if raw_e < 0 or raw_s > 6:
            continue  # 차트 범위와 전혀 안 겹침
        if begin.month == end.month:
            range_label = f"{begin.month}/{begin.day}~{end.day}"
        else:
            range_label = f"{begin.month}/{begin.day}~{end.month}/{end.day}"
        out.append({"title": p.get("title", ""), "start_idx": max(0, raw_s),
                    "end_idx": min(6, raw_e), "range_label": range_label})
    return out


def build_summary_items(text):
    items = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
        items.append(f"<li{style}>{line}</li>")
    return "\n      ".join(items)


def load_rows(section):
    if not section:
        return None
    if "rows" in section:
        return section["rows"]
    path = section.get("rows_file")
    if not path:
        return None
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return json.load(f)


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    d1 = target - timedelta(days=1)
    skeleton = bool(payload.get("skeleton"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1
    s1 = section_data("s1")
    if s1:
        status["s1"] = "ok"
        for field in ["소진율", "목표_예산", "소진액", "매출_달성률", "목표_매출", "기간_매출", "실제_ROAS", "목표_ROAS"]:
            html = html.replace(f"__S1_{field}__", fmt_value(field, s1.get(field)))
        html = html.replace("__S1_MM__", str(target.month)).replace("__S1_DD__", str(target.day))
        html = html.replace("__S1_FOOTNOTE_HTML__", S1_FOOTNOTE if s1.get("footnote") else "")
    else:
        status["s1"] = "placeholder"
        html = swap_section(html, "s1", PLACEHOLDER_CARD)

    # ── section 2
    s2 = section_data("s2")
    if s2 and s2.get("executive_summary"):
        status["s2"] = "ok"
        html = html.replace("__S2_ITEMS_HTML__", build_summary_items(s2["executive_summary"]))
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── section 3 (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한 JSON으로 치환 —
    #    placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    if s3 and s3.get("ad_cost"):
        status["s3"] = "ok"
        chart_data = {
            "labels": s3.get("labels") or build_labels(target),
            "ad_cost": s3["ad_cost"],
            "revenue": s3.get("revenue", []),
            "roas": s3.get("roas", []),
        }
        promotions = build_promotions(s3.get("promotions"), target)
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        chart_data = {"labels": [], "ad_cost": [], "revenue": [], "roas": []}
        promotions = []
    html = html.replace("__S3_CHART_DATA_JSON__", js_json(chart_data))
    html = html.replace("__S3_PROMOTIONS_JSON__", js_json(promotions))

    # ── section 4 / 5
    for key in ("s4", "s5"):
        rows = load_rows(section_data(key))
        if rows is not None:
            status[key] = "ok"
        else:
            status[key] = "placeholder"
            html = swap_section(html, key, PLACEHOLDER_CARD)
            rows = []
        html = html.replace(f"__{key.upper()}_ROWS_JSON__", js_json(rows))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__REPORT_DATE_LABEL__", f"{target.year}년 {target.month}월 {target.day}일 기준")
    html = (html.replace("__D1_MM__", str(d1.month)).replace("__D1_DD__", str(d1.day))
                .replace("__D0_MM__", str(target.month)).replace("__D0_DD__", str(target.day))
                .replace("__D1_M__", str(d1.month)).replace("__D1_D__", str(d1.day))
                .replace("__D0_M__", str(target.month)).replace("__D0_D__", str(target.day)))

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_ITEMS_HTML__",
        "__S3_CHART_DATA_JSON__", "__S3_PROMOTIONS_JSON__", "__S4_ROWS_JSON__",
        "__S5_ROWS_JSON__", "__D1_", "__D0_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    with open(CHART_JS, encoding="utf-8") as f:
        html = html.replace("__CHART_JS_INLINE__", f.read())

    out_path = os.path.abspath(os.path.expanduser(payload["out"]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path), "sections": status},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
