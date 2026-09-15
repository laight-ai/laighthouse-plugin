#!/usr/bin/env python3
"""daily-detailed section-4/5 공용: D-1 vs D-0 조인·파생지표·정렬·필터·<tr> HTML 생성.

이미 검증된 asset 스크립트다 — 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로
MCP 응답 JSON을 받아 stdout으로 완성된 행 배열만 낸다. 중간 파일을 만들지 않는다(파이프로만
입출력).

⚠️ **`get_ad_performance`는 JSON 봉투를 반환한다** — `{"source": "elt", "tenant": ...,
"time_grain": "day", "dimensions": [...], "metrics": [...], "row_count": N, "rows": [...]}`.
각 행(row)에는 요청한 차원 키(영문: `date`/`media`/`campaign_name`/`ad_group_name`/`ad_name`
등)와 **테넌트별 지표 키**가 들어있다. 그 원본 문자열을 손으로 옮겨 적거나(전사 실수·행 누락
위험) 파싱용 스크립트를 새로 만들지 않는다 — 아래 입력 형태로 원본 문자열/파일 경로를
**그대로** 넘기면 이 스크립트가 직접 파싱한다.

입력 (stdin, JSON):

(A) **권장 — MCP 도구가 반환하는 원본 JSON 봉투 문자열을 그대로 넘길 때** (각 호출의 응답
    문자열을 파싱·가공 없이 그대로 배열에 담는다 — 호출이 몇 번이든(section-4는 1개,
    section-5는 매체 수만큼) 전부 이 배열 하나에 넣으면 스크립트가 각 봉투를 파싱해 이어붙인다):
{
  "level": "campaign" | "ad",       # section-4=campaign, section-5=ad
  "d1_date": "YYYY-MM-DD",
  "d0_date": "YYYY-MM-DD",
  "threshold": 10000,                 # D0 광고비 <= threshold 인 행 제외 (기본 10000, currency 단위)
  "currency": "₩",                    # 금액 접두 기호 (기본 "₩")
  "json": [ "<매체1 호출의 봉투 원본 문자열>", "<매체2 호출의 봉투 원본 문자열>", ... ]
}

(B) **플러그인 캡처 훅이 동작하는 호스트(Claude Code)에서 최우선** — MCP 응답이
    "[laighthouse-capture-hook] ... 저장됨: <경로>" 스텁으로 도착한 경우, 그 저장 경로들을
    그대로 넘긴다. 원본을 컨텍스트에 다시 타이핑할 필요가 전혀 없다(스크립트가 파일을 직접
    읽는다) — 이 형태가 가능한 상황에서 (A)처럼 원본 전문을 heredoc에 담는 것은 금지된
    낭비다:
{
  "level": "campaign" | "ad", "d1_date": "...", "d0_date": "...",
  "json_files": [ "<스텁에 적힌 저장 경로1>", "<경로2>", ... ]
}
`json`과 `json_files`를 섞어 써도 된다(예: 일부 응답만 훅에 캡처된 경우) — 두 배열의 내용을
합쳐서 처리한다.

(C) 이미 파싱된 행 객체 리스트로 넘길 때:
{
  "level": "campaign", "d1_date": "...", "d0_date": "...",
  "rows": [ ... ]    # 봉투의 rows 배열을 그대로 이어붙인 리스트
}

`metric_keys` — 역할(cost/impression/click/revenue/선택 conversion) → 실제 지표 키
(`shared/references/generic-report-pattern.md` 3절). 빌더(`build_report.py`)에 넘기는 것과
**같은 맵**을 넘긴다. 생략하면 봉투의 `metrics`(또는 rows의 키)에서 패턴의 후보 목록으로
자동 해석하고, cost/impression/click/revenue 중 하나라도 못 정하면 명확한 에러를 낸다.
`conversion`을 못 정하면 전환·CPA 컬럼을 생략한다:
{
  "metric_keys": {"cost": "광고비", "impression": "노출", "click": "클릭",
                  "revenue": "매출_AB", "conversion": "예약완료_AB"}
}

출력 (stdout, JSON): [{"search": "매체 캠페인 [광고그룹 광고] (소문자)", "html": "<tr>...</tr>"}, ...]
D0 광고비 내림차순, threshold 이하 제외, HTML까지 완성된 상태. 매체 라벨은 행의 `media` 값
그대로(`null`이면 "Organic").

사용 예 (단 한 번의 Bash 호출 안에서 따옴표 있는 heredoc으로 — echo나 파일 저장 후 재실행 X):
  python3 assets/dxd_table_rows.py <<'PYEOF'
  {"level":"campaign", "d1_date":"...", "d0_date":"...", "json_files":["<스텁에 적힌 경로>"]}
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
    있다 — 래퍼면 벗기고, 아니면 그대로 돌려준다. `get_ad_performance` 봉투 자체도 JSON이지만
    `result` 키가 없으므로 그대로 통과한다."""
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
    """`get_ad_performance`가 반환하는 JSON 봉투 문자열에서 (rows, metrics)를 꺼낸다."""
    obj = json.loads(unwrap_json_result(text))
    if isinstance(obj, list):
        return obj, None  # rows 배열만 온 경우도 방어적으로 허용
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


def calc_ctr(click, impression):
    if not impression:
        return None
    return click / impression * 100


def calc_cpa(cost, conversion):
    if not conversion:
        return None
    return cost / conversion


def calc_roas(revenue, cost):
    if not cost:
        return None
    return revenue / cost * 100


def delta_relative(d0, d1):
    """% 변화 (광고비/전환/CPA/매출): D0 또는 D1이 없으면 표시 안 함, D1이 0이어도 표시 안 함."""
    if d0 is None or d1 in (None, 0):
        return None
    return (d0 - d1) / d1 * 100


def delta_point(d0, d1):
    """%p 변화 (CTR/ROAS): D1이 None이면 표시 안 함, 0은 유효한 값."""
    if d0 is None or d1 is None:
        return None
    return d0 - d1


DELTA_FN = {"cost": delta_relative, "ctr": delta_point, "conversion": delta_relative,
            "cpa": delta_relative, "revenue": delta_relative, "roas": delta_point}


def arrow_color(delta, metric_key, digits=1):
    """(화살표, 표시텍스트(부호 포함, 단위 제외), 색상) — delta가 None이면 표시하지 않음(빈 문자열)."""
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
    if delta_tuple is None:
        return ""
    arrow, text, color = delta_tuple
    return (
        f'\n            <div style="font-size:10.5px; text-align:center; color:{color};">'
        f"({arrow} {text}{suffix})</div>"
    )


def media_label(row):
    """매체 라벨은 `media` 값 그대로(접미사·번역 없음). null/빈 값은 Organic."""
    media = row.get("media")
    return str(media) if media not in (None, "") else ORGANIC_LABEL


def media_group_key(row, level):
    media = media_label(row)
    campaign = row.get("campaign_name") or ""
    if level == "ad":
        return (media, campaign, row.get("ad_group_name") or "", row.get("ad_name") or "")
    return (media, campaign)


def index_by_date_key(rows, level):
    idx = {}
    for r in rows:
        k = (r.get("date"), media_group_key(r, level))
        idx.setdefault(k, []).append(r)
    return idx


def sum_rows(rows, mk):
    """같은 (날짜, 키)에 여러 행이 있으면 합산. 행이 없으면 None(그 날짜에 항목 자체가 없음)."""
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


def compute_metrics(s):
    """s는 sum_rows 결과 — 매출/전환이 행에 함께 들어있으므로(ELT) 별도 조인이 없다."""
    cost = s["cost"]
    m = {
        "cost": cost,
        "ctr": calc_ctr(s["click"], s["impression"]),
        "revenue": s["revenue"],
        "roas": calc_roas(s["revenue"], cost),
    }
    if "conversion" in s:
        m["conversion"] = s["conversion"]
        m["cpa"] = calc_cpa(cost, s["conversion"])
    return m


def display(metrics):
    d = {}
    d["cost"] = fmt_won(metrics["cost"])
    d["ctr"] = fmt_pct1(metrics["ctr"]) if metrics["ctr"] is not None else "N/A"
    if "conversion" in metrics:
        d["conversion"] = str(int(metrics["conversion"])) if metrics["conversion"] is not None else "N/A"
        d["cpa"] = fmt_won(metrics["cpa"]) if metrics["cpa"] is not None else "N/A"
    d["revenue"] = fmt_won(metrics["revenue"]) if metrics["revenue"] is not None else "N/A"
    d["roas"] = fmt_pct1(metrics["roas"]) if metrics["roas"] is not None else "N/A"
    return d


def build_row_html(level, media_label, campaign, ad_group, ad_name, cells, order):
    if level == "ad":
        id_html = (
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{media_label}</td>\n'
            f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{campaign}</td>\n'
            f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{ad_group}</td>\n'
            f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{ad_name}</td>'
        )
    else:
        id_html = (
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{media_label}</td>\n'
            f'          <td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{campaign}</td>'
        )

    metric_html_parts = []
    for metric_key, suffix in order:
        d1_val, d0_val, delta = cells[metric_key]
        last = metric_key == "roas"
        border = "" if last else " border-right:1px solid #e2e8f0;"
        metric_html_parts.append(
            f'<td style="white-space:nowrap; text-align:center;">{d1_val}</td>\n'
            f'          <td style="white-space:nowrap; text-align:center;{border}">\n'
            f"            {d0_val}{delta_html(delta, suffix)}\n"
            f"          </td>"
        )

    return "<tr>\n          " + id_html + "\n          " + "\n          ".join(metric_html_parts) + "\n        </tr>"


def main():
    global CURRENCY
    payload = json.load(sys.stdin)
    level = payload["level"]
    d1_date = payload["d1_date"]
    d0_date = payload["d0_date"]
    threshold = payload.get("threshold", 10000)
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

    idx = index_by_date_key(rows, level)
    keys = {k for (_date, k) in idx.keys()}

    out = []
    for key in keys:
        label = key[0]

        d1_sum = sum_rows(idx.get((d1_date, key)), mk)
        d0_sum = sum_rows(idx.get((d0_date, key)), mk)
        if d0_sum is None:
            continue  # D0 데이터 자체가 없으면 cost=0 -> threshold 이하와 동일하게 제외

        if d0_sum["cost"] <= threshold:
            continue

        d1_metrics = compute_metrics(d1_sum) if d1_sum else None
        d0_metrics = compute_metrics(d0_sum)
        d1_disp = display(d1_metrics) if d1_metrics else None
        d0_disp = display(d0_metrics)

        cells = {}
        for metric_key, _suffix in order:
            d1_val = d1_disp[metric_key] if d1_disp else "N/A"
            d0_val = d0_disp[metric_key]
            d1_raw = d1_metrics[metric_key] if d1_metrics else None
            d0_raw = d0_metrics[metric_key]
            delta = DELTA_FN[metric_key](d0_raw, d1_raw)
            cells[metric_key] = (d1_val, d0_val, arrow_color(delta, metric_key))

        campaign = key[1]
        ad_group = key[2] if level == "ad" else None
        ad_name = key[3] if level == "ad" else None
        ad_group_disp = ad_group if ad_group else "-"
        ad_name_disp = ad_name if ad_name else "-"

        html = build_row_html(level, label, campaign, ad_group_disp, ad_name_disp, cells, order)
        search_parts = [label.lower(), campaign.lower()]
        if level == "ad":
            search_parts += [ad_group_disp.lower(), ad_name_disp.lower()]
        out.append({
            "search": " ".join(search_parts),
            "html": html,
            "_d0_cost": d0_sum["cost"],
        })

    out.sort(key=lambda r: r["_d0_cost"], reverse=True)
    for r in out:
        del r["_d0_cost"]

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
