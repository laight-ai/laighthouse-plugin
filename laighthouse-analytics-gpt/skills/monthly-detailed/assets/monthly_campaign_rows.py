#!/usr/bin/env python3
"""monthly-detailed section-5 전용: 캠페인 성과 비교(M-1 vs M0) 조인·파생지표·변화율·정렬·필터·
<tr> HTML 생성.

이미 검증된 asset 스크립트다 — 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로
MCP 응답 JSON을 받아 stdout으로 완성된 행 배열만 낸다. 중간 파일을 만들지 않는다(파이프로만
입출력).

`daily-detailed/assets/dxd_table_rows.py`(D-1 vs D-0, 날짜 단위)와 계산 로직은 거의 동일하지만,
이 스킬은 월 단위(M-1 vs M0) 비교이고 비교 불가 시 규칙이 다르다 —
`monthly-detailed-section-5-campaign-performance.md`의 스펙을 그대로 따른다:
  - M-1 값이 없거나(캠페인 자체가 그 달에 없음) 0이어서 비교가 불가능하면, 변화량 자리에
    "(-)"를 화살표/색 없이 회색으로 표시한다 (daily처럼 변화량 칸 자체를 비워두지 않는다).
  - 필터 기준은 M0 광고비 `threshold` 이하 제외 (기본 300000, daily는 10000).

⚠️ **`get_ad_performance`는 마크다운 표가 아니라 JSON 봉투를 반환한다** — `{"source": "elt",
"tenant": ..., "time_grain": "month", "dimensions": [...], "metrics": [...], "row_count": N,
"rows": [...]}`. month grain의 각 행에는 `month`("YYYY-MM")와 요청한 차원 키(영문: `media`/
`campaign_id`/`campaign_name`), **테넌트별 지표 키**가 들어있다 — 매출/전환이 행 안에 함께
오므로 별도 조인이 없다. 원본을 손으로 옮겨 적거나 파싱용 스크립트를 새로 만들지 않는다 —
아래 입력으로 원본 문자열/파일 경로를 그대로 넘기면 이 스크립트가 직접 파싱한다.

입력 (stdin, JSON):

(A) **응답이 캡처 훅 스텁(`[laighthouse-capture-hook] ... 저장됨: <경로>`)으로 온 경우 최우선**
    — 캡처 파일을 Read로 열어 내용을 옮기지 말고 경로만 넘긴다(스크립트가 파일을 직접 읽는다.
    `{"result": ...}` JSON 래퍼로 저장된 파일도 자동 언래핑):
{
  "m1_month": "YYYY-MM",
  "m0_month": "YYYY-MM",
  "threshold": 300000,                # M0 광고비 <= threshold 인 행 제외 (기본 300000, currency 단위)
  "currency": "₩",                    # 금액 접두 기호 (기본 "₩")
  "json_files": [ "<스텁에 적힌 저장 경로>" ]
}

(B) 원본 JSON 봉투 문자열을 그대로 넘길 때 (응답 문자열을 파싱·가공·선별 없이 그대로 —
    "주요 행만" 손으로 골라 옮기면 임계값 초과 행이 누락될 위험이 있으므로 절대 하지 않는다):
{
  "m1_month": "...", "m0_month": "...",
  "json": [ "<get_ad_performance 응답 원본 문자열>" ]
}

(C) 이미 파싱된 행 객체로 넘길 때:
{
  "m1_month": "...", "m0_month": "...",
  "rows": [ ... ]    # 봉투의 rows 배열 그대로
}
`json`과 `json_files`를 섞어 써도 된다 — 내용을 합쳐서 처리한다.

`metric_keys` — 역할(cost/impression/click/revenue/선택 conversion) → 실제 지표 키
(`shared/references/generic-report-pattern.md` 3절). 빌더(`build_report.py`)에 넘기는 것과
**같은 맵**을 넘긴다. 생략하면 봉투의 `metrics`(또는 rows의 키)에서 패턴의 후보 목록으로
자동 해석하고, cost/impression/click/revenue 중 하나라도 못 정하면 명확한 에러를 낸다.
`conversion`을 못 정하면 전환·CPA 컬럼을 생략한다:
{
  "metric_keys": {"cost": "광고비", "impression": "노출", "click": "클릭",
                  "revenue": "매출_AB", "conversion": "예약완료_AB"}
}

출력 (stdout, JSON): [{"search": "매체 캠페인 (소문자)", "html": "<tr>...</tr>"}, ...]
M0 광고비 내림차순, threshold 이하 제외, HTML까지 완성된 상태 — 출력을 파일로 저장해
build_report.py의 `s5.rows_file`에 경로로 넘기면 된다. 매체 라벨은 행의 `media` 값
그대로(`null`이면 "Organic").

사용 예 (단 한 번의 Bash 호출 안에서 따옴표 있는 heredoc으로 — echo나 파일 저장 후 재실행 X):
  python3 assets/monthly_campaign_rows.py <<'PYEOF' > /tmp/s5_rows.json
  {"m1_month":"2026-06","m0_month":"2026-07","json_files":["<스텁 경로>"]}
  PYEOF
"""
import sys
import json
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 역할별 지표 키 후보(순서대로 정확 일치) — generic-report-pattern.md 3절
ROLE_CANDIDATES = {
    "cost": ["광고비", "cost", "spend"],
    "impression": ["노출", "impressions", "impression"],
    "click": ["클릭", "clicks", "click"],
    "revenue": ["매출_AB", "매출", "revenue"],
    "conversion": ["예약완료_AB", "예약완료", "purchases", "conversions", "전환"],
}
REQUIRED_ROLES = ["cost", "impression", "click", "revenue"]
DIMENSION_KEYS = {"date", "month", "media", "source", "campaign_id", "campaign_name",
                  "ad_group_id", "ad_group_name", "ad_id", "ad_name", "ad_type"}
ORGANIC_LABEL = "Organic"

CURRENCY = "₩"


def unwrap_json_result(text):
    """Cowork(Claude Desktop) 캡처 훅이 저장한 파일은 `{"result": "<본문>"}` JSON 래퍼일 수
    있다 — 래퍼면 벗기고, 아니면 그대로 돌려준다."""
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


def parse_envelope(text):
    obj = json.loads(unwrap_json_result(text))
    if isinstance(obj, list):
        return obj, None
    if not isinstance(obj, dict) or not isinstance(obj.get("rows"), list):
        raise SystemExit("get_ad_performance JSON 봉투가 아님 — rows 배열이 없다")
    return obj["rows"], obj.get("metrics")


def resolve_metric_keys(payload, envelope_metrics, rows):
    """역할 → 지표 키. 명시 override 우선, 나머지는 후보 목록으로 자동 해석.
    conversion은 선택(못 정하면 None → 전환/CPA 컬럼 생략)."""
    metric_names = list(envelope_metrics or [])
    if not metric_names:
        seen = set()
        for r in rows:
            for k in r.keys():
                if k not in DIMENSION_KEYS and k not in seen:
                    seen.add(k)
                    metric_names.append(k)
    override = payload.get("metric_keys") or {}
    keys = {}
    for role, candidates in ROLE_CANDIDATES.items():
        if override.get(role):
            keys[role] = override[role]
            continue
        keys[role] = next((c for c in candidates if c in metric_names), None)
    bad = [keys[r] for r in keys if keys[r] and metric_names and keys[r] not in metric_names]
    if bad:
        raise SystemExit(f"지표 키 {bad}가 응답 metrics {metric_names}에 없음 — metric_keys를 바로잡아라")
    unresolved = [r for r in REQUIRED_ROLES if not keys[r]]
    if unresolved:
        raise SystemExit(
            f"역할 {unresolved}의 지표 키를 응답 metrics {metric_names}에서 정할 수 없음 — "
            f"metric_keys로 넘겨라")
    return keys


# 각 지표의 색상 규칙: True면 "증가=빨강(긍정)", False면 "감소=빨강(긍정)" (CPA만 False)
POSITIVE_ON_INCREASE = {
    "cost": True,
    "ctr": True,
    "conversion": True,
    "cpa": False,
    "revenue": True,
    "roas": True,
}


def metric_order(has_conversion):
    order = [("cost", "%"), ("ctr", "%p")]
    if has_conversion:
        order += [("conversion", "%"), ("cpa", "%")]
    return order + [("revenue", "%"), ("roas", "%p")]


def fmt_won(v):
    return f"{CURRENCY}{round(v):,}"


def fmt_pct1(v):
    return f"{v:.1f}%"


def media_label(row):
    """매체 라벨은 `media` 값 그대로(접미사·번역 없음). null/빈 값은 Organic."""
    media = row.get("media")
    return str(media) if media not in (None, "") else ORGANIC_LABEL


def sum_rows(rows, mk):
    """같은 (month, media, campaign) 키에 여러 행이 있으면 합산. 행이 없으면 None(그 달에
    캠페인 자체가 없음)."""
    if not rows:
        return None
    s = {
        "cost": sum(r.get(mk["cost"]) or 0 for r in rows),
        "impression": sum(r.get(mk["impression"]) or 0 for r in rows),
        "click": sum(r.get(mk["click"]) or 0 for r in rows),
        "revenue": sum(r.get(mk["revenue"]) or 0 for r in rows),
    }
    if mk.get("conversion"):
        s["conversion"] = sum(r.get(mk["conversion"]) or 0 for r in rows)
    return s


def compute_month(s, order):
    """s는 sum_rows 결과 또는 None(그 달에 캠페인 자체가 없음 → 전부 '-')."""
    if s is None:
        raw = {k: None for k, _ in order}
        disp = {k: "-" for k, _ in order}
        return raw, disp

    cost = s["cost"]
    impression = s["impression"]
    click = s["click"]
    revenue = s["revenue"]

    ctr = click / impression * 100 if impression else None
    roas = revenue / cost * 100 if cost else None

    raw = {"cost": cost, "ctr": ctr, "revenue": revenue, "roas": roas}
    disp = {
        "cost": fmt_won(cost),
        "ctr": fmt_pct1(ctr) if ctr is not None else "N/A",
        "revenue": fmt_won(revenue),
        "roas": fmt_pct1(roas) if roas is not None else "N/A",
    }
    if "conversion" in s:
        conversion = s["conversion"]
        cpa = cost / conversion if conversion else None
        raw["conversion"] = conversion
        raw["cpa"] = cpa
        disp["conversion"] = str(int(conversion))
        disp["cpa"] = fmt_won(cpa) if cpa is not None else "N/A"
    return raw, disp


def delta_relative(m0, m1):
    """% 변화 (광고비/전환/CPA/매출): m0 없거나 m1이 없거나 0이면 비교 불가(None)."""
    if m0 is None or m1 in (None, 0):
        return None
    return (m0 - m1) / m1 * 100


def delta_point(m0, m1):
    """%p 변화 (CTR/ROAS): m0 또는 m1이 None이면 비교 불가(None). 0은 유효한 값."""
    if m0 is None or m1 is None:
        return None
    return m0 - m1


DELTA_FN = {
    "cost": delta_relative,
    "ctr": delta_point,
    "conversion": delta_relative,
    "cpa": delta_relative,
    "revenue": delta_relative,
    "roas": delta_point,
}


def arrow_color(delta, metric_key, digits=1):
    """(화살표, 표시텍스트(부호 포함, 단위 제외), 색상) — delta가 None이면 비교 불가(호출부에서
    "(-)" 처리)."""
    if delta is None:
        return None
    rounded = round(delta, digits)
    if rounded == 0:
        return ("", f"{rounded:.{digits}f}", "#1e293b")
    arrow = "▲" if delta > 0 else "▼"
    positive_on_increase = POSITIVE_ON_INCREASE[metric_key]
    is_good = (delta > 0) == positive_on_increase
    color = "#dc2626" if is_good else "#2563eb"
    sign = "+" if delta > 0 else ""
    return (arrow, f"{sign}{rounded:.{digits}f}", color)


def delta_html(delta_tuple, suffix):
    """delta_tuple이 None이면 비교 자체가 불가능한 경우 — 섹션 스펙대로 '(-)'를 회색으로
    표시한다(daily처럼 칸을 비우지 않는다)."""
    if delta_tuple is None:
        return (
            '\n            <div style="font-size:10.5px; text-align:center; color:#94a3b8; '
            'line-height:1.3; margin-top:3px;">(-)</div>'
        )
    arrow, text, color = delta_tuple
    return (
        f'\n            <div style="font-size:10.5px; text-align:center; color:{color}; '
        f'line-height:1.3; margin-top:3px;">({arrow} {text}{suffix})</div>'
    )


def build_row_html(media_label, campaign, cells, order):
    id_html = (
        f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{media_label}</td>\n'
        f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{campaign}</td>'
    )

    metric_html_parts = []
    for metric_key, suffix in order:
        m1_val, m0_val, delta = cells[metric_key]
        last = metric_key == "roas"
        border = "" if last else " border-right:1px solid #e2e8f0;"
        metric_html_parts.append(
            f'<td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_val}</td>\n'
            f'          <td style="white-space:nowrap; text-align:center;{border} padding-top:10px; padding-bottom:10px; line-height:1.3;">\n'
            f'            <div style="line-height:1.3;">{m0_val}</div>{delta_html(delta, suffix)}\n'
            f"          </td>"
        )

    return "<tr>\n          " + id_html + "\n          " + "\n          ".join(metric_html_parts) + "\n        </tr>"


def main():
    global CURRENCY
    payload = json.load(sys.stdin)
    m1_month = payload["m1_month"]
    m0_month = payload["m0_month"]
    threshold = payload.get("threshold", 300000)
    CURRENCY = payload.get("currency") or CURRENCY

    rows = list(payload.get("rows") or [])
    envelope_metrics = None
    texts = payload.get("json", [])
    if isinstance(texts, str):
        texts = [texts]
    texts = list(texts)
    files = payload.get("json_files", [])
    if isinstance(files, str):
        files = [files]
    for path in files:
        with open(path, encoding="utf-8") as f:
            texts.append(f.read())
    for text in texts:
        env_rows, env_metrics = parse_envelope(text)
        rows.extend(env_rows)
        envelope_metrics = envelope_metrics or env_metrics

    mk = resolve_metric_keys(payload, envelope_metrics, rows)
    order = metric_order(bool(mk.get("conversion")))

    idx = {}
    for r in rows:
        key = (r.get("month"), media_label(r), r.get("campaign_name") or "")
        idx.setdefault(key, []).append(r)

    # M0에 캠페인 행이 존재하는 (media, campaign) 키만 후보로 삼는다 — M0에 없으면(M-1에만
    # 있던 캠페인) 필터 대상에서 자연히 제외된다.
    m0_keys = {(media, campaign) for (month, media, campaign) in idx.keys() if month == m0_month}

    out = []
    for label, campaign in m0_keys:
        m0_sum = sum_rows(idx.get((m0_month, label, campaign)), mk)
        if m0_sum is None or m0_sum["cost"] <= threshold:
            continue

        m1_sum = sum_rows(idx.get((m1_month, label, campaign)), mk)

        m1_raw, m1_disp = compute_month(m1_sum, order)
        m0_raw, m0_disp = compute_month(m0_sum, order)

        cells = {}
        for metric_key, _suffix in order:
            delta = DELTA_FN[metric_key](m0_raw[metric_key], m1_raw[metric_key])
            cells[metric_key] = (m1_disp[metric_key], m0_disp[metric_key], arrow_color(delta, metric_key))

        html = build_row_html(label, campaign, cells, order)
        out.append({
            "search": f"{label.lower()} {campaign.lower()}",
            "html": html,
            "_m0_cost": m0_sum["cost"],
        })

    out.sort(key=lambda r: r["_m0_cost"], reverse=True)
    for r in out:
        del r["_m0_cost"]

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
