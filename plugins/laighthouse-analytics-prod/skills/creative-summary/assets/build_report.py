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
  "out": "~/Downloads/laighthouse-reports/브리즘_creative-summary_2026-05-15.html",  # 필수
  "title": "브리즘 Executive 소재 보고서",                                            # 필수
  "target_date": "2026-05-15",                                                       # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)

  "series_file": "/tmp/creative_series.json",  # creative_daily_series.py 출력 파일 경로 —
                                               # s3(overall)와 s4/5(top5)가 이 한 파일을 공유한다.
                                               # (파일 대신 "series": {...} 직접 전달도 허용)

  "s1": {                    # 최우수 소재 — roas/ctr 각각 1·2위 배열 (2위 없으면 1개만)
    "roas": [ {"name": "AD_...", "value": 388.1, "thumbnail_url": "https://..."},   # value 숫자면
              {"name": "AD_...", "value": 201.5, "thumbnail_url": null} ],          # % 소수1자리 포맷
    "ctr":  [ {"name": "AD_...", "value": 2.4, "thumbnail_url": "https://..."} ]    # 1개면 2위는 "-"
  },
  "s2": {                    # Executive Summary — 불릿 배열. tone이 점(●) 색을 정한다:
    "bullets": [             #   "good"(평균 대비 뚜렷한 고성과)=초록, "bad"(비효율/액션 필요)=빨강,
      {"text": "문장... <strong>388.1%</strong> ...", "tone": "good"},              #   "neutral"=회색-갈색
      {"text": "문장...", "tone": "bad"}
    ]                        # (문자열 배열/"executive_summary" 문자열도 허용 — 전부 neutral 처리)
  },
  "s3": {},                  # 키가 존재하면 series의 overall.ctr_series/roas_series로 렌더링
  "s4": { "names": ["소재 표시이름1", ...] },  # 상위 5개 표시 이름(광고비 내림차순) — top5.ctr_series 사용
  "s5": {}                   # names는 s4와 공유, top5.roas_series 사용
                             # (s3/s4/s5에 개별 "series_file"/"series"를 넣으면 그 섹션만 그걸 쓴다)
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 라벨: series 출력의 dates(없으면 target_date 기준 7일)로 빌더가 자동 생성 —
  section-3은 "M/D(요일)", section-4/5는 "M/D" 형식(원본 스펙 그대로).
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

DOT_COLORS = {"good": "#16a34a", "bad": "#dc2626", "neutral": "#78716c"}

# section-1 md의 이미지 셀 마크업 원본 그대로 (2위 없으면 이미지/링크를 렌더링하지 않는다).
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


def fmt_pct(v):
    """숫자면 % 소수점 1자리, 문자열이면 그대로, None이면 '-'."""
    if v is None:
        return "-"
    if isinstance(v, str):
        return v
    return f"{v:.1f}%"


def js_json(value):
    """<script> 안에 삽입할 JSON — </script> 조기 종료 방지."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


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


def s1_rank_tokens(html, prefix, ranks, metric_label):
    """prefix: 'S1_ROAS'|'S1_CTR', ranks: [{name,value,thumbnail_url}, ...] (0~2개)."""
    ranks = ranks or []
    for i in (0, 1):
        n = i + 1
        item = ranks[i] if i < len(ranks) else None
        if item:
            name = item.get("name") or "-"
            value = item.get("value")
            value_text = "-" if value is None else f"{metric_label}: {fmt_pct(value)}"
            url = item.get("thumbnail_url")
            img = IMG_CELL.format(url=url, name=name) if url else ""
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

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1: 최우수 소재
    s1 = section_data("s1")
    if s1 and (s1.get("roas") or s1.get("ctr")):
        status["s1"] = "ok"
        html = s1_rank_tokens(html, "S1_ROAS", s1.get("roas"), "ROAS")
        html = s1_rank_tokens(html, "S1_CTR", s1.get("ctr"), "CTR")
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

    # ── section 3: 전체 소재 CTR/ROAS (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한
    #    JSON으로 치환 — placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    series3 = load_series(payload, s3) if s3 is not None else None
    overall = (series3 or {}).get("overall") or {}
    if s3 is not None and overall.get("ctr_series"):
        status["s3"] = "ok"
        if series3.get("dates"):
            dates = series3["dates"]
        ctr_series = overall["ctr_series"]
        roas_series = overall.get("roas_series", [])
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        ctr_series, roas_series = [], []
    html = html.replace("__S3_LABELS_JSON__", js_json(labels_with_weekday(dates)))
    html = html.replace("__S3_CTR_SERIES_JSON__", js_json(ctr_series))
    html = html.replace("__S3_ROAS_SERIES_JSON__", js_json(roas_series))

    # ── section 4 / 5: 상위 5개 소재 일별 CTR/ROAS
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

    if s5 is not None and names and top5_.get("roas_series"):
        status["s5"] = "ok"
        if (series5 or {}).get("dates"):
            dates = series5["dates"]
        s5_series = top5_["roas_series"]
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)
        s5_series = []

    html = html.replace("__S45_LABELS_JSON__", js_json(labels_plain(dates)))
    html = html.replace("__S45_NAMES_JSON__", js_json(names))
    html = html.replace("__S4_CTR_SERIES_JSON__", js_json(s4_series))
    html = html.replace("__S5_ROAS_SERIES_JSON__", js_json(s5_series))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__REPORT_DATE_LABEL__", f"{target.year}년 {target.month}월 {target.day}일 기준")

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_BULLETS_HTML__",
        "__S3_LABELS_JSON__", "__S3_CTR_SERIES_JSON__", "__S3_ROAS_SERIES_JSON__",
        "__S45_LABELS_JSON__", "__S45_NAMES_JSON__", "__S4_CTR_SERIES_JSON__",
        "__S5_ROAS_SERIES_JSON__",
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
