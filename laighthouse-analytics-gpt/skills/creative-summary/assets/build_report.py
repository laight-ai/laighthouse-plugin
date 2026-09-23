#!/usr/bin/env python3
"""creative-summary 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_creative-summary_{기준_일자}.html",  # 필수
  "title": "{브랜드명} Executive 소재 보고서",                                            # 필수
  "target_date": "YYYY-MM-DD",                                                       # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)
  "metric_keys": { ... },    # 디스커버리(discover.py) 출력 그대로 — revenue 유무로 모드를 정한다
                             # (generic-report-pattern.md 7절). 생략하면 series 파일의
                             # has_revenue를 쓴다. 클릭 라벨은 click 키 값 그대로 쓴다.

  "series_file": "/tmp/creative_series.json",  # creative_daily_series.py 출력 파일 경로 —
                                               # s3(overall)와 s4/5(top5)가 이 한 파일을 공유한다.
                                               # (파일 대신 "series": {...} 직접 전달도 허용)

  "s1": {                    # 최우수 소재 — 각 배열 1·2위 순 (2위 없으면 1개만)
    "roas":  [ {"name": "<ad_name>", "value": 388.1, "thumbnail_url": "https://..."} ],  # 매출 있음 모드
    "click": [ {"name": "<ad_name>", "value": 5321, "thumbnail_url": null} ],          # 매출 없음 모드
    "ctr":   [ {"name": "<ad_name>", "value": 2.4, "thumbnail_url": "https://..."} ]    # 두 모드 공통
  },                         # value: ROAS/CTR은 % 스케일 숫자(소수 1자리 포맷), click은 7일 합 클릭 수
  "s2": {                    # Executive Summary — 불릿 배열. tone이 점(●) 색을 정한다:
    "bullets": [             #   "good"(평균 대비 뚜렷한 고성과)=초록, "bad"(비효율/액션 필요)=빨강,
      {"text": "문장... <strong>2.4%</strong> ...", "tone": "good"},                #   "neutral"=회색-갈색
      {"text": "문장...", "tone": "bad"}
    ]                        # (문자열 배열/"executive_summary" 문자열도 허용 — 전부 neutral 처리)
  },
  "s3": {},                  # 키가 존재하면 series의 overall(ctr_series + roas_series|click_series)로 렌더링
  "s4": { "names": ["소재 표시이름1", ...] },  # 상위 5개 표시 이름(광고비 내림차순) — top5.ctr_series 사용
  "s5": {}                   # names는 s4와 공유, top5.roas_series(매출 없음: top5.click_series) 사용
                             # (s3/s4/s5에 개별 "series_file"/"series"를 넣으면 그 섹션만 그걸 쓴다)
}

- 모드: 매출 있음 → section-1 왼쪽 카드 "ROAS 최우수 소재", section-3 둘째 차트 "전체 ROAS",
  section-5 "일별 ROAS". 매출 없음 → 각각 "클릭 최우수 소재", "전체 클릭", "일별 클릭". 제목·각주·
  단위는 빌더가 바꾼다 — 모델은 모드에 맞는 s1 배열(roas 또는 click)만 넣는다.
- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 라벨: series 출력의 dates(없으면 target_date 기준 7일)로 빌더가 자동 생성 —
  section-3은 "M/D(요일)", section-4/5는 "M/D" 형식.
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...},
                "mode": {"has_revenue": bool}}
"""
import html as html_mod
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


def _load_kit():
    for cand in (os.path.join(ASSETS_DIR, "..", "shared", "assets"),          # ChatGPT 번들
                 os.path.join(ASSETS_DIR, "..", "..", "..", "shared", "assets")):  # 플러그인 루트
        if os.path.exists(os.path.join(cand, "report_kit.py")):
            sys.path.insert(0, os.path.normpath(cand))
            import report_kit
            return report_kit
    raise SystemExit("report_kit.py를 찾을 수 없다 (shared/assets)")


kit = _load_kit()

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]
PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'

DOT_COLORS = {"good": "#16a34a", "bad": "#dc2626", "neutral": "#78716c"}

# 모드별 문구 (generic-report-pattern.md 7절 — 소재 보고서: 매출 있음 ROAS·CTR / 매출 없음 클릭·CTR)
S1_A_TITLE = {True: "ROAS 최우수 소재 (최근 7일 기준)", False: "클릭 최우수 소재 (최근 7일 기준)"}
S1_A_NOTE = {
    True: "*'매출/광고비'로 계산되며, 높을수록 소재에서 매출이 효율적으로 발생하고 있음을 의미합니다.",
    False: "*최근 7일 합산 클릭 수 기준이며, 많을수록 소재가 고객의 관심을 많이 끌었음을 의미합니다. "
           "단, 클릭 수는 광고비 규모에 비례하므로 CTR과 함께 보아야 합니다.",
}
S3B_TITLE = {True: "최근 7일 전체 소재 ROAS", False: "최근 7일 전체 소재 클릭"}
S3B_NOTE = {
    True: "* 위 차트에 포함된 ROAS는 개별 소재 성과의 합계입니다. 이미지나 비디오 소재 단위에서\n"
          "      성과를 측정하지 않는 매체나 캠페인의 성과는 포함하지 않습니다. (예: 검색광고)",
    False: "* 위 차트의 클릭은 개별 소재 클릭의 날짜별 합계입니다. 이미지나 비디오 소재 단위에서\n"
           "      성과를 측정하지 않는 매체나 캠페인의 성과는 포함하지 않습니다. (예: 검색광고)",
}
S5_TITLE = {True: "최근 7일 일별 ROAS (광고비 상위 5개 소재)",
            False: "최근 7일 일별 클릭 (광고비 상위 5개 소재)"}

# section-1 이미지 셀 (2위 없으면 이미지/링크를 렌더링하지 않는다).
IMG_CELL = (
    '<img style="width:100%; max-width:220px; height:180px; border-radius:8px; object-fit:cover; display:block; margin:0 auto;"\n'
    '               src="{url}" alt="{name} 썸네일"\n'
    '               onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'inline\';">\n'
    '          <a href="{url}" target="_blank" style="display:none; color:#2563eb; text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>'
)

BULLET_CARD = (
    '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px 18px; display:flex; gap:10px; align-items:flex-start;">\n'
    '        <span style="color:{color}; font-size:14px; line-height:1.6;">●</span>\n'
    '        <span style="font-size:13px; color:#374151; line-height:1.6;">{text}</span>\n'
    '      </div>'
)


def esc(v):
    return html_mod.escape(str(v if v is not None else ""), quote=True)


def fmt_value(v, kind):
    """kind 'pct' → % 소수 1자리, 'count' → 콤마 정수. 문자열은 그대로, None은 '-'."""
    if v is None:
        return "-"
    if isinstance(v, str):
        return esc(v)
    return kit.fmt_pct(v) if kind == "pct" else kit.fmt_count(v)


def swap_section(html, key, replacement):
    begin = f"<!--SECTION:{key}:BEGIN-->"
    end = f"<!--SECTION:{key}:END-->"
    i = html.index(begin)
    j = html.index(end) + len(end)
    return html[:i] + replacement + html[j:]


def default_dates(target):
    return [(target - timedelta(days=6 - i)).isoformat() for i in range(7)]


def labels_with_weekday(dates):
    out = []
    for s in dates:
        d = date.fromisoformat(str(s)[:10])
        out.append(f"{d.month}/{d.day}({WEEKDAY_KO[d.weekday()]})")
    return out


def labels_plain(dates):
    out = []
    for s in dates:
        d = date.fromisoformat(str(s)[:10])
        out.append(f"{d.month}/{d.day}")
    return out


def load_series(payload, section):
    """섹션 개별 series/series_file이 있으면 그걸, 없으면 최상위 것을 쓴다."""
    for src in (section or {}, payload):
        if isinstance(src.get("series"), dict):
            return src["series"]
        path = src.get("series_file")
        if path:
            with open(os.path.expanduser(path), encoding="utf-8") as f:
                return json.load(f)
    return None


def s1_rank_tokens(html, prefix, ranks, metric_label, kind):
    """prefix: 'S1_A'|'S1_CTR', ranks: [{name,value,thumbnail_url}, ...] (0~2개)."""
    ranks = ranks or []
    for i in (0, 1):
        n = i + 1
        item = ranks[i] if i < len(ranks) else None
        if item:
            name = esc(item.get("name") or "-")
            value = item.get("value")
            value_text = "-" if value is None else f"{esc(metric_label)}: {fmt_value(value, kind)}"
            url = item.get("thumbnail_url")
            img = IMG_CELL.format(url=esc(url), name=name) if url else ""
        else:
            name, value_text, img = "-", "-", ""
        html = (html.replace(f"__{prefix}_{n}_NAME__", name)
                    .replace(f"__{prefix}_{n}_VALUE__", value_text)
                    .replace(f"__{prefix}_{n}_IMG_HTML__", img))
    return html


def build_bullets(s2):
    """bullets: [{"text","tone"|"color"}] / 문자열 배열 / "executive_summary" 문자열 전부 허용."""
    items = s2.get("bullets")
    if items is None and s2.get("executive_summary"):
        items = [ln for ln in s2["executive_summary"].split("\n") if ln.strip()]
    cards = []
    for item in items or []:
        if isinstance(item, str):
            text, color = item.strip(), DOT_COLORS["neutral"]
        else:
            text = (item.get("text") or "").strip()
            color = item.get("color") or DOT_COLORS.get(item.get("tone"), DOT_COLORS["neutral"])
        if text:
            cards.append(BULLET_CARD.format(color=color, text=text))
    return "\n      ".join(cards)


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    skeleton = bool(payload.get("skeleton"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    # ── 모드: metric_keys의 revenue 유무 (생략 시 series 파일의 has_revenue, 그것도 없으면 매출 있음)
    if payload.get("metric_keys"):
        modes = kit.Modes(payload["metric_keys"])
        has_revenue = modes.has_revenue
        click_label = modes.label("click")
    else:
        top_series = (None if skeleton else load_series(payload, None)) or {}
        has_revenue = bool(top_series.get("has_revenue", True))
        click_label = kit.DEFAULT_LABELS["click"]

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1: 최우수 소재 (왼쪽 카드: 매출 있음 ROAS / 매출 없음 클릭, 오른쪽: CTR)
    s1 = section_data("s1")
    a_key = "roas" if has_revenue else "click"
    if s1 and (s1.get(a_key) or s1.get("ctr")):
        status["s1"] = "ok"
        html = html.replace("__S1_A_TITLE__", S1_A_TITLE[has_revenue])
        html = html.replace("__S1_A_NOTE__", S1_A_NOTE[has_revenue])
        html = s1_rank_tokens(html, "S1_A", s1.get(a_key),
                              "ROAS" if has_revenue else click_label,
                              "pct" if has_revenue else "count")
        html = s1_rank_tokens(html, "S1_CTR", s1.get("ctr"), "CTR", "pct")
    else:
        status["s1"] = "placeholder"
        html = swap_section(html, "s1", PLACEHOLDER_CARD)

    # ── section 2: Executive Summary
    s2 = section_data("s2")
    bullets_html = build_bullets(s2) if s2 else ""
    if bullets_html:
        status["s2"] = "ok"
        html = html.replace("__S2_BULLETS_HTML__", bullets_html)
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── 공유 시리즈 (creative_daily_series.py 출력) — dates가 라벨의 근거
    dates = default_dates(target)
    second_key = "roas_series" if has_revenue else "click_series"
    second_unit = "%" if has_revenue else ""

    # ── section 3: 전체 소재 CTR + ROAS(매출 없음: 클릭) (스크립트 데이터는 섹션 유무와 무관하게
    #    항상 유효한 JSON으로 치환 — placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    series3 = load_series(payload, s3) if s3 is not None else None
    overall = (series3 or {}).get("overall") or {}
    if s3 is not None and overall.get("ctr_series"):
        status["s3"] = "ok"
        if series3.get("dates"):
            dates = series3["dates"]
        ctr_series = overall["ctr_series"]
        second_series = overall.get(second_key) or []
        html = html.replace("__S3B_TITLE__", S3B_TITLE[has_revenue])
        html = html.replace("__S3B_NOTE__", S3B_NOTE[has_revenue])
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        ctr_series, second_series = [], []
    html = html.replace("__S3_LABELS_JSON__", kit.js_json(labels_with_weekday(dates)))
    html = html.replace("__S3_CTR_SERIES_JSON__", kit.js_json(ctr_series))
    html = html.replace("__S3B_JSON__", kit.js_json({
        "label": "전체 ROAS" if has_revenue else f"전체 {click_label}",
        "unit": second_unit, "series": second_series}))

    # ── section 4 / 5: 상위 5개 소재 일별 CTR / ROAS(매출 없음: 클릭)
    s4 = section_data("s4")
    s5 = section_data("s5")
    series4 = load_series(payload, s4) if s4 is not None else None
    series5 = load_series(payload, s5) if s5 is not None else None
    top4 = (series4 or {}).get("top5") or {}
    top5_ = (series5 or {}).get("top5") or {}
    names = (s4 or {}).get("names") or (s5 or {}).get("names") or []

    if s4 is not None and names and top4.get("ctr_series"):
        status["s4"] = "ok"
        if (series4 or {}).get("dates"):
            dates = series4["dates"]
        s4_series = top4["ctr_series"]
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_series = []

    if s5 is not None and names and top5_.get(second_key):
        status["s5"] = "ok"
        if (series5 or {}).get("dates"):
            dates = series5["dates"]
        # 데이터 없는 날은 0 (끊기지 않게) — null이 와도 0으로 보정
        s5_series = [[(v if v is not None else 0) for v in row] for row in top5_[second_key]]
        html = html.replace("__S5_TITLE__", S5_TITLE[has_revenue])
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)
        s5_series = []

    html = html.replace("__S45_LABELS_JSON__", kit.js_json(labels_plain(dates)))
    html = html.replace("__S45_NAMES_JSON__", kit.js_json(names))
    html = html.replace("__S4_CTR_SERIES_JSON__", kit.js_json(s4_series))
    html = html.replace("__S5_JSON__", kit.js_json({"unit": second_unit, "series": s5_series}))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", esc(payload["title"]))
    html = html.replace("__REPORT_DATE_LABEL__", f"{target.year}년 {target.month}월 {target.day}일 기준")

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_BULLETS_HTML__",
        "__S3_LABELS_JSON__", "__S3_CTR_SERIES_JSON__", "__S3B_", "__S45_LABELS_JSON__",
        "__S45_NAMES_JSON__", "__S4_CTR_SERIES_JSON__", "__S5_JSON__", "__S5_TITLE__",
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

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path), "sections": status,
               "mode": {"has_revenue": has_revenue}}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
