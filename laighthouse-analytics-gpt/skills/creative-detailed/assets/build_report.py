#!/usr/bin/env python3
"""creative-detailed 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_creative-detailed_{기준_일자}.html",  # 필수
  "title": "{브랜드명} 소재 보고서",                                                      # 필수
  "target_date": "YYYY-MM-DD",                                                       # 필수 (기준일)
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)
  "metric_keys": {           # 디스커버리(discover.py) 출력 그대로 — 역할 → 실제 지표 키
    "cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>",
    "revenue": "<revenue 키 — 있을 때만>",       # 없으면 매출 없음 모드 (generic-report-pattern.md 7절)
    "conversion": "<conversion 키 — 있을 때만>"  # 없으면 section-5의 전환·CPA 컬럼을 숨긴다
  },                         # section-5 <th> 라벨·section-1 클릭 라벨에 값 그대로 쓴다
  "currency": "<discover.py 출력의 currency>",   # 금액 표기 기호 (생략 시 공용 킷 기본값)

  "series_file": "/tmp/creative_series.json",  # creative_daily_series.py 출력 파일 경로 —
                                               # s3(top5.ctr_series)와 s4(top5.roas_series |
                                               # 매출 없음: top5.click_series)가 공유한다.
                                               # (파일 대신 "series": {...} 직접 전달도 허용)

  "s1": {                    # 최우수 소재 — 각 배열 1·2위 순 (2위 없으면 1개만)
    "roas":  [ {"name": "<ad_name>", "value": 812.3, "thumbnail_url": "https://..."} ],  # 매출 있음 모드
    "click": [ {"name": "<ad_name>", "value": 5321, "thumbnail_url": null} ],          # 매출 없음 모드
    "ctr":   [ ...같은 형식, value는 % 스케일... ]                                       # 두 모드 공통
  },
  "s2": { "executive_summary": "문장1\n문장2\n⚠ 주의 문장..." },  # \n 구분, ⚠ 시작 줄은 주황색
  "s3": { "names": ["표시이름1", ...] },  # 광고비 상위 5개 표시 이름(광고비 내림차순) — s4와 공유
  "s4": {},                  # 키가 존재하면 series의 top5.roas_series(매출 없음: click_series)로 렌더링
  "s5": {                    # 소재 단위 누적 성과 표 — total 응답 행의 원본 수치 (포맷 금지)
    "rows": [ { "media": "<chosen_media>", "campaign": "...", "asset_group": "...", "ad_name": "...",
                "impression": 12345, "click": 67, "cost": 89012,
                "revenue": 345678,      # 매출 있음 모드만. 값이 없는 소재는 null (0과 다르다)
                "conversion": 3 } ]     # metric_keys에 conversion이 있을 때만; 없는 소재는 null
  }                          # (파일 경로로 넘기려면 "rows_file": "/tmp/s5.json" — rows 배열이 든 JSON)
}

- 모드별 표시 (빌더가 고른다 — 모델은 역할 원본 수치만 넣는다):
  매출 있음 → section-1 "ROAS 최우수 소재", section-4 "일별 ROAS",
             section-5 노출·클릭·CTR·광고비·매출·(전환·CPA)·ROAS.
  매출 없음 → section-1 "클릭 최우수 소재", section-4 "일별 클릭",
             section-5 노출·클릭·CTR·광고비·CPC·(전환·CPA).
- CTR/CPC/CPA/ROAS 계산, 통화·%·콤마 포맷, 광고비 내림차순 정렬, <thead>/<tr> HTML·검색 텍스트는 빌더가 만든다.
- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- s4는 s3의 names를 공유한다 — s3 없이 s4만 넘기면 s4도 placeholder가 된다.
- 라벨: series의 dates(없으면 target_date 기준 7일)로 "M/D" 7개를 자동 생성한다.
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...},
                "mode": {"has_revenue": bool, "has_conversion": bool}}
"""
import html as html_mod
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
CHART_JS_FALLBACK = os.path.normpath(os.path.join(
    ASSETS_DIR, "..", "..", "daily-detailed", "assets", "chart.umd.min.js"))


def _load_kit():
    for cand in (os.path.join(ASSETS_DIR, "..", "shared", "assets"),          # ChatGPT 번들
                 os.path.join(ASSETS_DIR, "..", "..", "..", "shared", "assets")):  # 플러그인 루트
        if os.path.exists(os.path.join(cand, "report_kit.py")):
            sys.path.insert(0, os.path.normpath(cand))
            import report_kit
            return report_kit
    raise SystemExit("report_kit.py를 찾을 수 없다 (shared/assets)")


kit = _load_kit()

PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'

# 모드별 문구 (generic-report-pattern.md 7절 — 소재 보고서: 매출 있음 ROAS·CTR / 매출 없음 클릭·CTR)
S1_A_TITLE = {True: "ROAS 최우수 소재 (최근 7일 기준)", False: "클릭 최우수 소재 (최근 7일 기준)"}
S1_A_NOTE = {
    True: "*'매출/광고비'로 계산되며, 높을수록 소재에서 매출이 효율적으로 발생하고 있음을 의미합니다.",
    False: "*최근 7일 합산 클릭 수 기준이며, 많을수록 소재가 고객의 관심을 많이 끌었음을 의미합니다. "
           "단, 클릭 수는 광고비 규모에 비례하므로 CTR과 함께 보아야 합니다.",
}
S4_TITLE = {True: "최근 7일 일별 ROAS (광고비 상위 5개 소재)",
            False: "최근 7일 일별 클릭 (광고비 상위 5개 소재)"}

# section-1 이미지 셀 내용 — 로드 실패 시 링크로 자동 전환
S1_IMG_TMPL = (
    '<img style="width:100%; max-width:220px; height:180px; border-radius:8px; '
    'object-fit:cover; display:block; margin:0 auto;"\n'
    '               src="{url}" alt="{name} 썸네일"\n'
    '               onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'inline\';">\n'
    '          <a href="{url}" target="_blank" style="display:none; color:#2563eb; '
    'text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>'
)

# section-5 셀 템플릿 — 식별열은 안 잘림 원칙(고정폭+break-word), 지표열은 nowrap
S5_TD_ID = '<td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:center; white-space:nowrap;">{}</td>'
S5_TD_TEXT = ('<td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; '
              'overflow-wrap:break-word; line-height:1.4;">{}</td>')
S5_TD_NUM = '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{}</td>'

S5_TH = ('<th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; '
         'white-space:nowrap; width:{width}px;">{label}</th>')
S5_TH_TEXT = ('<th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; '
              'width:{width}px;">{label}</th>')
S5_ID_HEADERS = [("매체", 90, S5_TH), ("캠페인", 260, S5_TH_TEXT), ("광고그룹", 200, S5_TH_TEXT), ("광고", 200, S5_TH_TEXT)]


def esc(v):
    return html_mod.escape(str(v if v is not None else ""), quote=True)


def swap_section(html, key, replacement):
    begin = f"<!--SECTION:{key}:BEGIN-->"
    end = f"<!--SECTION:{key}:END-->"
    i = html.index(begin)
    j = html.index(end) + len(end)
    return html[:i] + replacement + html[j:]


def build_labels(target):
    """단순 M/D 문자열 7개 (기준일-6일 → 기준일 순) — 요일 없음."""
    return [f"{d.month}/{d.day}" for d in (target - timedelta(days=6 - i) for i in range(7))]


def labels_from_dates(dates):
    out = []
    for s in dates:
        d = date.fromisoformat(str(s)[:10])
        out.append(f"{d.month}/{d.day}")
    return out


def load_series(payload):
    if isinstance(payload.get("series"), dict):
        return payload["series"]
    path = payload.get("series_file")
    if path:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            return json.load(f)
    return None


def build_summary_items(text):
    items = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
        items.append(f"<li{style}>{line}</li>")
    return "\n      ".join(items)


def s1_slots(entries, label, kind):
    """랭킹 배열(최대 2개) → (name, metric, img_html) × 2. 2위 없으면 '-'와 빈 이미지 셀.
    kind: 'pct'(ROAS/CTR, % 소수 1자리) | 'count'(클릭 수)."""
    out = []
    entries = entries or []
    for i in range(2):
        e = entries[i] if i < len(entries) else None
        if not e:
            out.append(("-", "-", ""))
            continue
        name = esc(e.get("name", "-"))
        v = e.get("value")
        if v is None:
            metric = "-"
        elif isinstance(v, str):
            metric = f"{esc(label)}: {esc(v)}"
        else:
            metric = f"{esc(label)}: {kit.fmt_pct(v) if kind == 'pct' else kit.fmt_count(v)}"
        url = e.get("thumbnail_url")
        img = S1_IMG_TMPL.format(url=esc(url), name=name) if url else ""
        out.append((name, metric, img))
    return out


def s5_columns(modes):
    """모드별 지표 컬럼 라벨 — metric_keys 값 그대로."""
    return [label for label, _ in _s5_spec(modes, None)]


def _s5_spec(modes, currency):
    """[(라벨, 행 → 셀 문자열)] — 매출 있음: 노출·클릭·CTR·광고비·매출·(전환·CPA)·ROAS,
    매출 없음: 노출·클릭·CTR·광고비·CPC·(전환·CPA)."""
    money = lambda v: kit.fmt_money(v, currency)  # noqa: E731
    conv_label = modes.label("conversion") if modes.has_conversion else None

    def ctr(r):
        return kit.fmt_pct(r["click"] / r["impression"] * 100, 2) if r["impression"] > 0 else "N/A"

    spec = [
        (modes.label("impression"), lambda r: kit.fmt_count(r["impression"])),
        (modes.label("click"), lambda r: kit.fmt_count(r["click"])),
        ("CTR", ctr),
        (modes.label("cost"), lambda r: money(r["cost"])),
    ]
    if modes.has_revenue:
        spec.append((modes.label("revenue"),
                     lambda r: money(r["revenue"]) if r["revenue"] is not None else "-"))
    else:
        spec.append(("CPC", lambda r: money(r["cost"] / r["click"]) if r["click"] > 0 else "-"))
    if conv_label:
        spec += [
            (conv_label, lambda r: kit.fmt_count(r["conversion"]) if r["conversion"] is not None else "-"),
            (f"{conv_label} CPA", lambda r: money(r["cost"] / r["conversion"]) if r["conversion"] else "-"),
        ]
    if modes.has_revenue:
        spec.append(("ROAS", lambda r: kit.fmt_pct(r["revenue"] / r["cost"] * 100)
                     if (r["revenue"] is not None and r["cost"] > 0) else "-"))
    return spec


def build_s5_thead(modes):
    ths = [tmpl.format(label=label, width=width) for label, width, tmpl in S5_ID_HEADERS]
    ths += [S5_TH.format(label=esc(label), width=150) for label in s5_columns(modes)]
    return "\n            ".join(ths)


def build_s5_rows(rows, modes, currency):
    """소재별 원본 수치 → 광고비 내림차순 정렬 + 파생지표/포맷 + <tr> HTML (<thead>와 컬럼 수 일치)."""
    spec = _s5_spec(modes, currency)
    rows = sorted(rows, key=lambda r: r.get("cost") or 0, reverse=True)
    out = []
    for r in rows:
        v = {
            "impression": r.get("impression") or 0,
            "click": r.get("click") or 0,
            "cost": r.get("cost") or 0,
            "revenue": r.get("revenue"),        # None = 값 없음 (0과 구분)
            "conversion": r.get("conversion"),  # None = 값 없음
        }
        cells = [
            S5_TD_ID.format(esc(r.get("media", ""))),
            S5_TD_TEXT.format(esc(r.get("campaign", ""))),
            S5_TD_TEXT.format(esc(r.get("asset_group", ""))),
            S5_TD_TEXT.format(esc(r.get("ad_name", ""))),
        ] + [S5_TD_NUM.format(fn(v)) for _, fn in spec]
        search = " ".join(str(r.get(k, "") or "") for k in
                          ("media", "campaign", "asset_group", "ad_name")).lower()
        out.append({"search": search, "html": "<tr>" + "".join(cells) + "</tr>"})
    return out


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
    skeleton = bool(payload.get("skeleton"))
    modes = kit.Modes(payload.get("metric_keys") or {})
    has_revenue = modes.has_revenue
    currency = payload.get("currency") or "₩"

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    series = None if skeleton else (load_series(payload) or {})
    top5 = (series or {}).get("top5") or {}

    # ── section 1 (최우수 소재 카드 ×2 — 왼쪽: 매출 있음 ROAS / 매출 없음 클릭, 오른쪽: CTR)
    s1 = section_data("s1")
    a_key = "roas" if has_revenue else "click"
    if s1 and (s1.get(a_key) or s1.get("ctr")):
        status["s1"] = "ok"
        html = html.replace("__S1_A_TITLE__", S1_A_TITLE[has_revenue])
        html = html.replace("__S1_A_NOTE__", S1_A_NOTE[has_revenue])
        for prefix_kind, entries, label, kind in (
                ("A", s1.get(a_key), "ROAS" if has_revenue else modes.label("click"),
                 "pct" if has_revenue else "count"),
                ("CTR", s1.get("ctr"), "CTR", "pct")):
            for rank, (name, metric, img) in enumerate(s1_slots(entries, label, kind), start=1):
                prefix = f"__S1_{prefix_kind}_{rank}_"
                html = (html.replace(prefix + "NAME__", name)
                            .replace(prefix + "METRIC__", metric)
                            .replace(prefix + "IMG_HTML__", img))
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

    # ── section 3 / 4 (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한 JSON으로 치환 —
    #    placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    s4 = section_data("s4")
    names = (s3 or {}).get("names") or []
    dates = (series or {}).get("dates")
    labels = (s3 or {}).get("labels") or (labels_from_dates(dates) if dates else build_labels(target))
    second_key = "roas_series" if has_revenue else "click_series"

    ctr_series = (s3 or {}).get("ctr_series") or top5.get("ctr_series")
    if s3 is not None and names and ctr_series:
        status["s3"] = "ok"
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        ctr_series = []

    second = (s4 or {}).get(second_key) or top5.get(second_key)
    if s4 is not None and names and second:
        status["s4"] = "ok"
        # 데이터 없는 날은 0 — null이 와도 스펙대로 0으로 보정
        second = [[(v if v is not None else 0) for v in row] for row in second]
        html = html.replace("__S4_TITLE__", S4_TITLE[has_revenue])
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        second = []

    if status["s3"] == "placeholder" and status["s4"] == "placeholder":
        names, labels = [], []
    html = html.replace("__S34_LABELS_JSON__", kit.js_json(labels))
    html = html.replace("__S34_NAMES_JSON__", kit.js_json(names))
    html = html.replace("__S3_CTR_SERIES_JSON__", kit.js_json(ctr_series))
    html = html.replace("__S4_JSON__", kit.js_json({"unit": "%" if has_revenue else "",
                                                     "series": second}))

    # ── section 5
    rows = load_rows(section_data("s5"))
    if rows is not None:
        status["s5"] = "ok"
        s5_rows = build_s5_rows(rows, modes, currency)
        html = html.replace("__S5_THEAD_HTML__", build_s5_thead(modes))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)
        s5_rows = []
    html = html.replace("__S5_ROWS_JSON__", kit.js_json(s5_rows))
    html = html.replace("__S5_COLSPAN__", str(len(S5_ID_HEADERS) + len(s5_columns(modes))))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", esc(payload["title"]))
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 {target.day}일 기준")

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_ITEMS_HTML__",
        "__S34_LABELS_JSON__", "__S34_NAMES_JSON__", "__S3_CTR_SERIES_JSON__",
        "__S4_JSON__", "__S4_TITLE__", "__S5_THEAD_HTML__", "__S5_ROWS_JSON__", "__S5_COLSPAN__",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    if not os.path.exists(CHART_JS) and os.path.exists(CHART_JS_FALLBACK):
        shutil.copyfile(CHART_JS_FALLBACK, CHART_JS)
    with open(CHART_JS, encoding="utf-8") as f:
        html = html.replace("__CHART_JS_INLINE__", f.read())

    out_path = os.path.abspath(os.path.expanduser(payload["out"]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path), "sections": status,
               "mode": {"has_revenue": has_revenue, "has_conversion": modes.has_conversion}},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
