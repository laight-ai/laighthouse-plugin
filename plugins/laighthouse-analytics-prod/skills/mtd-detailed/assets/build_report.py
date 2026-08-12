#!/usr/bin/env python3
"""mtd-detailed 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~7 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/브리즘_mtd-detailed_2026-05-15.html",  # 필수
  "title": "브리즘 MTD 보고서",                                                  # 필수
  "target_date": "2026-05-15",                                                   # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s7은 무시된다)

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
  "s3": {                    # 월별 광고 성과 — 배열은 전부 6개(5개월 전 → 당월 순)
    "ad_cost": [..6개..], "revenue": [..6개..], "roas": [..6개, 광고비 0인 달은 null..],
    "labels": ["26년 2월", ...],   # 선택 — 생략하면 target_date 기준 자동 생성(당월 "(진행 중)")
    "zero_fill_note": "* 26년 2월~26년 3월은 데이터가 수집되지 않아 광고비 또는 매출이 0으로 표시되었습니다."
                                   # 선택 — 0으로 채워진 월이 있을 때만 완성 문구를 넘긴다(없으면 생략)
  },                               # 당월 기준일 각주("* {YY}년 {M}월은 기준일...")는 빌더가 자동 생성
  "s4": {                    # 일일 매출 현황 — 배열은 월초~target_date 일수만큼(하루도 빠짐없이)
    "ad_revenue": [...], "total_revenue": [...],
    "labels": [["5/1","(금)"], ...],  # 선택 — 생략하면 빌더가 [M/D, (요일)] 자동 생성
    "promotions": [                   # 선택 — list_promotions 응답의 원본 날짜를 그대로 넘기면
      {"title": "여름 세일", "date_begin": "2026-05-01", "date_end": "2026-05-11"}
    ]                                 # 빌더가 인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리.
                                      # (이미 계산된 {title, start_idx, end_idx, range_label}도 허용)
  },
  "s5": { "campaign_analysis": "인트로 문단\n\n캠페인명 (Meta Ads)\n분석 문장..." },
                             # \n\n 블록 구분 — 첫 블록은 <p> 인트로, 이후 블록은 첫 줄 <h4> + 나머지 <p>
  "s6": {                    # 광고 매체별 현황 — 세 매체 행(숫자 원본 그대로, 계산 불가면 null)
    "rows": [
      {"channel": "Google Ads", "월_예산": 50000000, "소진액": 21000000, "예산_소진율": 42.0,
       "목표_매출": null, "광고_매출": 34000000, "매출_달성률": null, "목표_ROAS": null, "ROAS": 161.9},
      ...  # Meta Ads / Naver Ads — no-budget 매체도 행을 빼지 않는다(N/A 규칙)
    ]
  },
  "s7": {                    # 캠페인 성과 — 아래 형태 중 하나 (조인·파생지표·정렬·<tr>은 빌더가 처리)
    # (a) 매체 행/airbridge 행을 그대로 전사 (전 행 — 선별·요약 금지):
    "media_rows": [ {"channel":"Google Ads","campaign":"...","impression":1000,"click":50,"cost":54832}, ... ],
    "airbridge_rows": [ {"campaign":"...","revenue":1200000,"reservation":3}, ... ]
    # (b) "rows": [...] — 이미 조인된 행(campaign별 {channel,campaign,impression,click,cost,revenue,reservation},
    #     미매칭이면 revenue/reservation을 null 대신 생략하지 말고 "unmatched": true)
    # (c) "rows_file": "/tmp/s7.json" — (a)/(b) 형태의 JSON 파일 경로
    # (d) "markdown": ["<range_table 응답 원본 문자열>", ...] / "markdown_files": ["<경로>", ...]
    #     — 4개 응답 원본을 가공 없이 그대로 담으면 빌더가 파싱·media 분리·조인까지 처리
  }
}

- s1~s7 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
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

MONEY_FIELDS = {"목표_예산", "소진액", "목표_매출", "기간_매출", "월_예산", "광고_매출"}
PCT_FIELDS = {"소진율", "매출_달성률", "실제_ROAS", "목표_ROAS", "예산_소진율", "ROAS"}

MEDIA_LABEL = {"google": "Google Ads", "meta": "Meta Ads", "naver": "Naver Ads"}
STRING_FIELDS = {"logdate", "media", "campaign_name", "asset_group", "ad_name", "channel"}


def fmt_won(v):
    return f"₩{round(v):,}"


def fmt_pct(v):
    return f"{v:.1f}%"


def fmt_int(v):
    return f"{round(v):,}"


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


# ── 날짜 파생값 ─────────────────────────────────────────────────────────────

def month_shift(y, m, delta):
    idx = (y * 12 + (m - 1)) + delta
    return idx // 12, idx % 12 + 1


def build_month_labels(target):
    """최근 6개월 라벨 — '{YY}년 {M}월', 당월은 ' (진행 중)' 접미사."""
    labels = []
    for i in range(-5, 1):
        y, m = month_shift(target.year, target.month, i)
        label = f"{y % 100}년 {m}월"
        if i == 0:
            label += " (진행 중)"
        labels.append(label)
    return labels


def build_day_labels(target):
    """월초~target_date, [['M/D', '(요일)'], ...] — 하루도 건너뛰지 않는다."""
    first = target.replace(day=1)
    return [[f"{d.month}/{d.day}", f"({WEEKDAY_KO[d.weekday()]})"]
            for d in (first + timedelta(days=i) for i in range((target - first).days + 1))]


def build_promotions(promos, target):
    """list_promotions 원본(date_begin/date_end) 또는 사전 계산본을 받아
    인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리한다."""
    if not promos:
        return []
    first = target.replace(day=1)
    n = (target - first).days + 1
    out = []
    for p in promos:
        if "start_idx" in p and "end_idx" in p:
            out.append({"title": p.get("title", ""), "start_idx": max(0, min(n - 1, p["start_idx"])),
                        "end_idx": max(0, min(n - 1, p["end_idx"])),
                        "range_label": p.get("range_label", "")})
            continue
        begin = date.fromisoformat(str(p["date_begin"])[:10])
        end = date.fromisoformat(str(p["date_end"])[:10])
        raw_s = (begin - first).days
        raw_e = (end - first).days
        if raw_e < 0 or raw_s > n - 1:
            continue  # 차트 범위와 전혀 안 겹침
        if begin.month == end.month:
            range_label = f"{begin.month}월 {begin.day}일~{end.day}일"
        else:
            range_label = f"{begin.month}월 {begin.day}일~{end.month}월 {end.day}일"
        out.append({"title": p.get("title", ""), "start_idx": max(0, raw_s),
                    "end_idx": min(n - 1, raw_e), "range_label": range_label})
    return out


# ── 텍스트 섹션(s2/s5) ──────────────────────────────────────────────────────

def build_summary_items(text):
    items = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
        items.append(f"<li{style}>{line}</li>")
    return "\n      ".join(items)


def _para(line):
    style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
    return f"<p{style}>{line}</p>"


def build_analysis_blocks(text):
    """\n\n 블록 구분 — 첫 블록은 <p> 인트로, 이후 블록은 첫 줄 <h4> + 나머지 <p>."""
    blocks = [b.strip() for b in (text or "").split("\n\n") if b.strip()]
    parts = []
    for i, block in enumerate(blocks):
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if i == 0:
            parts.extend(_para(ln) for ln in lines)
            continue
        parts.append(f'<h4 style="font-size:14px; font-weight:700; margin:16px 0 6px;">{lines[0]}</h4>')
        parts.extend(_para(ln) for ln in lines[1:])
    return "\n      ".join(parts)


# ── section 6 ───────────────────────────────────────────────────────────────

S6_FIELDS = ["월_예산", "소진액", "예산_소진율", "목표_매출", "광고_매출", "매출_달성률", "목표_ROAS", "ROAS"]


def build_s6_rows(rows):
    trs = []
    for r in rows:
        v = {f: fmt_value(f, r.get(f)) for f in S6_FIELDS}
        trs.append(
            "<tr>\n"
            f'        <td style="border-right:1px solid #e2e8f0;">{r.get("channel", "")}</td>\n'
            f'        <td>{v["월_예산"]}</td><td>{v["소진액"]}</td>'
            f'<td style="border-right:1px solid #e2e8f0;">{v["예산_소진율"]}</td>\n'
            f'        <td>{v["목표_매출"]}</td><td>{v["광고_매출"]}</td>'
            f'<td style="border-right:1px solid #e2e8f0;">{v["매출_달성률"]}</td>\n'
            f'        <td>{v["목표_ROAS"]}</td><td>{v["ROAS"]}</td>\n'
            "      </tr>"
        )
    return "\n      ".join(trs)


# ── section 7 ───────────────────────────────────────────────────────────────

def _coerce_cell(key, value):
    value = value.strip()
    if key in STRING_FIELDS:
        return value
    if value == "":
        return None
    try:
        f = float(value)
    except ValueError:
        return value  # 예상 못 한 비숫자 값은 문자열 그대로 보존(방어적)
    return int(f) if f.is_integer() else f


def unwrap_json_result(text):
    """Cowork(Claude Desktop) 계층이 저장한 응답은 `{"result": "<본문>"}` JSON 래퍼일 수
    있다(줄바꿈이 리터럴 \\n) — 래퍼면 벗기고, 아니면 그대로 돌려준다."""
    for _ in range(3):
        if not isinstance(text, str) or not text.lstrip().startswith("{"):
            return text
        try:
            obj = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return text
        if isinstance(obj, dict) and isinstance(obj.get("result"), str):
            text = obj["result"]
        elif isinstance(obj, str):
            text = obj
        else:
            return text
    return text


def parse_markdown_table(text):
    """`get_ad_performance_range_table` 등이 반환하는 파이프(|) 마크다운 표 문자열을
    행 dict 리스트로 파싱한다. 구분선(전부 `---`)은 건너뛴다."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    header = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(c == "" or set(c) <= {"-"} for c in cells):
            continue
        if len(cells) != len(header):
            continue
        rows.append({h: _coerce_cell(h, v) for h, v in zip(header, cells)})
    return rows


def load_s7_input(section):
    """s7 입력을 정규화 — {'media_rows':[...], 'airbridge_rows':[...]} 또는 {'rows':[...]}."""
    data = section
    path = section.get("rows_file")
    if path:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            data = {"rows": data}
    if "markdown" in data or "markdown_files" in data:
        md = data.get("markdown", [])
        if isinstance(md, str):
            md = [md]
        md = list(md)
        files = data.get("markdown_files", [])
        if isinstance(files, str):
            files = [files]
        for p in files:
            with open(os.path.expanduser(p), encoding="utf-8") as f:
                md.append(f.read())
        raw = [r for text in md for r in parse_markdown_table(unwrap_json_result(text))]
        media_rows = [{"channel": MEDIA_LABEL[r["media"]], "campaign": r.get("campaign_name") or "",
                       "impression": r.get("impression"), "click": r.get("click"), "cost": r.get("cost")}
                      for r in raw if r.get("media") in MEDIA_LABEL]
        ab_rows = [{"campaign": r.get("campaign_name") or "",
                    "revenue": r.get("airbridge_revenue"), "reservation": r.get("reservation")}
                   for r in raw if r.get("media") == "airbridge"]
        if not media_rows:
            raise SystemExit("s7 markdown 파싱 결과 매체 행이 0개 — 원본이 range_table 응답인지 확인")
        return {"media_rows": media_rows, "airbridge_rows": ab_rows}
    return data


def join_s7_rows(media_rows, airbridge_rows):
    """캠페인 이름 정확 일치(exact match) 조인 — airbridge 쪽에만 있는 캠페인은 제외,
    매체 쪽에만 있는 캠페인은 unmatched(매출/예약 '-')."""
    ab = {}
    for r in airbridge_rows or []:
        k = r.get("campaign") or ""
        cur = ab.setdefault(k, {"revenue": 0, "reservation": 0})
        cur["revenue"] += r.get("revenue") or 0
        cur["reservation"] += r.get("reservation") or 0
    out = []
    for r in media_rows:
        m = ab.get(r.get("campaign") or "")
        row = dict(r)
        if m is None:
            row["unmatched"] = True
            row["revenue"] = None
            row["reservation"] = None
        else:
            row["unmatched"] = False
            row["revenue"] = m["revenue"]
            row["reservation"] = m["reservation"]
        out.append(row)
    return out


def build_s7_rows(section):
    data = load_s7_input(section)
    if "rows" in data:
        rows = data["rows"]
    else:
        rows = join_s7_rows(data["media_rows"], data.get("airbridge_rows") or [])

    out = []
    for r in sorted(rows, key=lambda x: x.get("cost") or 0, reverse=True):
        channel = r.get("channel") or ""
        campaign = r.get("campaign") or ""
        impression = r.get("impression")
        click = r.get("click")
        cost = r.get("cost") or 0
        unmatched = bool(r.get("unmatched")) or ("revenue" not in r and "reservation" not in r)
        revenue = r.get("revenue")
        reservation = r.get("reservation")

        ctr = (click / impression * 100) if impression else None
        d = {
            "노출": fmt_int(impression) if impression is not None else "N/A",
            "클릭": fmt_int(click) if click is not None else "N/A",
            "CTR": fmt_pct(ctr) if ctr is not None else "N/A",
            "광고비": fmt_won(cost),
        }
        if unmatched:
            d["매출"] = d["예약_완료"] = d["CPA"] = d["ROAS"] = "-"
        else:
            d["매출"] = fmt_won(revenue) if revenue is not None else "N/A"
            d["예약_완료"] = fmt_int(reservation) if reservation is not None else "N/A"
            d["CPA"] = fmt_won(cost / reservation) if reservation else "N/A"
            d["ROAS"] = fmt_pct(revenue / cost * 100) if (revenue is not None and cost) else "N/A"

        html = (
            "<tr>\n"
            f'          <td style="border-right:1px solid #e2e8f0;">{channel}</td>'
            f'<td style="text-align:left; border-right:1px solid #e2e8f0;">{campaign}</td>'
            f'<td>{d["노출"]}</td><td>{d["클릭"]}</td><td>{d["CTR"]}</td>\n'
            f'          <td>{d["광고비"]}</td><td>{d["매출"]}</td><td>{d["예약_완료"]}</td>'
            f'<td>{d["CPA"]}</td><td>{d["ROAS"]}</td>\n'
            "        </tr>"
        )
        out.append({"search": f"{channel} {campaign}".lower(), "html": html})
    return out


# ── main ────────────────────────────────────────────────────────────────────

def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
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
        s3_chart = {
            "labels": s3.get("labels") or build_month_labels(target),
            "ad_cost": s3["ad_cost"],
            "revenue": s3.get("revenue", []),
            "roas": s3.get("roas", []),
        }
        footnote_current = (f"* {target.year % 100}년 {target.month}월은 "
                            f"기준일({target.month}/{target.day})까지의 데이터만 포함합니다.")
        html = html.replace("__S3_FOOTNOTE_CURRENT_MONTH__", footnote_current)
        html = html.replace("__S3_FOOTNOTE_ZERO_FILL__", s3.get("zero_fill_note") or "")
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_chart = {"labels": [], "ad_cost": [], "revenue": [], "roas": []}
    html = html.replace("__S3_CHART_DATA_JSON__", js_json(s3_chart))

    # ── section 4
    s4 = section_data("s4")
    if s4 and (s4.get("ad_revenue") or s4.get("total_revenue")):
        status["s4"] = "ok"
        s4_chart = {
            "labels": s4.get("labels") or build_day_labels(target),
            "ad_revenue": s4.get("ad_revenue", []),
            "total_revenue": s4.get("total_revenue", []),
        }
        promotions = build_promotions(s4.get("promotions"), target)
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_chart = {"labels": [], "ad_revenue": [], "total_revenue": []}
        promotions = []
    html = html.replace("__S4_CHART_DATA_JSON__", js_json(s4_chart))
    html = html.replace("__S4_PROMOTIONS_JSON__", js_json(promotions))

    # ── section 5
    s5 = section_data("s5")
    if s5 and s5.get("campaign_analysis"):
        status["s5"] = "ok"
        html = html.replace("__S5_BLOCKS_HTML__", build_analysis_blocks(s5["campaign_analysis"]))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

    # ── section 6
    s6 = section_data("s6")
    if s6 and s6.get("rows"):
        status["s6"] = "ok"
        html = html.replace("__S6_ROWS_HTML__", build_s6_rows(s6["rows"]))
    else:
        status["s6"] = "placeholder"
        html = swap_section(html, "s6", PLACEHOLDER_CARD)

    # ── section 7
    s7 = section_data("s7")
    if s7 and any(k in s7 for k in ("rows", "rows_file", "media_rows", "markdown", "markdown_files")):
        status["s7"] = "ok"
        s7_rows = build_s7_rows(s7)
    else:
        status["s7"] = "placeholder"
        html = swap_section(html, "s7", PLACEHOLDER_CARD)
        s7_rows = []
    html = html.replace("__S7_ROWS_JSON__", js_json(s7_rows))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 1일 ~ {target.month}월 {target.day}일")
    html = html.replace("__T_MM__", str(target.month)).replace("__T_DD__", str(target.day))

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__T_MM__", "__T_DD__",
        "__S1_", "__S2_ITEMS_HTML__", "__S3_", "__S4_", "__S5_BLOCKS_HTML__",
        "__S6_ROWS_HTML__", "__S7_ROWS_JSON__",
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
