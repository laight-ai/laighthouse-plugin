#!/usr/bin/env python3
"""daily-summary 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/브리즘_daily-summary_2026-05-15.html",  # 필수
  "title": "브리즘 Executive 데일리 보고서",                                       # 필수
  "target_date": "2026-05-15",                                                    # 필수 (D-0)
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
  "s2": {                    # Executive Summary — 불릿 카드 (3~5개)
    "bullets": [
      {"text": "Google Ads 매출이 전일 대비 <strong>+22.4%</strong> 성장...", "tone": "green"},
      {"text": "Meta Ads 매출이 전일 대비 -19.8% 감소...", "tone": "red"},
      {"text": "광고 매출 비중이 전일 15%에서 금일 43%로 확대...", "tone": "neutral"}
    ]                         # tone: green(성장/개선)|red(하락/점검 필요)|neutral(중립 관찰, 기본값)
                              # ("executive_summary" 문자열(\n 구분, 전부 neutral)도 허용)
  },
  "s3": {                    # 최근 7일 성과 — 배열은 전부 7개(기준일-6일 ~ 기준일 순)
    "ad_cost": [..7개..], "revenue": [..7개..], "roas": [..7개, 광고비 0인 날은 null..],
    "labels": ["5/9(토)", ...],   # 선택 — 생략하면 target_date 기준으로 자동 생성
    "promotions": [               # 선택 — list_promotions 응답의 원본 날짜를 그대로 넘기면
      {"title": "여름 세일", "date_begin": "2026-05-09", "date_end": "2026-05-11"}
    ]                             # 빌더가 인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리.
                                  # (이미 계산된 {title, start_idx, end_idx, range_label}도 허용)
  },
  "s4": {                    # 일일 매출 현황 (최근 7일) — 배열은 전부 7개
    "total_revenue": [..7개..], "ad_revenue": [..7개..],
    "labels": [["5/9","(토)"], ...],  # 선택 — 생략하면 자동 생성 ([날짜,요일] 2줄 라벨)
    "promotions": [...]               # s3와 동일한 원본 형식 — range_label만 "M월 D일~D일" 형식으로 생성
  },
  "s5": {                    # 매체별 성과 (D-1 vs D-0) — 매체별 원본 수치만 넘기면
    "rows": [                # ROAS·변화율·화살표·색상·정렬·포맷은 전부 빌더가 계산한다
      {"name": "Naver Ads",  "d1": {"cost": 156158, "revenue": 7864000, "reservation": 12},
                             "d0": {"cost": 149000, "revenue": 6964000, "reservation": 10}},
      {"name": "Google Ads", "d1": {...}, "d0": {...}},
      {"name": "Meta Ads",   "d1": {...}, "d0": {...}},
      {"name": "Organic",    "d1": {"revenue": ..., "reservation": ...}, "d0": {...}},  # cost 없음(항상 "-")
      {"name": "Others",     "d1": {...}, "d0": {...}}
    ]                        # 5개 행 고정(누락 채널은 빌더가 "-" 행으로 채움), D-0 매출 내림차순 정렬
  }
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...}}
"""
import io
import json
import os
import shutil
import sys
from datetime import date, timedelta

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ASSETS_DIR, "report-template.html")
CHART_JS = os.path.join(ASSETS_DIR, "chart.umd.min.js")
# 스킬 폴더 assets에 chart.umd.min.js가 없으면 자매 스킬 daily-detailed의 것을 복사해 온다.
CHART_JS_FALLBACK = os.path.normpath(os.path.join(
    ASSETS_DIR, "..", "..", "daily-detailed", "assets", "chart.umd.min.js"))

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]
PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'
S1_FOOTNOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
               "* 매체별 예산 및 목표 매출이 등록되지 않은 경우, 현황이 제대로 표시되지 않을 수 있습니다.</p>")

MONEY_FIELDS = {"목표_예산", "소진액", "목표_매출", "기간_매출"}
PCT_FIELDS = {"소진율", "매출_달성률", "실제_ROAS", "목표_ROAS"}

# section-2 불릿 점(●) 색상 — 성장/개선=초록, 하락/점검=빨강, 중립 관찰=회색-갈색
S2_TONE_COLORS = {"green": "#16a34a", "red": "#dc2626", "neutral": "#78716c"}

# section-5 — 5개 행 고정, Organic/Others는 광고비 개념 없음(항상 "-")
S5_CHANNELS = ["Naver Ads", "Google Ads", "Meta Ads", "Organic", "Others"]
S5_NO_COST = {"Organic", "Others"}
S5_UP_COLOR = "#dc2626"    # 증가 = 빨강 (이 섹션은 네 지표 전부 "증가=긍정")
S5_DOWN_COLOR = "#2563eb"  # 감소 = 파랑
S5_ZERO_COLOR = "#1e293b"  # 표시값 0.0 = 검정 (화살표 없음)


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


def week_dates(target):
    return [target - timedelta(days=6 - i) for i in range(7)]


def build_s3_labels(target):
    return [f"{d.month}/{d.day}({WEEKDAY_KO[d.weekday()]})" for d in week_dates(target)]


def build_s4_labels(target):
    # Chart.js가 배열 라벨을 두 줄로 렌더링하는 것을 이용 — 날짜(M/D) 아래에 (요일).
    return [[f"{d.month}/{d.day}", f"({WEEKDAY_KO[d.weekday()]})"] for d in week_dates(target)]


def s3_range_label(begin, end):
    if begin.month == end.month:
        return f"{begin.month}/{begin.day}~{end.day}"
    return f"{begin.month}/{begin.day}~{end.month}/{end.day}"


def s4_range_label(begin, end):
    if begin.month == end.month:
        return f"{begin.month}월 {begin.day}일~{end.day}일"
    return f"{begin.month}월 {begin.day}일~{end.month}월 {end.day}일"


def build_promotions(promos, target, label_fn):
    """list_promotions 원본(date_begin/date_end) 또는 사전 계산본을 받아
    인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리한다.
    range_label은 클램핑 전의 원래 날짜로 만든다."""
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
        out.append({"title": p.get("title", ""), "start_idx": max(0, raw_s),
                    "end_idx": min(6, raw_e), "range_label": label_fn(begin, end)})
    return out


def build_bullets(s2):
    """s2 → 불릿 카드 HTML. bullets 배열(text/tone) 우선, executive_summary 문자열도 허용."""
    bullets = s2.get("bullets")
    if bullets is None and s2.get("executive_summary"):
        bullets = [{"text": line.strip(), "tone": "neutral"}
                   for line in s2["executive_summary"].split("\n") if line.strip()]
    items = []
    for b in bullets or []:
        color = S2_TONE_COLORS.get(b.get("tone", "neutral"), S2_TONE_COLORS["neutral"])
        items.append(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px 18px; '
            'display:flex; gap:10px; align-items:flex-start;">\n'
            f'        <span style="color:{color}; font-size:14px; line-height:1.6;">●</span>\n'
            f'        <span style="font-size:13px; color:#374151; line-height:1.6;">{b.get("text", "")}</span>\n'
            '      </div>')
    return "\n      ".join(items)


# ── section-5: 매체별 성과 계산 ──────────────────────────────────────────────

def _num(d, key):
    v = (d or {}).get(key)
    return v if isinstance(v, (int, float)) else None


def _roas(cost, revenue):
    if cost is None or cost == 0 or revenue is None:
        return None
    return revenue / cost * 100


def _delta_html(d0, d1, suffix):
    """D-0 값 아래 변화량 div. D-1이 None/0(상대변화) 또는 None(%p)이면 표시 안 함.
    표시값(반올림) 0.0이면 화살표 없이 검정. 화살표는 원본 부호 기준."""
    if d0 is None or d1 is None:
        return ""
    if suffix == "%p":
        raw = d0 - d1
    else:
        if d1 == 0:
            return ""
        raw = (d0 - d1) / d1 * 100
    shown = round(raw, 1)
    if shown == 0:
        inner = f"(0.0{suffix})"
        color = S5_ZERO_COLOR
    else:
        arrow = "▲" if raw > 0 else "▼"
        color = S5_UP_COLOR if raw > 0 else S5_DOWN_COLOR
        inner = f"({arrow} {shown:+.1f}{suffix})"
    return f'\n            <div style="font-size:10.5px; text-align:center; color:{color};">{inner}</div>'


def _cell(value, delta="", border=False):
    style = "white-space:nowrap; text-align:center;"
    if border:
        style = "white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;"
    if delta:
        return f'<td style="{style}">\n            {value}{delta}\n          </td>'
    return f'<td style="{style}">{value}</td>'


def build_s5_rows(rows):
    """매체별 원본 수치 → ROAS 계산·변화량·화살표·색상·정렬·포맷·<tr> HTML.
    5개 행 고정(누락 채널은 "-" 행), D-0 매출 내림차순 정렬."""
    by_name = {r.get("name"): r for r in rows or []}
    prepared = []
    for name in S5_CHANNELS:
        r = by_name.get(name, {})
        d1, d0 = r.get("d1") or {}, r.get("d0") or {}
        no_cost = name in S5_NO_COST
        d1c = None if no_cost else _num(d1, "cost")
        d0c = None if no_cost else _num(d0, "cost")
        d1r, d0r = _num(d1, "revenue"), _num(d0, "revenue")
        d1b, d0b = _num(d1, "reservation"), _num(d0, "reservation")
        d1roas, d0roas = _roas(d1c, d1r), _roas(d0c, d0r)
        prepared.append({
            "name": name, "sort": d0r if d0r is not None else float("-inf"),
            "d1c": d1c, "d0c": d0c, "d1r": d1r, "d0r": d0r,
            "d1b": d1b, "d0b": d0b, "d1roas": d1roas, "d0roas": d0roas,
        })
    prepared.sort(key=lambda x: x["sort"], reverse=True)

    def money(v):
        return fmt_won(v) if v is not None else "-"

    def count(v):
        return f"{round(v):,}" if v is not None else "-"

    def pct(v):
        return fmt_pct(v) if v is not None else "-"

    trs = []
    for p in prepared:
        cells = [
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{p["name"]}</td>',
            _cell(money(p["d1c"])),
            _cell(money(p["d0c"]), _delta_html(p["d0c"], p["d1c"], "%"), border=True),
            _cell(money(p["d1r"])),
            _cell(money(p["d0r"]), _delta_html(p["d0r"], p["d1r"], "%"), border=True),
            _cell(count(p["d1b"])),
            _cell(count(p["d0b"]), _delta_html(p["d0b"], p["d1b"], "%"), border=True),
            _cell(pct(p["d1roas"])),
            _cell(pct(p["d0roas"]), _delta_html(p["d0roas"], p["d1roas"], "%p")),
        ]
        trs.append("<tr>\n          " + "\n          ".join(cells) + "\n        </tr>")
    return "\n        ".join(trs)


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
    if s2 and (s2.get("bullets") or s2.get("executive_summary")):
        status["s2"] = "ok"
        html = html.replace("__S2_ITEMS_HTML__", build_bullets(s2))
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── section 3 (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한 JSON으로 치환 —
    #    placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    if s3 and s3.get("ad_cost"):
        status["s3"] = "ok"
        s3_chart = {
            "labels": s3.get("labels") or build_s3_labels(target),
            "ad_cost": s3["ad_cost"],
            "revenue": s3.get("revenue", []),
            "roas": s3.get("roas", []),
        }
        s3_promos = build_promotions(s3.get("promotions"), target, s3_range_label)
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_chart = {"labels": [], "ad_cost": [], "revenue": [], "roas": []}
        s3_promos = []
    html = html.replace("__S3_CHART_DATA_JSON__", js_json(s3_chart))
    html = html.replace("__S3_PROMOTIONS_JSON__", js_json(s3_promos))

    # ── section 4
    s4 = section_data("s4")
    if s4 and s4.get("total_revenue"):
        status["s4"] = "ok"
        s4_chart = {
            "labels": s4.get("labels") or build_s4_labels(target),
            "total_revenue": s4["total_revenue"],
            "ad_revenue": s4.get("ad_revenue", []),
        }
        s4_promos = build_promotions(s4.get("promotions"), target, s4_range_label)
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_chart = {"labels": [], "total_revenue": [], "ad_revenue": []}
        s4_promos = []
    html = html.replace("__S4_CHART_DATA_JSON__", js_json(s4_chart))
    html = html.replace("__S4_PROMOTIONS_JSON__", js_json(s4_promos))

    # ── section 5
    s5 = section_data("s5")
    if s5 and s5.get("rows"):
        status["s5"] = "ok"
        html = html.replace("__S5_ROWS_HTML__", build_s5_rows(s5["rows"]))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

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
        "__S3_CHART_DATA_JSON__", "__S3_PROMOTIONS_JSON__", "__S4_CHART_DATA_JSON__",
        "__S4_PROMOTIONS_JSON__", "__S5_ROWS_HTML__", "__D1_", "__D0_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    if not os.path.exists(CHART_JS):
        if os.path.exists(CHART_JS_FALLBACK):
            shutil.copyfile(CHART_JS_FALLBACK, CHART_JS)
        else:
            raise SystemExit(f"chart.umd.min.js 없음: {CHART_JS} (fallback도 없음: {CHART_JS_FALLBACK})")
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
