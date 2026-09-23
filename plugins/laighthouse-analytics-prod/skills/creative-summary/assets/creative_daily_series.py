#!/usr/bin/env python3
"""소재 보고서 공용 일별 시리즈 계산기 — 이미 검증된 asset 스크립트.

`creative-summary`(section-3/4/5)와 `creative-detailed`(section-3/4)가 **같은 파일**을 각자의
`assets/`에 두고 쓴다. 소재(ad) 단위 `get_ad_performance(time_grain="day")` 응답에서 날짜별
CTR/ROAS/클릭 시리즈를 계산한다. 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로
입력 JSON을 받아 stdout으로 완성된 시리즈만 낸다(중간 파일 없음).

이 스크립트가 대체하는 계산:

  - overall (creative-summary section-3): **모든** 소재를 날짜별로 합산한 전체 CTR과
    전체 ROAS(매출 있음) 또는 전체 클릭(매출 없음) 7일 추이. 소재 수만큼 행이 있는 열린 집계라
    손계산하면 정확도 사고가 난다(실제 사례).
  - top5 (creative-summary section-4/5, creative-detailed section-3/4): 이미 정한 광고비 상위
    5개 소재 키로 day 응답을 exact-match(`campaign_name`+`ad_group_name`+`ad_name` 세 필드 정확
    일치 — 정규화/부분일치 없음)해 소재별 날짜별 CTR·ROAS·클릭 시리즈를 만든다. 랭킹은 다시
    매기지 않는다(top5_keys를 그대로 받는다).

⚠️ 비율은 항상 원자 지표(역할 키 값) 합으로 직접 계산한다 — 응답에 서버 비율 지표(CTR/ROAS류)가
있어도 행 단위 비율은 합칠 수 없다.

⚠️ `media`가 `null`인 행(Organic — 소재 개념이 없다)은 무시한다. 소재 호출은 매체 필터를 걸어
원래 오지 않지만, 행에 `media` 키가 있고 값이 null이면 건너뛴다.

입력 (stdin, JSON) — day 응답은 아래 중 하나(섞어도 된다, 여러 개면 합쳐서 처리):
  "json_files": ["<캡처 훅 스텁에 적힌 저장 경로>"]   # 캡처 훅 호스트에서 최우선 — 경로만
  "json": "<응답 원본 JSON 봉투 문자열>"                # 문자열 하나 또는 리스트
  "rows": [ ...봉투의 rows 배열 그대로... ]

공통 나머지 필드:
{
  "metric_keys": {             # 권장. 디스커버리(discover.py) 출력의 metric_keys를 그대로.
    "cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>",
    "revenue": "<revenue 키 — 있을 때만>"      # 없으면 매출 없음 모드 (ROAS 시리즈 생략)
  },                           # 생략하면 봉투 metrics에서 공용 킷(report_kit.resolve_roles)
                               # 규칙으로 해석한다. 필수 역할(cost/impression/click)을 못 정하면 에러.
  "top5_keys": [               # 선택 — 생략하면 top5 시리즈를 계산하지 않는다
    {"campaign_name": "...", "ad_group_name": "...", "ad_name": "..."}, ...
  ],
  "dates": ["YYYY-MM-DD", ...] # 선택(권장) — 기준일 포함 7일 전체. 행이 없는 날짜도 결측으로 채운다.
                               # 생략하면 rows에 등장한 날짜만 쓴다.
}

출력 (stdout, JSON):
{
  "dates": [...7개, 오름차순...],
  "has_revenue": true|false,                   # metric_keys에 revenue가 있었는지
  "overall": {
    "ctr_series":   [1.53, null, ...],         # 노출 합 0인 날짜는 null
    "click_series": [1234, 0, ...],            # 날짜별 클릭 합 (행 없으면 0)
    "roas_series":  [182.3, null, ...],        # 매출 있음 모드만. 광고비 합 0인 날짜는 null
    "totals": {"cost": [...], "impression": [...], "click": [...], "revenue": [...]}
                                               # 날짜별 원자 지표 합 (revenue는 매출 있음 모드만)
  },
  "top5": {                                    # top5_keys를 준 경우에만
    "ctr_series":   [[...7개...], ...],        # top5_keys 순서, 행 없음/노출 0 → null
    "click_series": [[...7개...], ...],        # 행 없음 → 0
    "roas_series":  [[...7개...], ...],        # 매출 있음 모드만. 행 없음/광고비 0 → 0 (끊기지 않게)
    "totals": [ {"cost":..,"impression":..,"click":..,"revenue":..,"ctr":..,"cpc":..,"roas":..}, ...]
                                               # 소재별 7일 합 + 파생 비율 (Executive Summary 근거용)
  }
}

사용 예 (한 번의 Bash 호출, 따옴표 있는 heredoc — echo나 파일 저장 후 재실행 금지):
  python3 assets/creative_daily_series.py <<'PYEOF' > /tmp/creative_series.json
  {"json_files": ["<스텁 경로>"], "dates": [...], "metric_keys": {...}, "top5_keys": [...]}
  PYEOF
"""
import io
import json
import os
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ("cost", "impression", "click")


def _load_kit():
    for cand in (os.path.join(ASSETS_DIR, "..", "shared", "assets"),          # ChatGPT 번들
                 os.path.join(ASSETS_DIR, "..", "..", "..", "shared", "assets")):  # 플러그인 루트
        if os.path.exists(os.path.join(cand, "report_kit.py")):
            sys.path.insert(0, os.path.normpath(cand))
            import report_kit
            return report_kit
    raise SystemExit("report_kit.py를 찾을 수 없다 (shared/assets)")


def resolve_metric_keys(metrics, override):
    """역할 → 실제 지표 키. 넘겨받은 metric_keys를 우선하고, 없으면 공용 킷 규칙으로 해석한다.
    revenue는 선택(없으면 매출 없음 모드), cost/impression/click은 필수."""
    if override:
        mk = {r: k for r, k in override.items() if k}
    else:
        mk = dict(_load_kit().resolve_roles({"metrics": sorted(metrics), "rows": []})["metric_keys"])
    missing = [r for r in REQUIRED if not mk.get(r)]
    if missing:
        raise SystemExit(f"필수 지표 역할 {missing}의 키를 정하지 못함 — 응답 metrics "
                         f"{sorted(metrics)}에서 쓸 키를 metric_keys로 넘겨라")
    if metrics:
        unknown = [f"{r}={k}" for r, k in mk.items() if r in REQUIRED + ("revenue",) and k not in metrics]
        if unknown:
            raise SystemExit(f"metric_keys {unknown}가 응답 metrics {sorted(metrics)}에 없다")
    return mk


def unwrap_json_result(text):
    """Cowork(Claude Desktop) 캡처 훅 파일은 `{"result": "<본문>"}` 래퍼일 수 있다 — 벗긴다."""
    for _ in range(3):
        if not isinstance(text, str) or not text.lstrip().startswith("{"):
            return text
        try:
            obj = json.loads(text)
        except ValueError:
            return text
        if isinstance(obj, dict) and isinstance(obj.get("result"), str):
            text = obj["result"]
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


def key_tuple(d):
    return (d.get("campaign_name") or "", d.get("ad_group_name") or "", d.get("ad_name") or "")


def _sum(rows, key):
    return sum((r.get(key) or 0) for r in rows) if key else 0


def _ratio(num, den, scale=100.0):
    return num / den * scale if den else None


def compute_overall(rows, dates, mk):
    by_date = {}
    for r in rows:
        by_date.setdefault(r.get("date"), []).append(r)
    has_rev = bool(mk.get("revenue"))
    totals = {role: [] for role in ("cost", "impression", "click") + (("revenue",) if has_rev else ())}
    ctr, roas = [], []
    for d in dates:
        day = by_date.get(d, [])
        sums = {role: _sum(day, mk[role]) for role in totals}
        for role, v in sums.items():
            totals[role].append(v)
        ctr.append(_ratio(sums["click"], sums["impression"]))
        if has_rev:
            roas.append(_ratio(sums["revenue"], sums["cost"]))
    out = {"ctr_series": ctr, "click_series": list(totals["click"]), "totals": totals}
    if has_rev:
        out["roas_series"] = roas
    return out


def compute_top5(rows, dates, top5_keys, mk):
    idx = {}
    for r in rows:
        idx.setdefault((r.get("date"), key_tuple(r)), []).append(r)
    has_rev = bool(mk.get("revenue"))
    ctr_s, click_s, roas_s, totals = [], [], [], []
    for kd in top5_keys:
        k = key_tuple(kd)
        ctr_row, click_row, roas_row = [], [], []
        tot = {"cost": 0, "impression": 0, "click": 0}
        if has_rev:
            tot["revenue"] = 0
        for d in dates:
            day = idx.get((d, k))
            if not day:
                ctr_row.append(None)
                click_row.append(0)
                roas_row.append(0)  # ROAS 차트 스펙: 데이터 없는 날은 0 (끊기지 않게)
                continue
            s = {role: _sum(day, mk[role]) for role in tot}
            for role, v in s.items():
                tot[role] += v
            ctr_row.append(_ratio(s["click"], s["impression"]))
            click_row.append(s["click"])
            if has_rev:
                roas_row.append(_ratio(s["revenue"], s["cost"]) or 0)  # 광고비 0 → 0
        tot["ctr"] = _ratio(tot["click"], tot["impression"])
        tot["cpc"] = _ratio(tot["cost"], tot["click"], 1.0)
        if has_rev:
            tot["roas"] = _ratio(tot["revenue"], tot["cost"])
        ctr_s.append(ctr_row)
        click_s.append(click_row)
        roas_s.append(roas_row)
        totals.append(tot)
    out = {"ctr_series": ctr_s, "click_series": click_s, "totals": totals}
    if has_rev:
        out["roas_series"] = roas_s
    return out


def main():
    payload = json.load(sys.stdin)

    rows = list(payload.get("rows") or [])
    metrics = set()
    texts = payload.get("json", [])
    texts = [texts] if isinstance(texts, str) else list(texts)
    files = payload.get("json_files", [])
    for path in [files] if isinstance(files, str) else files:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            texts.append(f.read())
    for text in texts:
        env_rows, env_metrics = parse_envelope(text)
        rows.extend(env_rows)
        metrics.update(env_metrics or ())
    # Organic(media=null) 행은 소재가 아니다 — 무시
    rows = [r for r in rows if not ("media" in r and r["media"] is None)]
    if not metrics:
        for r in rows:
            metrics.update(k for k, v in r.items() if isinstance(v, (int, float)) or v is None)

    mk = resolve_metric_keys(metrics, payload.get("metric_keys"))

    dates = payload.get("dates") or sorted({r.get("date") for r in rows if r.get("date")})

    out = {"dates": dates, "has_revenue": bool(mk.get("revenue")),
           "overall": compute_overall(rows, dates, mk)}
    if payload.get("top5_keys"):
        out["top5"] = compute_top5(rows, dates, payload["top5_keys"], mk)

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
