#!/usr/bin/env python3
"""mtd-detailed 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~7 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`와 공용 킷(`shared/assets/report_kit.*`)을 인라인해서
**최종 HTML 한 파일을 한 번의 호출로** 만든다. 모델은 HTML을 한 글자도 타이핑하지 않는다 —
아래 값 JSON만 heredoc으로 넘기면 된다. 모드 분기(매출 있음/없음, Organic 있음/없음)와 계층 표
생성은 전부 공용 킷이 한다(`shared/references/generic-report-pattern.md` 7·8절).

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_mtd-detailed_2026-05-15.html",  # 필수
  "title": "{브랜드명} MTD 보고서",                                                  # 필수
  "target_date": "2026-05-15",                                                   # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
  "metric_keys": {...},      # discover.py 출력 그대로 (revenue 없으면 매출 없음 모드)
  "has_organic": true,       # discover.py 출력 그대로
  "currency": "₩",           # discover.py 출력 그대로

  "s1": {"목표_예산": .., "소진액": .., "목표_매출": .., "기간_매출": .., "기간_노출": .., "기간_클릭": ..},
                             # shared/references/target-achievement.md — 원본 숫자, 없으면 null
  "s2": {"executive_summary": "문장1\n문장2\n⚠ 주의 문장..."},   # \n 구분, ⚠ 시작 줄은 주황색
  "s3": {                    # 월별 광고 성과 — 배열 6개(5개월 전 → 당월), 광고 매체 행(media non-null) 합
    "cost": [..], "revenue": [..],           # 매출 있음
    "impression": [..], "click": [..],       # 매출 없음 (cost도 함께 — 툴팁·CPC용)
    "labels": [...],                         # 선택 — 생략하면 "YY년 M월"(당월 " (진행 중)") 자동 생성
    "zero_fill_note": "..."                  # 선택 — 생략하면 막대가 전부 0인 월을 찾아 빌더가 각주 생성
  },
  "s4": {                    # 매체별 일별 추이 — 배열은 월초~target_date 일수만큼(하루도 빠짐없이)
    "series": [{"name": "<media 값 그대로>", "values": [...]}, ...,
               {"name": "Organic", "values": [...]}],  # 매출 있음: revenue 값 / 매출 없음: click 값
    "labels": [["5/1","(금)"], ...],         # 선택 — 생략하면 [M/D, (요일)] 자동 생성
    "promotions": [{"title": "여름 세일", "date_begin": "2026-05-01", "date_end": "2026-05-11"}]
                                             # list_promotions 원본 그대로 — 인덱스·클램프·라벨은 빌더가
  },
  "s5": {"campaign_analysis": "인트로 문단\n\n캠페인명 (매체명)\n분석 문장..."},
                             # \n\n 블록 구분 — 첫 블록은 <p> 인트로, 이후 블록은 첫 줄 <h4> + 나머지 <p>
  "s6": {                    # 매체별 예산·소진 — 디스커버리된 매체마다 한 행, 디스커버리 순서
    "rows": [{"name": "<media 값 그대로>",
              "월_예산": 50000000, "목표_매출": null,        # 매체별 get_target_progress_v2 target (없으면 null)
              "cost": .., "revenue": .., "impression": .., "click": ..}]  # get_ad_performance 실적 (역할 원본)
  },                         # 소진율·달성률·목표 ROAS·ROAS·CTR·CPC는 빌더가 계산, 컬럼은 모드별
  "s7": {                    # 계층 표 — 레벨별 get_ad_performance 응답(month grain, 전월 동기+당월, metrics 생략)
    "json_files": ["<캡처 스텁 경로>", ...],   # 스텁으로 온 응답
    "json": ["<원본 봉투 문자열>", ...]          # 원본으로 온 응답 (섞어도 된다)
  }
}

- s1~s7 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "mode": {...}, "sections": {...}, "tree_nodes": N}
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
# 스킬 폴더 assets에 chart.umd.min.js가 없으면 자매 스킬 mtd-summary의 것을 복사해 온다.
CHART_JS_FALLBACK = os.path.normpath(os.path.join(
    ASSETS_DIR, "..", "..", "mtd-summary", "assets", "chart.umd.min.js"))


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
S3_NO_REVENUE_NOTE = ("* 매출 지표가 없는 브랜드라 클릭·CTR 기준으로 표시합니다. 광고비·노출·CPC는 "
                      "막대에 마우스를 올리면 확인할 수 있습니다.")

TH = '<th style="text-align:center;">{label}</th>'
TH_BORDER = '<th style="text-align:center; border-right:1px solid #e2e8f0;">{label}</th>'
TD = "<td>{v}</td>"
TD_BORDER = '<td style="border-right:1px solid #e2e8f0;">{v}</td>'


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


def zero_fill_note(labels, spec):
    """막대 값이 전부 0(또는 없음)인 월을 찾아 각주 문구를 만든다. 없으면 빈 문자열."""
    zero = [str(lab).replace(" (진행 중)", "") for i, lab in enumerate(labels)
            if all(not (b["data"][i] if i < len(b["data"]) else None) for b in spec["bars"])]
    if not zero:
        return ""
    return f"* {', '.join(zero)}은 데이터가 수집되지 않아 0으로 표시되었습니다."


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


# ── section 6: 매체별 예산·소진 ───────────────────────────────────────────────

def _num(r, *keys):
    for k in keys:
        v = r.get(k)
        if isinstance(v, (int, float)):
            return v
    return None


def _target(v):
    """목표 값은 0/없음이면 목표 없음(null)."""
    return v if isinstance(v, (int, float)) and v > 0 else None


def build_s6(rows, modes, currency):
    """(<thead> 행, <tbody> 행들). 컬럼은 모드별 — 매출 있음: 예산·소진 + 목표 매출·광고 매출·
    달성률·목표 ROAS·ROAS / 매출 없음: 예산·소진 + 노출·클릭·CTR·CPC. 행은 받은 순서 그대로."""
    money = lambda v: kit.fmt_money(v, currency)  # noqa: E731

    def show(v, fmt):
        return "-" if v is None else fmt(v)

    head = [("매체", True), ("월 예산", False), ("소진액", False), ("예산 소진율", True)]
    if modes.has_revenue:
        head += [("목표 매출", False), (f"광고 {modes.label('revenue')}", False), ("매출 달성률", True),
                 ("목표 ROAS", False), ("ROAS", False)]
    else:
        head += [(modes.label("impression"), False), (modes.label("click"), False),
                 ("CTR", False), ("CPC", False)]
    thead = "<tr>\n        " + "".join(
        (TH_BORDER if border else TH).format(label=label) for label, border in head) + "\n      </tr>"

    trs = []
    for r in rows:
        budget = _target(_num(r, "월_예산"))
        cost = _num(r, "cost", "소진액")
        cells = [TD_BORDER.format(v=r.get("name") or ""),
                 TD.format(v=show(budget, money)), TD.format(v=show(cost, money)),
                 TD_BORDER.format(v=show(_num(r, "예산_소진율") if _num(r, "예산_소진율") is not None
                                         else kit.ratio(cost, budget), kit.fmt_pct))]
        if modes.has_revenue:
            tgt_rev = _target(_num(r, "목표_매출"))
            rev = _num(r, "revenue", "광고_매출")
            tgt_roas = _num(r, "목표_ROAS")
            if tgt_roas is None:
                tgt_roas = kit.ratio(tgt_rev, budget)
            cells += [TD.format(v=show(tgt_rev, money)), TD.format(v=show(rev, money)),
                      TD_BORDER.format(v=show(kit.ratio(rev, tgt_rev), kit.fmt_pct)),
                      TD.format(v=show(tgt_roas, kit.fmt_pct)),
                      TD.format(v=show(kit.ratio(rev, cost), kit.fmt_pct))]
        else:
            imp, clk = _num(r, "impression"), _num(r, "click")
            cells += [TD.format(v=show(imp, kit.fmt_count)), TD.format(v=show(clk, kit.fmt_count)),
                      TD.format(v=show(kit.ratio(clk, imp), lambda v: kit.fmt_pct(v, 2))),
                      TD.format(v=show(kit.ratio(cost, clk, 1.0), money))]
        trs.append("<tr>\n        " + "".join(cells) + "\n      </tr>")
    return thead, "\n      ".join(trs)


def tree_note(target, m1_m):
    return (f"* 각 값 아래 증감은 전월 동기({m1_m}월 1일~{target.day}일) 대비 {target.month}월 1일~"
            f"{target.day}일 변화입니다(비율 지표는 %p). 시작은 매체 단위이며 ▶를 눌러 캠페인·광고그룹·"
            "광고로 펼칠 수 있습니다. 지표 헤더를 누르면 정렬되고(기본: 광고비 내림차순), '지표 선택'으로 "
            "표시할 컬럼을 고를 수 있습니다.")


# ── main ────────────────────────────────────────────────────────────────────

def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    m1_y, m1_m = month_shift(target.year, target.month, -1)
    skeleton = bool(payload.get("skeleton"))
    currency = payload.get("currency") or "₩"
    metric_keys = payload.get("metric_keys") or {}
    modes = kit.Modes(metric_keys, payload.get("has_organic"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}
    tree_nodes = 0

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1
    s1 = section_data("s1")
    if s1:
        status["s1"] = "ok"
        html = html.replace("__S1_GRID_HTML__", kit.s1_grid_html(s1, modes, currency))
        html = html.replace("__S1_FOOTNOTE_HTML__", kit.s1_footnote_html(s1))
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
    if s3 and (s3.get("cost") or s3.get("ad_cost") or s3.get("click")):
        status["s3"] = "ok"
        labels = s3.get("labels") or build_month_labels(target)
        s3_spec = kit.perf_chart_spec(labels, s3, modes)
        notes = [f"* {target.year % 100}년 {target.month}월은 기준일({target.month}/{target.day})까지의 "
                 "데이터만 포함합니다."]
        zf = s3["zero_fill_note"] if "zero_fill_note" in s3 else zero_fill_note(labels, s3_spec)
        if zf:
            notes.append(zf)
        if not modes.has_revenue:
            notes.append(S3_NO_REVENUE_NOTE)
        html = html.replace("__S3_FOOTNOTE_HTML__", "\n      ".join(f"<div>{n}</div>" for n in notes))
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_spec = None
    html = html.replace("__S3_CHART_SPEC_JSON__", kit.js_json(s3_spec))

    # ── section 4 (매체별 일별 추이 누적 막대)
    s4 = section_data("s4")
    if s4 and s4.get("series"):
        status["s4"] = "ok"
        s4_spec = kit.media_trend_spec(s4.get("labels") or build_day_labels(target), s4["series"], modes)
        s4_promos = build_promotions(s4.get("promotions"), target)
        html = html.replace("__S4_TITLE__", kit.media_trend_title(modes))
        html = html.replace("__S4_FOOTNOTE_HTML__", kit.media_trend_footnote(modes))
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_spec, s4_promos = None, []
    html = html.replace("__S4_CHART_SPEC_JSON__", kit.js_json(s4_spec))
    html = html.replace("__S4_PROMOTIONS_JSON__", kit.js_json(s4_promos))

    # ── section 5
    s5 = section_data("s5")
    if s5 and s5.get("campaign_analysis"):
        status["s5"] = "ok"
        html = html.replace("__S5_BLOCKS_HTML__", build_analysis_blocks(s5["campaign_analysis"]))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

    # ── section 6 (매체별 예산·소진 — 컬럼은 모드별)
    s6 = section_data("s6")
    if s6 and s6.get("rows"):
        status["s6"] = "ok"
        thead, rows_html = build_s6(s6["rows"], modes, currency)
        html = html.replace("__S6_THEAD_HTML__", thead)
        html = html.replace("__S6_ROWS_HTML__", rows_html)
    else:
        status["s6"] = "placeholder"
        html = swap_section(html, "s6", PLACEHOLDER_CARD)

    # ── section 7 (계층 표 — 전월 동기 vs 당월 MTD, month grain "YYYY-MM")
    s7 = section_data("s7")
    tree = None
    if s7 and (s7.get("json_files") or s7.get("json")):
        tree = kit.build_tree(kit.load_envelopes(s7), f"{m1_y:04d}-{m1_m:02d}",
                              f"{target.year:04d}-{target.month:02d}", metric_keys,
                              has_organic=modes.has_organic)
        if tree["nodes"]:
            status["s7"] = "ok"

            def count(nodes):
                return sum(1 + count(n[3]) for n in nodes)
            tree_nodes = count(tree["nodes"])
        else:
            tree = None
    if tree is None:
        status["s7"] = "placeholder"
        html = swap_section(html, "s7", PLACEHOLDER_CARD)
    html = html.replace("__S7_TREE_JSON__", kit.js_json(tree))
    html = html.replace("__S7_NOTE_JSON__", kit.js_json(tree_note(target, m1_m)))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__CURRENCY_JSON__", kit.js_json(currency))
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 1일 ~ {target.month}월 {target.day}일")
    html = (html.replace("__T_MM__", str(target.month)).replace("__T_DD__", str(target.day))
                .replace("__M1_MM__", str(m1_m)))

    # ── 치환 누락 검증 (인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__T_MM__", "__T_DD__", "__M1_MM__", "__CURRENCY",
        "__S1_", "__S2_", "__S3_", "__S4_", "__S5_", "__S6_", "__S7_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── 공용 킷·chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    html = kit.inline_assets(html)
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

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path),
               "mode": {"has_revenue": modes.has_revenue, "has_organic": modes.has_organic,
                        "has_conversion": modes.has_conversion},
               "sections": status, "tree_nodes": tree_nodes}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
