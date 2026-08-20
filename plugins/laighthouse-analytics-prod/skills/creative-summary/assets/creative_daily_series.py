#!/usr/bin/env python3
"""creative-summary section-3/4/5 공용: 소재(ad) 단위 get_ad_performance(time_grain="day")
응답으로부터 날짜별 CTR/ROAS 시리즈를 계산하는 이미 검증된 asset 스크립트.

실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로 MCP 응답 JSON을 받아 stdout으로
완성된 시리즈만 낸다. 중간 파일을 만들지 않는다(파이프로만 입출력).

이 스크립트가 대체하는 계산:

  - section-3: **모든** 소재를 날짜별로 합산해 전체 CTR/전체 ROAS 7일 추이를 낸다(열린
    집계 — 소재 수만큼 행이 있고 5개로 좁혀지지 않는다. 이 스킬에서 정확도 사고가 실제로
    발생했던 것과 동일한 종류의 "날짜별 행이 여러 개인 소재 단위 응답 합산" 작업이다).
  - section-4/5: 이미 알고 있는 광고비 상위 5개 소재 키로 daily 응답을 exact-match 필터링해
    각 소재의 날짜별 CTR/ROAS 시리즈를 만든다(닫힌 추출, section-1의 total 응답에서 이미
    뽑은 top5_keys를 그대로 입력받는다 — 이 스크립트가 랭킹을 다시 매기지 않는다).

⚠️ CTR/ROAS는 항상 원자 지표(클릭/노출/매출/광고비)로 직접 계산한다 — 응답에 서버 계산
비율 지표(`CTR`/`ROAS_AB`)가 있어도, 날짜별 합산(section-3)은 행 단위 비율을 합칠 수 없기
때문에 원자 지표 합으로 계산해야 정확하다.

⚠️ **`get_ad_performance`는 마크다운 표가 아니라 JSON 봉투를 반환한다** — `{"source": "elt",
"tenant": ..., "time_grain": "day", "dimensions": [...], "metrics": [...], "row_count": N,
"rows": [...]}`. 각 행에는 차원 키(영문: `date`/`campaign_name`/`ad_group_name`/`ad_name` 등)와
**테넌트별 지표 키**(브리즘: `광고비`/`노출`/`클릭`/`매출_AB`/`예약완료_AB` 등)가 들어있다 —
매출이 행 안에 함께 오므로 예전 같은 meta/airbridge 2응답 조인이 없다. 원본을 손으로 옮겨
적거나(전사 실수·행 선별 위험) 파싱용 스크립트를 새로 만들지 않는다 — 아래 입력으로 원본
문자열/파일 경로를 그대로 넘기면 이 스크립트가 직접 파싱한다.

입력 (stdin, JSON) — 아래 형태 중 하나로 daily 응답을 넘긴다:

(A) **플러그인 캡처 훅이 동작하는 호스트(Claude Code)에서 최우선** — MCP 응답이
    "[laighthouse-capture-hook] ... 저장됨: <경로>" 스텁으로 도착한 경우, 그 저장 경로를
    그대로 넘긴다(스크립트가 파일을 직접 읽으므로 원본을 다시 타이핑하지 않는다):
{
  "json_files": ["<daily 호출 스텁에 적힌 저장 경로>"],
  ...
}

(B) 원본 JSON 봉투 문자열을 그대로 넘길 때 (응답이 크다고 "주요 소재만" 손으로 골라 옮기지
    않는다, 문자열 하나 또는 리스트 둘 다 허용):
{
  "json": "<get_ad_performance(time_grain=\"day\", media=\"Meta\") 응답 원본 문자열>",
  ...
}

(C) 이미 파싱된 행 객체로 넘길 때:
{
  "rows": [ ... ],   # 봉투의 rows 배열 그대로
  ...
}
(A)/(B)/(C)는 섞어 써도 된다 — 여러 형태가 오면 합쳐서 처리한다.

공통 나머지 필드:
{
  "top5_keys": [              # section-4/5용. 생략하면 top5 시리즈는 계산하지 않는다(section-3만 필요할 때).
    {"campaign_name": "...", "ad_group_name": "...", "ad_name": "..."}, ...
  ],
  "dates": ["2026-07-19", ..., "2026-07-25"],  # 선택. 기준일 포함 7일 전체를 명시적으로 넘기면
                                                # 그 날짜 행이 전혀 없는(광고가 완전히 게재되지
                                                # 않은) 날짜도 결측(null/0)으로 정확히 채워진다.
                                                # 생략하면 rows에 실제 등장하는 날짜만으로 dates를
                                                # 만든다(행이 하나도 없는 날은 배열에서 통째로 빠질
                                                # 수 있음 — 캘린더 7일을 항상 보장하려면 이 필드를
                                                # 넘기는 것을 권장한다).
  "metric_keys": {             # 선택. 지표 키는 테넌트별 — 생략하면 브리즘(breezm) 기본값을 쓰고,
    "cost": "광고비",           # 봉투의 metrics 목록과 대조해 없는 키는 명확한 에러를 낸다.
    "impression": "노출", "click": "클릭", "revenue": "매출_AB"
  }
}

출력 (stdout, JSON):
{
  "dates": ["2026-07-19", ..., "2026-07-25"],   # 오름차순
  "overall": {
    "ctr_series": [1.53, null, ...],             # section-3용. 노출 합 0인 날짜는 null
    "roas_series": [182.3, null, ...]            # 광고비 합 0인 날짜는 null
  },
  "top5": {                                       # top5_keys를 준 경우에만 포함
    "ctr_series": [[...7개...], ...],             # top5_keys와 같은 순서, 값 없는 날짜는 null
    "roas_series": [[...7개...], ...]             # 매칭 실패/광고비 0인 날짜는 0 (section-5 스펙)
  }
}

사용 예 (단 한 번의 Bash 호출 안에서 따옴표 있는 heredoc으로 — echo나 파일 저장 후 재실행 X):
  python3 assets/creative_daily_series.py <<'PYEOF'
  {"json_files": ["<스텁 경로>"], "dates": [...], "top5_keys": [...]}
  PYEOF
"""
import sys
import json
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DEFAULT_METRIC_KEYS = {
    "cost": "광고비",
    "impression": "노출",
    "click": "클릭",
    "revenue": "매출_AB",
}


def unwrap_json_result(text):
    """Cowork(Claude Desktop) 캡처 훅이 저장한 파일은 `{"result": "<본문>"}` JSON 래퍼일 수
    있다 — 래퍼면 벗기고, 아니면 그대로 돌려준다. `get_ad_performance` 봉투는 `result` 키가
    없으므로 그대로 통과한다."""
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


def creative_key(row):
    return (
        row.get("campaign_name") or "",
        row.get("ad_group_name") or "",
        row.get("ad_name") or "",
    )


def key_tuple(d):
    return (d.get("campaign_name") or "", d.get("ad_group_name") or "", d.get("ad_name") or "")


def index_by_date(rows):
    """date -> list[row]"""
    idx = {}
    for r in rows:
        idx.setdefault(r.get("date"), []).append(r)
    return idx


def index_by_date_key(rows):
    """(date, key) -> list[row] (같은 날짜/같은 소재의 중복 행은 합산)"""
    idx = {}
    for r in rows:
        idx.setdefault((r.get("date"), creative_key(r)), []).append(r)
    return idx


def compute_overall(rows, dates, mk):
    by_date = index_by_date(rows)

    ctr_series = []
    roas_series = []
    for d in dates:
        day_rows = by_date.get(d, [])
        cost_sum = sum(r.get(mk["cost"]) or 0 for r in day_rows)
        impression_sum = sum(r.get(mk["impression"]) or 0 for r in day_rows)
        click_sum = sum(r.get(mk["click"]) or 0 for r in day_rows)
        revenue_sum = sum(r.get(mk["revenue"]) or 0 for r in day_rows)

        ctr_series.append(click_sum / impression_sum * 100 if impression_sum else None)
        roas_series.append(revenue_sum / cost_sum * 100 if cost_sum else None)

    return ctr_series, roas_series


def compute_top5(rows, dates, top5_keys, mk):
    by_date_key = index_by_date_key(rows)

    ctr_series = []
    roas_series = []
    for key_dict in top5_keys:
        k = key_tuple(key_dict)
        ctr_row = []
        roas_row = []
        for d in dates:
            day_rows = by_date_key.get((d, k))
            if not day_rows:
                ctr_row.append(None)
                roas_row.append(0)  # section-5 스펙: 데이터가 없는 날은 0으로 채움(끊기지 않게)
                continue

            impression = sum(r.get(mk["impression"]) or 0 for r in day_rows)
            click = sum(r.get(mk["click"]) or 0 for r in day_rows)
            ctr_row.append(click / impression * 100 if impression else None)

            cost = sum(r.get(mk["cost"]) or 0 for r in day_rows)
            revenue = sum(r.get(mk["revenue"]) or 0 for r in day_rows)
            if not cost:
                roas_row.append(0)  # section-5 스펙: cost 0이면 0
            else:
                roas_row.append(revenue / cost * 100)
        ctr_series.append(ctr_row)
        roas_series.append(roas_row)

    return ctr_series, roas_series


def main():
    payload = json.load(sys.stdin)

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

    mk = dict(DEFAULT_METRIC_KEYS)
    mk.update(payload.get("metric_keys") or {})
    if envelope_metrics:
        missing = [v for v in mk.values() if v not in envelope_metrics]
        if missing:
            raise SystemExit(
                f"지표 키 {missing}가 응답 metrics {envelope_metrics}에 없음 — "
                f"테넌트별 지표 키를 metric_keys로 넘겨라"
            )

    top5_keys = payload.get("top5_keys")

    dates = payload.get("dates")
    if not dates:
        dates = sorted({r.get("date") for r in rows if r.get("date") is not None})

    overall_ctr, overall_roas = compute_overall(rows, dates, mk)

    out = {
        "dates": dates,
        "overall": {"ctr_series": overall_ctr, "roas_series": overall_roas},
    }

    if top5_keys:
        top5_ctr, top5_roas = compute_top5(rows, dates, top5_keys, mk)
        out["top5"] = {"ctr_series": top5_ctr, "roas_series": top5_roas}

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
