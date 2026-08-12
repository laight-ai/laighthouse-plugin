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
  "out": "~/Downloads/laighthouse-reports/브리즘_creative-detailed_2026-05-15.html",  # 필수
  "title": "브리즘 소재 보고서",                                                      # 필수
  "target_date": "2026-05-15",                                                       # 필수 (기준일)
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)

  "s1": {                    # 최우수 소재 — 각 배열은 1·2위 순, 최대 2개 (2위 없으면 1개만)
    "roas": [ {"name": "소재명", "value": 812.3, "thumbnail_url": "https://..."},
              {"name": "소재명2", "value": 623.4, "thumbnail_url": null} ],
    "ctr":  [ ...같은 형식... ]
    # value는 % 스케일 숫자(소수 1자리로 포맷). thumbnail_url이 null/없으면 이미지 셀 비움.
    # 2위 없으면 배열에 1개만 — 2위 칸은 "-"로, 이미지 셀은 비워서 렌더링된다.
  },
  "s2": { "executive_summary": "문장1\n문장2\n⚠ 주의 문장..." },  # \n 구분, ⚠ 시작 줄은 주황색
  "s3": {                    # 일별 CTR — 광고비 상위 5개 소재 (section-3에서 선정)
    "names": ["표시이름1", ...],          # 광고비 내림차순, ad_name 중복 시 "ad_name (asset_group)"
    "ctr_series": [[7개 값, 없는 날은 null], ...],   # names와 같은 순서
    "labels": ["7/9", ...]               # 선택 — 생략하면 target_date 기준 M/D 7개 자동 생성
  },
  "s4": {                    # 일별 ROAS — s3와 같은 소재·순서 (names/labels는 s3 것을 재사용)
    "roas_series": [[7개 값], ...]       # 매출 매칭 실패/광고비 0인 날은 0 (null이 와도 0으로 보정)
  },
  "s5": {                    # 소재 단위 누적 성과 표 — 조인이 끝난 소재별 원본 수치 (포맷 금지)
    "rows": [ { "media": "Meta Ads", "campaign": "...", "asset_group": "...", "ad_name": "...",
                "impression": 12345, "click": 67, "cost": 89012,
                "revenue": 345678,      # airbridge 미매칭 소재는 null (0과 다르다 — 0은 매칭됐는데 매출 0)
                "reservation": 3 } ]    # airbridge 미매칭 소재는 null
  }                          # (파일 경로로 넘기려면 "rows_file": "/tmp/s5.json" — rows 배열이 든 JSON)
    # CTR/CPA/ROAS 계산, ₩·%·콤마 포맷, 광고비 내림차순 정렬, <tr> HTML·검색 텍스트 생성은 빌더가 한다.
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- s4는 s3의 names/labels를 공유한다 — s3 없이 s4만 넘기면 s4도 placeholder가 된다.
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...}}
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

PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'

# section-1 이미지 셀 내용 — 로드 실패 시 링크로 자동 전환 (마크업은 섹션 스펙 그대로)
S1_IMG_TMPL = (
    '<img style="width:100%; max-width:220px; height:180px; border-radius:8px; '
    'object-fit:cover; display:block; margin:0 auto;"\n'
    '               src="{url}" alt="{name} 썸네일"\n'
    '               onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'inline\';">\n'
    '          <a href="{url}" target="_blank" style="display:none; color:#2563eb; '
    'text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>'
)

# section-5 행 템플릿 — 식별열은 안 잘림 원칙(고정폭+break-word), 지표열은 nowrap (섹션 스펙 그대로)
S5_TR_TMPL = (
    '<tr>'
    '<td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:center; white-space:nowrap;">{media}</td>'
    '<td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4;">{campaign}</td>'
    '<td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4;">{asset_group}</td>'
    '<td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4;">{ad_name}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{impression}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{click}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{ctr}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{cost}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{revenue}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{reservation}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{cpa}</td>'
    '<td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{roas}</td>'
    '</tr>'
)


def esc(v):
    return html_mod.escape(str(v if v is not None else ""), quote=True)


def fmt_won(v):
    return f"₩{round(v):,}"


def fmt_int(v):
    return f"{round(v):,}"


def fmt_pct1(v):
    return f"{v:.1f}%"


def fmt_pct2(v):
    return f"{v:.2f}%"


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
    """단순 M/D 문자열 7개 (기준일-6일 → 기준일 순) — 요일 없음(daily-detailed와 다름)."""
    return [f"{d.month}/{d.day}" for d in (target - timedelta(days=6 - i) for i in range(7))]


def build_summary_items(text):
    items = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
        items.append(f"<li{style}>{line}</li>")
    return "\n      ".join(items)


def s1_slots(entries, label):
    """랭킹 배열(최대 2개) → (name, metric, img_html) × 2. 2위 없으면 '-'와 빈 이미지 셀."""
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
            metric = f"{label}: {esc(v)}"
        else:
            metric = f"{label}: {fmt_pct1(v)}"
        url = e.get("thumbnail_url")
        img = S1_IMG_TMPL.format(url=esc(url), name=name) if url else ""
        out.append((name, metric, img))
    return out


def build_s5_rows(rows):
    """조인이 끝난 소재별 원본 수치 → 광고비 내림차순 정렬 + 파생지표/포맷 + <tr> HTML."""
    rows = sorted(rows, key=lambda r: r.get("cost") or 0, reverse=True)
    out = []
    for r in rows:
        imp = r.get("impression") or 0
        clk = r.get("click") or 0
        cost = r.get("cost") or 0
        rev = r.get("revenue")          # None = airbridge 미매칭 (0과 구분)
        res = r.get("reservation")      # None = airbridge 미매칭
        ctr = fmt_pct2(clk / imp * 100) if imp > 0 else "N/A"
        revenue_s = fmt_won(rev) if rev is not None else "-"
        reservation_s = fmt_int(res) if res is not None else "-"
        cpa_s = fmt_won(cost / res) if res else "-"
        roas_s = fmt_pct1(rev / cost * 100) if (rev is not None and cost > 0) else "-"
        html = S5_TR_TMPL.format(
            media=esc(r.get("media", "")), campaign=esc(r.get("campaign", "")),
            asset_group=esc(r.get("asset_group", "")), ad_name=esc(r.get("ad_name", "")),
            impression=fmt_int(imp), click=fmt_int(clk), ctr=ctr, cost=fmt_won(cost),
            revenue=revenue_s, reservation=reservation_s, cpa=cpa_s, roas=roas_s)
        search = " ".join(str(r.get(k, "") or "") for k in
                          ("media", "campaign", "asset_group", "ad_name")).lower()
        out.append({"search": search, "html": html})
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

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1 (최우수 소재 카드 ×2)
    s1 = section_data("s1")
    if s1 and (s1.get("roas") or s1.get("ctr")):
        status["s1"] = "ok"
        for kind, label in (("roas", "ROAS"), ("ctr", "CTR")):
            slots = s1_slots(s1.get(kind), label)
            for rank, (name, metric, img) in enumerate(slots, start=1):
                prefix = f"__S1_{kind.upper()}_{rank}_"
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
    labels = (s3 or {}).get("labels") or build_labels(target)

    if s3 and names and s3.get("ctr_series"):
        status["s3"] = "ok"
        ctr_series = s3["ctr_series"]
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        ctr_series = []

    if s4 and names and s4.get("roas_series"):
        status["s4"] = "ok"
        # 매출 매칭 실패/광고비 0인 날은 0 — null이 와도 스펙대로 0으로 보정
        roas_series = [[(v if v is not None else 0) for v in row] for row in s4["roas_series"]]
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        roas_series = []

    if status["s3"] == "placeholder" and status["s4"] == "placeholder":
        names, labels = [], []
    html = html.replace("__S34_LABELS_JSON__", js_json(labels))
    html = html.replace("__S34_NAMES_JSON__", js_json(names))
    html = html.replace("__S3_CTR_SERIES_JSON__", js_json(ctr_series))
    html = html.replace("__S4_ROAS_SERIES_JSON__", js_json(roas_series))

    # ── section 5
    rows = load_rows(section_data("s5"))
    if rows is not None:
        status["s5"] = "ok"
        s5_rows = build_s5_rows(rows)
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)
        s5_rows = []
    html = html.replace("__S5_ROWS_JSON__", js_json(s5_rows))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 {target.day}일 기준")

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_ITEMS_HTML__",
        "__S34_LABELS_JSON__", "__S34_NAMES_JSON__", "__S3_CTR_SERIES_JSON__",
        "__S4_ROAS_SERIES_JSON__", "__S5_ROWS_JSON__",
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

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path), "sections": status},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
