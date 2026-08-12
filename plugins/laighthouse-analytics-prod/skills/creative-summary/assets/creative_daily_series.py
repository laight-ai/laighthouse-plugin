#!/usr/bin/env python3
"""creative-summary section-3/4/5 공용: 소재(ad) 단위 daily_table 응답으로부터
날짜별 CTR/ROAS 시리즈를 계산하는 이미 검증된 asset 스크립트.

실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로 MCP 응답 JSON을 받아 stdout으로
완성된 시리즈만 낸다. 중간 파일을 만들지 않는다(파이프로만 입출력).

이 스크립트가 대체하는 계산 (SKILL.md 실행 방식 절대 지침의 Bash 집계 필수 규칙이 원래
가리키던 대상):

  - section-3: **모든** 소재를 날짜별로 합산해 전체 CTR/전체 ROAS 7일 추이를 낸다(열린
    집계 — 소재 수만큼 행이 있고 5개로 좁혀지지 않는다. 이 스킬에서 정확도 사고가 실제로
    발생했던 것과 동일한 종류의 "날짜별 행이 여러 개인 group_by:ad 응답 합산" 작업이다).
  - section-4/5: 이미 알고 있는 광고비 상위 5개 소재 키로 daily 응답을 exact-match 필터링해
    각 소재의 날짜별 CTR/ROAS 시리즈를 만든다(닫힌 추출, section-1의 range_table 응답에서
    이미 뽑은 top5_keys를 그대로 입력받는다 — 이 스크립트가 랭킹을 다시 매기지 않는다).

⚠️ CTR은 항상 click/impression*100으로 직접 계산한다(응답의 `ctr` 필드는 쓰지 않는다) —
`ctr` 필드가 비율(0.021)인지 %(2.1)인지 응답마다 다를 수 있어 혼동을 피하기 위함.

⚠️ **`get_ad_performance_daily_table`은 JSON 행 배열이 아니라 마크다운 표(파이프 `|` 텍스트)
문자열을 반환한다.** 그 원본을 손으로 JSON으로 옮겨 적거나(전사 실수·행 선별 위험) 파싱용
스크립트를 새로 만들지 않는다 — 아래 `meta_markdown`/`airbridge_markdown` 입력으로 원본
문자열을 그대로 넘기면 이 스크립트가 직접 파싱한다.

입력 (stdin, JSON) — 아래 두 형태 중 하나로 meta/airbridge 각각 넘긴다:

(A) 이미 파싱된 행 객체로 넘길 때:
{
  "meta_rows": [ ... ],       # get_ad_performance_daily_table(media="meta", group_by="ad") 응답 행 그대로
  "airbridge_rows": [ ... ],  # get_ad_performance_daily_table(media="airbridge", group_by="ad") 응답 행 그대로
  ...
}

(B) **권장 — MCP 도구가 실제로 반환하는 원본 마크다운 문자열을 그대로 넘길 때** (각 호출의
    `result` 문자열을 파싱·가공·선별 없이 그대로 넣는다 — 응답이 크다고 "주요 소재만" 손으로
    골라 옮기지 않는다, 문자열 하나 또는 리스트 둘 다 허용):
{
  "meta_markdown": "<media=\"meta\" 호출의 응답 원본 문자열>",
  "airbridge_markdown": "<media=\"airbridge\" 호출의 응답 원본 문자열>",
  ...
}

(C) **플러그인 캡처 훅이 동작하는 호스트(Claude Code)에서 최우선** — MCP 응답이
    "[laighthouse-capture-hook] ... 저장됨: <경로>" 스텁으로 도착한 경우, 그 저장 경로를
    그대로 넘긴다(스크립트가 파일을 직접 읽으므로 원본을 다시 타이핑하지 않는다):
{
  "meta_markdown_files": ["<meta 호출 스텁에 적힌 저장 경로>"],
  "airbridge_markdown_files": ["<airbridge 호출 스텁에 적힌 저장 경로>"],
  ...
}
(A)/(B)/(C)는 섞어 써도 된다 — 같은 쪽(meta/airbridge)에 여러 형태가 오면 합쳐서 처리한다.

공통 나머지 필드:
{
  "top5_keys": [              # section-4/5용. 생략하면 top5 시리즈는 계산하지 않는다(section-3만 필요할 때).
    {"campaign_name": "...", "asset_group": "...", "ad_name": "..."}, ...
  ],
  "dates": ["2026-07-19", ..., "2026-07-25"]  # 선택. 기준일 포함 7일 전체를 명시적으로 넘기면
                                                # meta_rows에 그 날짜 행이 전혀 없는(광고가 완전히
                                                # 게재되지 않은) 날짜도 결측(null/0)으로 정확히
                                                # 채워진다. 생략하면 meta_rows에 실제 등장하는
                                                # 날짜만으로 dates를 만든다(행이 하나도 없는 날은
                                                # 배열에서 통째로 빠질 수 있음 — 캘린더 7일을 항상
                                                # 보장하려면 이 필드를 넘기는 것을 권장한다).
}

행 스키마 가정: 각 행에 `logdate`(또는 `date`), `campaign_name`, `asset_group`, `ad_name`,
`cost`, `impression`, `click`(meta_rows), `airbridge_revenue`(airbridge_rows)가 있다. 날짜
필드명이 다르면 `logdate`/`date` 둘 다 시도한다.

출력 (stdout, JSON):
{
  "dates": ["2026-07-19", ..., "2026-07-25"],   # 오름차순, meta_rows에 등장하는 날짜 전체
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
  {"meta_markdown": "<원본 문자열>", "airbridge_markdown": "<원본 문자열>"}
  PYEOF
"""
import sys
import json
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

STRING_FIELDS = {"logdate", "date", "media", "campaign_name", "asset_group", "ad_name", "channel"}


def _coerce_cell(key, value):
    value = value.strip()
    if key in STRING_FIELDS:
        return value
    if value == "":
        return None
    try:
        f = float(value)
    except ValueError:
        return value
    return int(f) if f.is_integer() else f


def parse_markdown_table(text):
    """`get_ad_performance_daily_table`이 반환하는 파이프(|) 마크다운 표 문자열을 행 dict
    리스트로 파싱한다."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    header = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(c == "" or set(c) <= {"-"} for c in cells):
            continue
        if len(cells) != len(header):
            continue
        rows.append({h: _coerce_cell(h, v) for h, v in zip(header, cells)})
    return rows


def unwrap_json_result(text):
    """Cowork(Claude Desktop) 캡처 훅이 저장한 파일은 `{"result": "<본문>"}` JSON 래퍼일 수
    있다(줄바꿈이 리터럴 \\n) — 래퍼면 벗기고, 아니면 그대로 돌려준다."""
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


def parse_markdown_input(value):
    """문자열 또는 문자열 리스트를 받아 파싱된 행을 전부 이어붙인다."""
    texts = [value] if isinstance(value, str) else list(value)
    return [r for text in texts for r in parse_markdown_table(unwrap_json_result(text))]


def parse_markdown_files(value):
    """파일 경로(문자열 또는 리스트)를 받아 각 파일의 마크다운을 파싱해 이어붙인다 —
    플러그인 캡처 훅이 응답을 파일로 저장한 경우("[laighthouse-capture-hook] ... 저장됨:
    <경로>" 스텁) 그 경로를 그대로 넘기면 된다(원본을 컨텍스트에 다시 타이핑하지 않는다)."""
    paths = [value] if isinstance(value, str) else list(value)
    rows = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            rows.extend(parse_markdown_table(unwrap_json_result(f.read())))
    return rows


def row_date(row):
    return row.get("logdate") or row.get("date")


def creative_key(row):
    return (
        row.get("campaign_name") or "",
        row.get("asset_group") or "",
        row.get("ad_name") or "",
    )


def key_tuple(d):
    return (d.get("campaign_name") or "", d.get("asset_group") or "", d.get("ad_name") or "")


def index_by_date(rows):
    """date -> list[row]"""
    idx = {}
    for r in rows:
        idx.setdefault(row_date(r), []).append(r)
    return idx


def index_by_date_key(rows):
    """(date, key) -> row (첫 매칭행을 그대로 씀 — 같은 날짜/같은 소재 중복 행은 없다고 가정)"""
    idx = {}
    for r in rows:
        idx.setdefault((row_date(r), creative_key(r)), r)
    return idx


def compute_overall(meta_rows, airbridge_rows, dates):
    meta_by_date = index_by_date(meta_rows)
    airbridge_by_date_key = index_by_date_key(airbridge_rows)

    ctr_series = []
    roas_series = []
    for d in dates:
        day_meta_rows = meta_by_date.get(d, [])
        cost_sum = sum(r.get("cost") or 0 for r in day_meta_rows)
        impression_sum = sum(r.get("impression") or 0 for r in day_meta_rows)
        click_sum = sum(r.get("click") or 0 for r in day_meta_rows)

        ctr_series.append(click_sum / impression_sum * 100 if impression_sum else None)

        # 매출은 그 날짜 meta 응답에 존재하는 소재와 조인된 airbridge 행만 합산한다
        # (매체 쪽에 없는 소재의 airbridge 매출은 제외 — section-3 스펙).
        revenue_sum = 0.0
        matched_any = False
        for r in day_meta_rows:
            k = creative_key(r)
            ab_row = airbridge_by_date_key.get((d, k))
            if ab_row is not None:
                revenue_sum += ab_row.get("airbridge_revenue") or 0
                matched_any = True
        roas_series.append(revenue_sum / cost_sum * 100 if cost_sum else None)
        if not matched_any and not cost_sum:
            # cost_sum이 이미 0이면 위에서 None 처리됨 — 별도 처리 불필요, 그냥 통과
            pass

    return ctr_series, roas_series


def compute_top5(meta_rows, airbridge_rows, dates, top5_keys):
    meta_by_date_key = index_by_date_key(meta_rows)
    airbridge_by_date_key = index_by_date_key(airbridge_rows)

    ctr_series = []
    roas_series = []
    for key_dict in top5_keys:
        k = key_tuple(key_dict)
        ctr_row = []
        roas_row = []
        for d in dates:
            meta_row = meta_by_date_key.get((d, k))
            if meta_row is None:
                ctr_row.append(None)
                roas_row.append(0)  # section-5 스펙: 매체 데이터가 없는 날은 0으로 채움(끊기지 않게)
                continue

            impression = meta_row.get("impression") or 0
            click = meta_row.get("click") or 0
            ctr_row.append(click / impression * 100 if impression else None)

            cost = meta_row.get("cost") or 0
            ab_row = airbridge_by_date_key.get((d, k))
            if not cost or ab_row is None:
                roas_row.append(0)  # section-5 스펙: cost 0 또는 조인 실패 시 0
            else:
                revenue = ab_row.get("airbridge_revenue") or 0
                roas_row.append(revenue / cost * 100)
        ctr_series.append(ctr_row)
        roas_series.append(roas_row)

    return ctr_series, roas_series


def main():
    payload = json.load(sys.stdin)
    meta_rows = payload.get("meta_rows", [])
    if "meta_markdown" in payload:
        meta_rows = meta_rows + parse_markdown_input(payload["meta_markdown"])
    if "meta_markdown_files" in payload:
        meta_rows = meta_rows + parse_markdown_files(payload["meta_markdown_files"])
    airbridge_rows = payload.get("airbridge_rows", [])
    if "airbridge_markdown" in payload:
        airbridge_rows = airbridge_rows + parse_markdown_input(payload["airbridge_markdown"])
    if "airbridge_markdown_files" in payload:
        airbridge_rows = airbridge_rows + parse_markdown_files(payload["airbridge_markdown_files"])
    top5_keys = payload.get("top5_keys")

    dates = payload.get("dates")
    if not dates:
        dates = sorted({row_date(r) for r in meta_rows if row_date(r) is not None})

    overall_ctr, overall_roas = compute_overall(meta_rows, airbridge_rows, dates)

    out = {
        "dates": dates,
        "overall": {"ctr_series": overall_ctr, "roas_series": overall_roas},
    }

    if top5_keys:
        top5_ctr, top5_roas = compute_top5(meta_rows, airbridge_rows, dates, top5_keys)
        out["top5"] = {"ctr_series": top5_ctr, "roas_series": top5_roas}

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
