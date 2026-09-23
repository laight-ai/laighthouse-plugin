"""보고서 공용 킷 — 모든 스킬 빌더가 공유하는 브랜드 비종속 렌더링 부품.

각 스킬의 `assets/build_report.py`·`assets/discover.py`가 import 해서 쓴다(모델이 직접 import
하지 않는다). 찾는 위치: `<스킬>/shared/assets`(ChatGPT 번들) → `<플러그인>/shared/assets`.

부품 (모드 분기는 전부 여기 한 곳에 있다 — generic-report-pattern.md 3·7절):
- `resolve_roles`         — 디스커버리 봉투 → media_list/has_organic/metric_keys/currency
- `Modes`                 — metric_keys/has_organic → has_revenue/has_conversion/has_organic
- 포맷터                   — fmt_money / fmt_count / fmt_pct / fmt_metric(값, 단위)
- `s1_grid_html`          — 목표 달성 카드 3장 (매출 있음: 소진율/매출 달성률/ROAS,
                             매출 없음: 소진율/노출·클릭/CTR·CPC)
- `perf_chart_spec`       — 광고 성과 혼합 차트 스펙 (매출 있음: 광고비·매출 막대 + ROAS 선,
                             매출 없음: 클릭 막대 + CTR 선, 광고비·노출·CPC는 툴팁)
- `media_trend_spec`      — 매체별 매출(없으면 클릭) 누적 막대 스펙 (Organic은 있을 때만)
- `compare_thead_html`/`compare_rows_html` — 매체 성과 비교 표(기준 기간 vs 비교 기간) <thead>/<tbody>
- `build_tree`            — 매체→캠페인→광고그룹→광고 계층 표 데이터 (ELT 봉투 → 트리 JSON)
- `inline_assets`         — 템플릿의 __REPORT_KIT_JS__ / __REPORT_KIT_CSS__ 치환
"""
import json
import os

KIT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 모드 ─────────────────────────────────────────────────────────────────────


class Modes:
    """실행당 한 번 정해지는 보고서 모드.

    - has_revenue: metric_keys에 revenue 역할이 있으면 True. False면 매출·ROAS 자리를
      노출·클릭·CTR(·CPC)로 대체한다.
    - has_organic: 디스커버리에 media=null 행이 있었으면 True. Organic 행/계열/서술을 켠다.
      매출이 없으면 Organic(광고비 없이 매출만 귀속되는 행)은 보여줄 값이 없으므로 강제로 끈다.
    - has_conversion: conversion 역할이 있으면 True(전환·CPA 컬럼 표시).
    """

    def __init__(self, metric_keys, has_organic=False):
        self.metric_keys = dict(metric_keys or {})
        self.has_revenue = bool(self.metric_keys.get("revenue"))
        self.has_conversion = bool(self.metric_keys.get("conversion"))
        self.has_organic = bool(has_organic) and self.has_revenue

    def label(self, role):
        return self.metric_keys.get(role) or DEFAULT_LABELS[role]


DEFAULT_LABELS = {"cost": "광고비", "impression": "노출", "click": "클릭",
                  "revenue": "매출", "conversion": "전환"}

# ── 디스커버리: 매체 목록·지표 역할 해석 (generic-report-pattern.md 2·3절) ──────────

# 역할별 후보 (대소문자 무시). 완전 일치 → 없으면 접두 일치("<후보>_…").
ROLE_CANDIDATES = {
    "cost": ["광고비", "cost", "spend", "spending"],
    "impression": ["노출", "impression", "impressions", "imps"],
    "click": ["클릭", "click", "clicks"],
    "revenue": ["매출", "revenue"],
    "conversion": ["전환", "conversion", "conversions", "구매", "구매수", "purchase", "purchases"],
}
REQUIRED_ROLES = ("cost", "impression", "click")


def _suffix(key, base):
    """'매출_AB' 와 후보 '매출' → '_AB'."""
    return key[len(base):] if key.lower().startswith(base.lower()) else None


def _resolve_role(role, metrics, prefer_suffix=None):
    """(키 | None, 모호 후보 리스트). 완전 일치 우선, 없으면 '<후보>_' 접두 일치."""
    lower = {m.lower(): m for m in metrics}
    for cand in ROLE_CANDIDATES[role]:
        if cand.lower() in lower:
            return lower[cand.lower()], []
    for cand in ROLE_CANDIDATES[role]:
        hits = [m for m in metrics if m.lower().startswith(cand.lower() + "_")]
        if not hits:
            continue
        if len(hits) == 1:
            return hits[0], []
        if prefer_suffix:
            same = [h for h in hits if _suffix(h, cand) == prefer_suffix]
            if len(same) == 1:
                return same[0], []
        return None, hits
    return None, []


def resolve_roles(envelope):
    """metrics 생략·group_by ["media"]·time_grain "total" 디스커버리 봉투 → 실행 설정.

    반환: {"media_list": [...], "has_organic": bool, "metric_keys": {...}, "metric_names": [...],
           "currency": str, "missing": [필수 역할], "ambiguous": {역할: [후보...]}, "has_revenue": bool,
           "sources_of": {매체: [source...]}  ← group_by에 "source"가 함께 있을 때만}
    - 필수 역할(cost/impression/click)이 missing이면 사용자에게 한 번에 묻는다.
    - ambiguous(접두 일치 후보가 여럿)는 사용자에게 한 번에 묻는다(conversion은 묻지 않고 생략).
    - revenue를 못 찾으면(모호하지 않은 한) 매출 없음 모드다 — 묻지 않는다.
    """
    metrics = list(envelope.get("metrics") or [])
    rows = envelope.get("rows") or []
    dim = "media" if "media" in (envelope.get("dimensions") or []) else "source"
    media_list, has_organic = [], False
    with_source = dim == "media" and "source" in (envelope.get("dimensions") or [])
    sources_of = {}
    for r in rows:
        v = r.get(dim)
        if v is None:
            has_organic = True
            continue
        if v not in media_list:
            media_list.append(v)
        if with_source and r.get("source") is not None:
            lst = sources_of.setdefault(v, [])
            if r["source"] not in lst:
                lst.append(r["source"])
    keys, ambiguous = {}, {}
    for role in ("cost", "impression", "click", "revenue"):
        key, hits = _resolve_role(role, metrics)
        if key:
            keys[role] = key
        elif hits:
            ambiguous[role] = hits
    rev_suffix = None
    if keys.get("revenue"):
        for cand in ROLE_CANDIDATES["revenue"]:
            rev_suffix = _suffix(keys["revenue"], cand)
            if rev_suffix is not None:
                break
    conv, _ = _resolve_role("conversion", metrics, prefer_suffix=rev_suffix or None)
    if conv:
        keys["conversion"] = conv
    units = envelope.get("metric_units") or {}
    currency = units.get(keys.get("cost")) if keys.get("cost") else None
    out = {"media_list": media_list, "has_organic": has_organic, "metric_keys": keys,
            "metric_names": metrics, "currency": currency or "₩",
            "missing": [r for r in REQUIRED_ROLES if r not in keys and r not in ambiguous],
            "ambiguous": ambiguous, "has_revenue": "revenue" in keys}
    if with_source:
        out["sources_of"] = sources_of   # group_by ["media","source"] 디스커버리일 때만 (소재 스킬)
    return out

# ── 포맷터 ───────────────────────────────────────────────────────────────────

# 소수점 없는 통화(원화·엔화). 그 외 통화는 소수 2자리.
ZERO_DECIMAL_CURRENCIES = {"₩", "¥", "원", "KRW", "JPY"}
# 뒤에 붙는 통화 표기
SUFFIX_CURRENCIES = {"원", "KRW", "USD", "JPY", "EUR"}
CURRENCY_UNITS = {"₩", "$", "€", "£", "¥", "원", "KRW", "USD", "JPY", "EUR"}


def is_currency_unit(unit):
    return unit in CURRENCY_UNITS


def fmt_money(v, currency="₩"):
    if v is None:
        return "-"
    if currency in ZERO_DECIMAL_CURRENCIES:
        body = f"{round(v):,}"
    else:
        body = f"{v:,.2f}"
    return f"{body}{currency}" if currency in SUFFIX_CURRENCIES else f"{currency}{body}"


def fmt_count(v):
    return "-" if v is None else f"{round(v):,}"


def fmt_pct(v, digits=1):
    return "-" if v is None else f"{v:.{digits}f}%"


def fmt_metric(v, unit, currency="₩"):
    """ELT metric_units 값으로 임의 지표 표시. 단위를 지표명으로 추측하지 않는다."""
    if v is None:
        return "-"
    if unit == "%":
        return f"{v:,.2f}%"
    if is_currency_unit(unit):
        return fmt_money(v, unit)
    body = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"
    return f"{body}{unit}" if unit else body


def ratio(num, den, scale=100.0):
    if num is None or den in (None, 0):
        return None
    return num / den * scale


def discover_main(stdin, stdout):
    """스킬 assets/discover.py 의 본체. stdin: 디스커버리 봉투 원문 JSON 그대로, 또는
    {"json_files": [...]} / {"json": "..."} (캡처 스텁 경로). stdout: resolve_roles 결과 JSON."""
    payload = json.load(stdin)
    if isinstance(payload, dict) and ("json_files" in payload or "json" in payload) and "rows" not in payload:
        envs = load_envelopes(payload)
        payload = envs[0] if envs else {}
    json.dump(resolve_roles(payload), stdout, ensure_ascii=False)


# ── section-1: 목표 달성 카드 ─────────────────────────────────────────────────

S1_FOOTNOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
               "* 목표(예산·매출)는 목표가 등록된 매체 기준 합계이며, 실적은 전체 광고 매체 기준입니다. "
               "목표가 없는 매체가 있으면 소진율·달성률이 실제보다 높게 보일 수 있습니다.</p>")
S1_NO_TARGET_NOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
                     "* 이번 달 등록된 목표(예산·매출)가 없어 목표 대비 항목은 N/A로 표시됩니다.</p>")

_CARD = ('<div style="padding:20px;{border} text-align:center;">\n'
         '        <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{title}</div>\n'
         '        <div style="font-size:28px; font-weight:700; color:#1e293b; margin-bottom:12px;">{big}</div>\n'
         '        <div style="display:flex; justify-content:center; gap:16px; font-size:12px;">\n'
         '          <div><div style="color:#94a3b8;">{a_label}</div><div style="font-weight:600;">{a}</div></div>\n'
         '          <div style="width:1px; background:#e2e8f0;"></div>\n'
         '          <div><div style="color:#94a3b8;">{b_label}</div><div style="font-weight:600;">{b}</div></div>\n'
         '        </div>\n'
         '      </div>')
_CARD_SOLO = ('<div style="padding:20px; text-align:center; display:flex; flex-direction:column; '
              'justify-content:center; align-items:center;">\n'
              '        <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{title}</div>\n'
              '        <div style="font-size:28px; font-weight:700; color:#1e293b; margin-bottom:10px;">{big}</div>\n'
              '        <div style="font-size:12px; color:#94a3b8;">{sub_label}</div>\n'
              '        <div style="font-size:12px; font-weight:600; color:#64748b;">{sub}</div>\n'
              '      </div>')
_BORDER_R = " border-right:1px solid #e2e8f0;"


def _na(v, fmt):
    if v is None:
        return "N/A"
    if isinstance(v, str):
        return v
    return fmt(v)


def s1_grid_html(s1, modes, currency="₩"):
    """목표 달성 카드 3장의 HTML(그리드 안쪽). s1은 원본 숫자(없으면 null).

    공통 필드: 목표_예산, 소진액 (소진율은 없으면 여기서 계산)
    매출 있음: 목표_매출, 기간_매출 (매출_달성률·목표_ROAS·실제_ROAS는 없으면 계산)
    매출 없음: 기간_노출, 기간_클릭 (CTR·CPC는 없으면 계산)
    """
    money = lambda v: fmt_money(v, currency)  # noqa: E731
    budget, spent = s1.get("목표_예산"), s1.get("소진액")
    burn = s1.get("소진율", ratio(spent, budget))
    cards = [_CARD.format(border=_BORDER_R, title="기간 예산대비 소진율", big=_na(burn, fmt_pct),
                          a_label="목표 예산", a=_na(budget, money),
                          b_label="소진액", b=_na(spent, money))]
    if modes.has_revenue:
        tgt_rev, rev = s1.get("목표_매출"), s1.get("기간_매출")
        achv = s1.get("매출_달성률", ratio(rev, tgt_rev))
        roas = s1.get("실제_ROAS", ratio(rev, spent))
        tgt_roas = s1.get("목표_ROAS", ratio(tgt_rev, budget))
        cards.append(_CARD.format(border=_BORDER_R, title="기간 목표 매출 대비 달성률",
                                  big=_na(achv, fmt_pct), a_label="목표 매출", a=_na(tgt_rev, money),
                                  b_label="기간 매출", b=_na(rev, money)))
        cards.append(_CARD_SOLO.format(title="실제 ROAS", big=_na(roas, fmt_pct),
                                       sub_label="목표 ROAS", sub=_na(tgt_roas, fmt_pct)))
    else:
        imp, clk = s1.get("기간_노출"), s1.get("기간_클릭")
        ctr = s1.get("CTR", ratio(clk, imp))
        cpc = s1.get("CPC", ratio(spent, clk, 1.0))
        cards.append(_CARD_SOLO.format(title=f"기간 {modes.label('click')}", big=_na(clk, fmt_count),
                                       sub_label=f"기간 {modes.label('impression')}",
                                       sub=_na(imp, fmt_count)).replace(
            'style="padding:20px;', f'style="padding:20px;{_BORDER_R}', 1))
        cards.append(_CARD_SOLO.format(title="CTR", big=_na(ctr, lambda v: fmt_pct(v, 2)),
                                       sub_label="CPC", sub=_na(cpc, money)))
    return "\n\n      ".join(cards)


def s1_footnote_html(s1):
    """목표가 하나라도 있으면 목표 범위 각주(항상), 전혀 없으면 목표 없음 각주."""
    if s1.get("목표_예산") is None and s1.get("목표_매출") is None:
        return S1_NO_TARGET_NOTE
    return S1_FOOTNOTE


# ── 차트 스펙 (report_kit.js 의 LHKit.mixedChart / LHKit.stackChart 가 그린다) ─────

# dataviz 분류형 팔레트(검증된 순서) — 매체 순서대로 고정 배정, 순환하지 않는다.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                 "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
ORGANIC_COLOR = "#a8a29e"   # Organic — 광고 매체가 아닌 계열이므로 분류형 슬롯을 쓰지 않는다
OTHER_COLOR = "#cbd5e1"     # 9번째 이후 매체를 묶은 "그 외 매체"(차트 전용)
COST_COLOR = "#93c5fd"
REVENUE_COLOR = "#94a3b8"
LINE_COLOR = "#ef4444"
CLICK_COLOR = "#93c5fd"


def _sum_arrays(arrays, n):
    out = [0] * n
    for arr in arrays:
        for i, v in enumerate(arr[:n]):
            out[i] += v or 0
    return out


def perf_chart_spec(labels, s, modes):
    """광고 성과 혼합 차트 스펙. s는 역할별 원자 값 배열(labels와 같은 길이).

    매출 있음: s["cost"], s["revenue"] → 광고비·매출 막대(좌축 통화) + ROAS 선(우축 %)
    매출 없음: s["cost"], s["impression"], s["click"] → 클릭 막대(좌축 개수) + CTR 선(우축 %).
               광고비·노출·CPC는 툴팁에 함께 보여준다(세 가지 스케일을 한 차트 축에 올리지 않음).
    비율은 원자 값 합으로 계산한다 — 서버 비율 지표를 합산하지 않는다.
    """
    n = len(labels)
    cost = list(s.get("cost") or s.get("ad_cost") or [None] * n)
    if modes.has_revenue:
        rev = list(s.get("revenue") or [None] * n)
        roas = [ratio(r, c) for r, c in zip(rev, cost)]
        return {"labels": labels, "left": "money", "right": "pct",
                "bars": [{"label": modes.label("cost"), "data": cost, "color": COST_COLOR},
                         {"label": modes.label("revenue"), "data": rev, "color": REVENUE_COLOR}],
                "line": {"label": "ROAS", "data": roas, "color": LINE_COLOR},
                "extra": []}
    imp = list(s.get("impression") or [None] * n)
    clk = list(s.get("click") or [None] * n)
    ctr = [ratio(c, i) for c, i in zip(clk, imp)]
    cpc = [ratio(c, k, 1.0) for c, k in zip(cost, clk)]
    return {"labels": labels, "left": "count", "right": "pct",
            "bars": [{"label": modes.label("click"), "data": clk, "color": CLICK_COLOR}],
            "line": {"label": "CTR", "data": ctr, "color": LINE_COLOR},
            "extra": [{"label": modes.label("cost"), "data": cost, "unit": "money"},
                      {"label": modes.label("impression"), "data": imp, "unit": "count"},
                      {"label": "CPC", "data": cpc, "unit": "money"}]}


def media_trend_spec(labels, series, modes, max_series=8):
    """매체별 추이 누적 막대 스펙.

    series: [{"name": <media 값 그대로 또는 "Organic">, "values": [...]}] — 매출 있음이면
    revenue 역할 값, 매출 없음이면 click 역할 값. 입력 순서(디스커버리 순서)로 색을 고정 배정한다.
    Organic은 has_organic일 때만 남기고 회색으로 맨 위에 쌓는다. 광고 매체가 max_series를 넘으면
    넘친 매체를 "그 외 매체" 하나로 묶는다(차트 전용 — 표에는 매체가 전부 나온다).
    """
    n = len(labels)
    media, organic = [], None
    for item in series or []:
        if item.get("name") == "Organic":
            organic = item
        else:
            media.append(item)
    out = []
    head, tail = media[:max_series], media[max_series:]
    if tail:
        head = media[:max_series - 1]
        tail = media[max_series - 1:]
    for i, item in enumerate(head):
        out.append({"label": item["name"], "data": list(item.get("values") or [])[:n],
                    "color": SERIES_COLORS[i]})
    if tail:
        out.append({"label": f"그 외 매체 {len(tail)}개",
                    "data": _sum_arrays([t.get("values") or [] for t in tail], n),
                    "color": OTHER_COLOR})
    if organic is not None and modes.has_organic:
        out.append({"label": "Organic", "data": list(organic.get("values") or [])[:n],
                    "color": ORGANIC_COLOR})
    unit = "money" if modes.has_revenue else "count"
    metric = modes.label("revenue") if modes.has_revenue else modes.label("click")
    return {"labels": labels, "unit": unit, "metric": metric, "series": out}


def media_trend_title(modes):
    return f"매체별 {modes.label('revenue') if modes.has_revenue else modes.label('click')} 추이"


def media_trend_footnote(modes):
    if modes.has_organic:
        return ('<p style="font-size:11px; color:#64748b; margin-top:8px;">'
                "* 'Organic'은 광고비 없이 귀속된 매출이며, 막대 전체 높이는 광고 매체와 Organic을 합친 매출입니다.</p>")
    return ""


# ── 매체 성과 비교 표 ──────────────────────────────────────────────────────────

UP_COLOR = "#dc2626"     # 증가 = 빨강
DOWN_COLOR = "#2563eb"   # 감소 = 파랑
ZERO_COLOR = "#1e293b"
_TH_GROUP = ('<th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; '
             'padding-top:8px; padding-bottom:8px; vertical-align:middle;{border}">{label}</th>')
_TH_DATE = ('<th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; '
            'padding-top:8px; padding-bottom:8px; vertical-align:middle;{border}">{label}</th>')
_TH_BORDER = " border-right:1px solid #e2e8f0;"


def delta_html(cur, base, suffix):
    """비교 기간 값 아래 변화량 div. %p는 차이, 그 외는 상대 %. 기준 값이 없으면 표시 안 함."""
    if cur is None or base is None:
        return ""
    if suffix == "%p":
        raw = cur - base
    else:
        if base == 0:
            return ""
        raw = (cur - base) / base * 100
    shown = round(raw, 1)
    if shown == 0:
        inner, color = f"(0.0{suffix})", ZERO_COLOR
    else:
        arrow = "▲" if raw > 0 else "▼"
        color = UP_COLOR if raw > 0 else DOWN_COLOR
        inner = f"({arrow} {shown:+.1f}{suffix})"
    return f'\n            <div style="font-size:10.5px; text-align:center; color:{color};">{inner}</div>'


def _num(d, key):
    v = (d or {}).get(key)
    return v if isinstance(v, (int, float)) else None


def compare_columns(modes):
    """(라벨, 값 함수, 포맷 종류, 변화 접미사) 목록. 값 함수는 역할 원본 dict → 숫자."""
    cols = [(modes.label("cost"), lambda d: _num(d, "cost"), "money", "%")]
    if modes.has_revenue:
        cols.append((modes.label("revenue"), lambda d: _num(d, "revenue"), "money", "%"))
        if modes.has_conversion:
            cols.append((modes.label("conversion"), lambda d: _num(d, "conversion"), "count", "%"))
        cols.append(("ROAS", lambda d: ratio(_num(d, "revenue"), _num(d, "cost")), "pct", "%p"))
    else:
        cols += [(modes.label("impression"), lambda d: _num(d, "impression"), "count", "%"),
                 (modes.label("click"), lambda d: _num(d, "click"), "count", "%"),
                 ("CTR", lambda d: ratio(_num(d, "click"), _num(d, "impression")), "pct2", "%p"),
                 ("CPC", lambda d: ratio(_num(d, "cost"), _num(d, "click"), 1.0), "money", "%")]
        if modes.has_conversion:
            cols.append((modes.label("conversion"), lambda d: _num(d, "conversion"), "count", "%"))
    return cols


def compare_thead_html(modes, base_label, cur_label, name_label="매체"):
    cols = compare_columns(modes)
    row1 = ['<th rowspan="2" style="white-space:nowrap; text-align:center; vertical-align:middle;'
            f'{_TH_BORDER}">{name_label}</th>']
    row2 = []
    for i, (label, _, _, _) in enumerate(cols):
        last = i == len(cols) - 1
        row1.append(_TH_GROUP.format(label=label, border="" if last else _TH_BORDER))
        row2.append(_TH_DATE.format(label=base_label, border=""))
        row2.append(_TH_DATE.format(label=cur_label, border="" if last else _TH_BORDER))
    sep = "\n            "
    return ("<tr>" + sep + sep.join(row1) + "\n          </tr>\n          <tr>" + sep
            + sep.join(row2) + "\n          </tr>")


def compare_rows_html(rows, modes, currency="₩", base_key="d1", cur_key="d0"):
    """행: [{"name", base_key: {역할: 원본}, cur_key: {...}}] — 입력 순서대로 렌더링.
    매출 없음 모드에서는 Organic 행을 뺀다(보여줄 광고 지표가 없다)."""
    cols = compare_columns(modes)
    fmts = {"money": lambda v: fmt_money(v, currency), "count": fmt_count,
            "pct": fmt_pct, "pct2": lambda v: fmt_pct(v, 2)}
    trs = []
    for r in rows or []:
        if r.get("name") == "Organic" and not modes.has_organic:
            continue
        base, cur = r.get(base_key) or {}, r.get(cur_key) or {}
        cells = [f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">'
                 f'{r.get("name", "")}</td>']
        for i, (_, fn, kind, suffix) in enumerate(cols):
            last = i == len(cols) - 1
            bv, cv = fn(base), fn(cur)
            f = fmts[kind]
            cells.append(f'<td style="white-space:nowrap; text-align:center;">{f(bv) if bv is not None else "-"}</td>')
            style = "white-space:nowrap; text-align:center;" + ("" if last else _TH_BORDER)
            delta = delta_html(cv, bv, suffix)
            val = f(cv) if cv is not None else "-"
            if delta:
                cells.append(f'<td style="{style}">\n            {val}{delta}\n          </td>')
            else:
                cells.append(f'<td style="{style}">{val}</td>')
        trs.append("<tr>\n          " + "\n          ".join(cells) + "\n        </tr>")
    return "\n        ".join(trs)


# ── 계층 표 (매체 → 캠페인 → 광고그룹 → 광고) ───────────────────────────────────

LEVEL_DIMS = ["media", "campaign_name", "ad_group_name", "ad_name"]
LEVEL_LABELS = ["매체", "캠페인", "광고그룹", "광고"]
UNSET_LABEL = "(미지정)"


def load_envelopes(section):
    """{"json_files": [경로...], "json": [봉투 문자열|dict ...]} → 봉투 dict 리스트.
    캡처 훅 스텁 경로와 원본 문자열을 섞어 넘겨도 된다."""
    envs = []
    for path in section.get("json_files") or []:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            envs.append(json.load(f))
    raw = section.get("json")
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raw = [raw]
    for item in raw:
        envs.append(json.loads(item) if isinstance(item, str) else item)
    return envs


def _period_of(row):
    return str(row.get("date") or row.get("month") or "")


def _level_of(env):
    dims = env.get("dimensions") or []
    present = [d for d in LEVEL_DIMS if d in dims]
    if present != LEVEL_DIMS[:len(present)] or not present:
        raise SystemExit(f"계층 표 봉투의 group_by가 {LEVEL_DIMS}의 접두가 아니다: {dims}")
    return len(present)


def _label(level_idx, value):
    if value is None or value == "":
        return "Organic" if level_idx == 0 else UNSET_LABEL
    return str(value)


def _metric_order(metrics, metric_keys):
    """역할 지표(광고비→노출→클릭→전환→매출) 먼저, 나머지는 봉투 순서."""
    role_first = [metric_keys.get(r) for r in ("cost", "impression", "click", "conversion", "revenue")]
    ordered = [m for m in role_first if m and m in metrics]
    return ordered + [m for m in metrics if m not in ordered]


def build_tree(envelopes, base_period, cur_period, metric_keys, has_organic=True):
    """레벨별 get_ad_performance 봉투들(같은 두 기간, group_by가 LEVEL_DIMS의 접두)을
    트리 JSON으로 만든다. 각 레벨 값은 그 레벨 group_by로 서버가 계산한 값을 그대로 쓴다
    (비율 지표를 하위 행에서 합산하지 않기 위해 레벨마다 따로 조회한다).

    반환: {"levels": [...], "metrics": [{"key", "unit"}], "base": 기간, "cur": 기간,
           "nodes": [[name, cur_values, base_values, children], ...]}
    값 배열은 metrics 순서, 없으면 null. 하위 레벨 봉투가 없으면 그 레벨 이하는 비어 있다.
    """
    base_period, cur_period = str(base_period), str(cur_period)
    metrics, units = [], {}
    by_level = {}
    for env in envelopes:
        lvl = _level_of(env)
        for m in env.get("metrics") or []:
            if m not in metrics:
                metrics.append(m)
        units.update({k: v for k, v in (env.get("metric_units") or {}).items() if k not in units or v})
        by_level.setdefault(lvl, []).append(env)
    if not by_level:
        raise SystemExit("계층 표 입력 봉투가 없다")
    metrics = _metric_order(metrics, metric_keys or {})
    depth = max(by_level)

    # path(tuple) → {"cur": {m: v}, "base": {m: v}}
    values = {}
    for lvl, envs in by_level.items():
        dims = LEVEL_DIMS[:lvl]
        for env in envs:
            for row in env.get("rows") or []:
                period = _period_of(row)
                if period.startswith(cur_period):
                    slot = "cur"
                elif period.startswith(base_period):
                    slot = "base"
                else:
                    continue
                path = tuple(_label(i, row.get(d)) for i, d in enumerate(dims))
                if path[0] == "Organic" and not has_organic:
                    continue
                bucket = values.setdefault(path, {"cur": {}, "base": {}})[slot]
                for m in metrics:
                    v = row.get(m)
                    if not isinstance(v, (int, float)):
                        continue
                    if m in bucket and units.get(m) != "%":
                        bucket[m] += v   # 같은 이름이 중복된 행(드묾)은 가산 지표만 합친다
                    elif m in bucket:
                        bucket[m] = None
                    else:
                        bucket[m] = v

    # 조상 경로 보장 (하위 레벨에만 있는 경로도 트리에 걸리게)
    for path in list(values):
        for k in range(1, len(path)):
            values.setdefault(path[:k], {"cur": {}, "base": {}})

    cost_key = (metric_keys or {}).get("cost")

    def arr(d):
        return [d.get(m) for m in metrics]

    children = {}
    for path in values:
        children.setdefault(path[:-1], []).append(path)

    def sort_key(path):
        v = values[path]["cur"].get(cost_key) if cost_key else None
        return (-(v or 0), path[-1])

    def node(path):
        kids = sorted(children.get(path, []), key=sort_key)
        return [path[-1], arr(values[path]["cur"]), arr(values[path]["base"]), [node(k) for k in kids]]

    roots = sorted(children.get((), []), key=sort_key)
    return {"levels": LEVEL_LABELS[:depth],
            "metrics": [{"key": m, "unit": units.get(m)} for m in metrics],
            "cost": cost_key, "base": base_period, "cur": cur_period,
            "nodes": [node(p) for p in roots]}


def tree_json(tree):
    return js_json(tree)


# ── 공통 ─────────────────────────────────────────────────────────────────────


def js_json(value):
    """<script> 안에 삽입할 JSON — </script> 조기 종료 방지."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def inline_assets(html):
    """템플릿의 __REPORT_KIT_CSS__ / __REPORT_KIT_JS__ 를 킷 파일 내용으로 치환."""
    for token, name in (("__REPORT_KIT_CSS__", "report_kit.css"), ("__REPORT_KIT_JS__", "report_kit.js")):
        if token in html:
            with open(os.path.join(KIT_DIR, name), encoding="utf-8") as f:
                html = html.replace(token, f.read())
    return html
