#!/usr/bin/env python3
"""소재 보고서 공용 랭킹 계산기 — 미리 검증된 asset 스크립트.

`creative-summary`와 `creative-detailed`가 **같은 파일**을 각자의 `assets/`에 두고 쓴다(두 사본은
항상 동일해야 한다). 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. 모델은 소재 행을 손으로
정렬·필터링하지 않는다 — 랭킹·상위 5개·표시 이름·section-5 rows는 전부 이 스크립트가 낸다.

두 가지 모드가 있다.

━━ 모드 A: 매체 후보 확인 (SKILL.md 매체 선택 3) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  입력: {"candidates": {"<media>": "<캡처 스텁 경로 또는 응답 원문 JSON 문자열>", ...}}
        (각 값은 get_ad_performance(total, group_by ["ad_name"], metrics [], filters media) 응답)
  출력: {"candidates": ["<media>", ...],            # 실제 소재명이 1개 이상 있는 매체(입력 순서)
         "excluded": {"<media>": "사유", ...},
         "named_ad_count": {"<media>": N, ...}}
  규칙: `ad_name`이 null/빈 문자열/"-"인 행만 있는 매체는 소재가 없는 것으로 본다 — null이 아니고
        "-"도 아닌 `ad_name`이 **하나 이상** 있어야 후보다.

━━ 모드 B: 랭킹 (실행 순서의 total 응답 수신 직후 1회) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  입력 (stdin, JSON):
  {
    "json_files": ["<total 응답 캡처 스텁 경로>"],   # 또는 "json": "<응답 원문>" / "rows": [...]
    "metric_keys": { ...discover.py 출력 그대로... }, # 필수 — revenue 유무로 모드를 정한다
    "chosen_media": "<chosen_media>",                 # section-5 rows의 media 칸
    "media_total_cost": 1234567,                      # 선택 — 생략하면 total 응답 전체 행의 광고비 합
    "s5": true,                                       # 선택 — creative-detailed만: section-5 rows 포함
    "out": "/tmp/creative_rank.json"                  # 필수 — 전체 결과 저장 경로(빌더·시리즈 스크립트가 읽음)
  }
  total 응답 = get_ad_performance(time_grain "total", group_by ["campaign_name","ad_group_name","ad_name"],
               filters {"media": ["<chosen_media>"]}, 최근 7일) — 소재당 1행, 7일 합산 완료.

  계산 규칙:
  - 매출(revenue 키)이 null인 행은 합계·ROAS 계산에서 **0으로 취급**한다(매출 귀속 없음).
  - 최소 표본 기준(최우수 소재 랭킹에만 적용): 노출 ≥ 1,000 **그리고** 광고비 ≥ chosen_media 7일
    총광고비의 1%. 기준을 충족하는 소재가 하나도 없으면 전체 소재로 폴백한다(`eligibility.fallback`).
  - 매출 있음: ROAS = 매출 ÷ 광고비 × 100 내림차순 1·2위(광고비 0 제외).
    매출 없음: 클릭 수(7일 합) 내림차순 1·2위.
  - 두 모드 공통: CTR = 클릭 ÷ 노출 × 100 내림차순 1·2위(노출 0 제외). 두 랭킹은 서로 독립.
  - 동점은 광고비가 큰 소재 우선.
  - 상위 5개(section-3/4/5 차트): 광고비 내림차순 5개 — 최소 표본 기준 **미적용**(전체 소재).
  - 표시 이름: `ad_name`이 비었거나 "-"이면 "<ad_group_name> (소재명 없음)". 같은 목록(최우수 카드
    1·2위 쌍, 상위 5개) 안에서 표시 이름이 겹치면 " (<ad_group_name>)"을(그래도 겹치면
    " (<campaign_name>)"을) 덧붙인다. section-5 표의 광고 칸도 같은 소재명 폴백을 쓴다.

  출력 파일(`out`) JSON:
  {
    "has_revenue": bool, "has_conversion": bool,
    "eligibility": {"min_impressions": 1000, "min_cost_share": 0.01, "media_total_cost": ..,
                    "min_cost": .., "eligible": n, "total": N, "fallback": bool},
    "media_totals": {"cost","impression","click",("revenue"),"ctr",("roas"|"cpc")},
    "s1": {"roas"|"click": [{"name","value","lookup","thumbnail_url": null}, ...], "ctr": [...]},
    "lookups": [{"id": "L1", "ad_name", "campaign_name", "ad_group_name"}, ...],
                # get_ad_creative_info로 썸네일을 찾을 소재(유니크, 소재명 없는 소재 제외)
    "top5_keys": [{"campaign_name","ad_group_name","ad_name"}, ...],
    "top5_names": ["표시이름", ...],
    "top_by_cost": [{"name","cost","impression","click","ctr",("revenue","roas"|"cpc"),("conversion")}, ...10개],
    "s5_rows": [...]            # "s5": true일 때만 — 빌더 section-5 rows 스키마 그대로
  }
  stdout: 위 JSON에서 s5_rows를 뺀 요약(Executive Summary 근거·lookups 확인용).

사용 예 (따옴표 있는 heredoc 하나 — 파일을 Read로 다시 열지 않는다):
  python3 assets/rank_creatives.py <<'PYEOF'
  {"json_files": ["<total 스텁 경로>"], "metric_keys": {...}, "chosen_media": "<m>", "out": "/tmp/creative_rank.json"}
  PYEOF
"""
import io
import json
import os
import sys

if __name__ == "__main__":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MIN_IMPRESSIONS = 1000
MIN_COST_SHARE = 0.01
NO_NAME = "(소재명 없음)"
REQUIRED = ("cost", "impression", "click")


# ── 응답 로드 ────────────────────────────────────────────────────────────────
def _unwrap(text):
    """Cowork 캡처 파일의 `{"result": "<본문>"}` 래퍼를 벗긴다."""
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


def _envelope(text):
    obj = json.loads(_unwrap(text))
    if isinstance(obj, list):
        return obj, None
    if not isinstance(obj, dict) or not isinstance(obj.get("rows"), list):
        raise SystemExit("get_ad_performance JSON 봉투가 아님 — rows 배열이 없다")
    return obj["rows"], obj.get("metrics")


def _text_of(value):
    """캡처 스텁 경로 또는 응답 원문 문자열 → 원문."""
    s = value.strip()
    if s.startswith("{") or s.startswith("["):
        return s
    with open(os.path.expanduser(s), encoding="utf-8") as f:
        return f.read()


def load_rows(payload):
    rows = list(payload.get("rows") or [])
    metrics = set()
    texts = payload.get("json", [])
    texts = [texts] if isinstance(texts, str) else list(texts)
    files = payload.get("json_files", [])
    for path in [files] if isinstance(files, str) else files:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            texts.append(f.read())
    for text in texts:
        r, m = _envelope(text)
        rows.extend(r)
        metrics.update(m or ())
    # Organic(media=null) 행은 소재가 아니다
    rows = [r for r in rows if not ("media" in r and r["media"] is None)]
    return rows, metrics


# ── 표시 이름 ────────────────────────────────────────────────────────────────
def has_ad_name(name):
    return name is not None and str(name).strip() not in ("", "-")


def base_name(r):
    if has_ad_name(r.get("ad_name")):
        return str(r["ad_name"])
    return f"{r.get('ad_group_name') or '-'} {NO_NAME}"


def display_names(rows):
    """같은 목록 안에서 겹치는 표시 이름만 광고그룹(그래도 겹치면 캠페인)으로 구분한다."""
    names = [base_name(r) for r in rows]

    def dups(ns):
        return {n for n in ns if ns.count(n) > 1}

    d = dups(names)
    if d:
        names = [f"{n} ({r.get('ad_group_name') or '-'})"
                 if n in d and has_ad_name(r.get("ad_name")) else n
                 for n, r in zip(names, rows)]
    d = dups(names)
    if d:
        names = [f"{n} ({r.get('campaign_name') or '-'})" if n in d else n
                 for n, r in zip(names, rows)]
    return names


# ── 모드 A ───────────────────────────────────────────────────────────────────
def candidates_main(cands):
    out = {"candidates": [], "excluded": {}, "named_ad_count": {}}
    for media, value in cands.items():
        try:
            rows, _ = _envelope(_text_of(value))
        except (OSError, ValueError, SystemExit) as e:
            out["excluded"][media] = f"응답 해석 실패: {e}"
            continue
        n = len({r.get("ad_name") for r in rows if has_ad_name(r.get("ad_name"))})
        out["named_ad_count"][media] = n
        if n:
            out["candidates"].append(media)
        else:
            out["excluded"][media] = ("행 없음" if not rows
                                      else "ad_name이 전부 null/빈 값/\"-\" — 소재 단위 데이터 아님")
    return out


# ── 모드 B ───────────────────────────────────────────────────────────────────
def _num(r, key):
    v = r.get(key) if key else None
    return v if isinstance(v, (int, float)) else 0


def _ratio(num, den, scale=100.0):
    return num / den * scale if den else None


def rank_main(payload):
    mk = {r: k for r, k in (payload.get("metric_keys") or {}).items() if k}
    missing = [r for r in REQUIRED if not mk.get(r)]
    if missing:
        raise SystemExit(f"metric_keys에 필수 역할 {missing}가 없다 — discover.py 출력을 그대로 넘겨라")
    rows, metrics = load_rows(payload)
    if metrics:
        unknown = [f"{r}={k}" for r, k in mk.items() if r in REQUIRED + ("revenue", "conversion")
                   and k not in metrics]
        if unknown:
            raise SystemExit(f"metric_keys {unknown}가 응답 metrics {sorted(metrics)}에 없다")
    has_rev = bool(mk.get("revenue"))
    has_conv = bool(mk.get("conversion"))

    recs = []
    for r in rows:
        rec = {"campaign_name": r.get("campaign_name"), "ad_group_name": r.get("ad_group_name"),
               "ad_name": r.get("ad_name"),
               "cost": _num(r, mk["cost"]), "impression": _num(r, mk["impression"]),
               "click": _num(r, mk["click"])}
        if has_rev:
            rec["revenue"] = _num(r, mk["revenue"])            # null → 0 (합계·ROAS용)
            rec["revenue_raw"] = r.get(mk["revenue"])          # section-5 표시용 원본
        if has_conv:
            rec["conversion_raw"] = r.get(mk["conversion"])
            rec["conversion"] = _num(r, mk["conversion"])
        recs.append(rec)

    tot = {k: sum(x[k] for x in recs) for k in ("cost", "impression", "click")}
    if has_rev:
        tot["revenue"] = sum(x["revenue"] for x in recs)
    tot["ctr"] = _ratio(tot["click"], tot["impression"])
    if has_rev:
        tot["roas"] = _ratio(tot["revenue"], tot["cost"])
    else:
        tot["cpc"] = _ratio(tot["cost"], tot["click"], 1.0)

    media_cost = payload.get("media_total_cost")
    if not isinstance(media_cost, (int, float)):
        media_cost = tot["cost"]
    min_cost = media_cost * MIN_COST_SHARE
    eligible = [x for x in recs if x["impression"] >= MIN_IMPRESSIONS and x["cost"] >= min_cost]
    fallback = not eligible
    pool = recs if fallback else eligible

    by_cost = lambda x: x["cost"]  # noqa: E731 — 동점 시 광고비 큰 소재 우선

    def top2(cands, metric):
        return sorted(cands, key=lambda x: (metric(x), by_cost(x)), reverse=True)[:2]

    if has_rev:
        a_key = "roas"
        a_metric = lambda x: x["revenue"] / x["cost"] * 100  # noqa: E731
        a_list = top2([x for x in pool if x["cost"] > 0], a_metric)
    else:
        a_key = "click"
        a_metric = lambda x: x["click"]  # noqa: E731
        a_list = top2(pool, a_metric)
    ctr_metric = lambda x: x["click"] / x["impression"] * 100  # noqa: E731
    ctr_list = top2([x for x in pool if x["impression"] > 0], ctr_metric)

    lookups, lookup_id = [], {}

    def lookup_of(x):
        if not has_ad_name(x["ad_name"]):
            return None
        k = (x["campaign_name"], x["ad_group_name"], x["ad_name"])
        if k not in lookup_id:
            lookup_id[k] = f"L{len(lookups) + 1}"
            lookups.append({"id": lookup_id[k], "ad_name": x["ad_name"],
                            "campaign_name": x["campaign_name"], "ad_group_name": x["ad_group_name"]})
        return lookup_id[k]

    def card(lst, metric):
        return [{"name": n, "value": metric(x), "lookup": lookup_of(x), "thumbnail_url": None}
                for n, x in zip(display_names(lst), lst)]

    s1 = {a_key: card(a_list, a_metric), "ctr": card(ctr_list, ctr_metric)}

    ranked = sorted(recs, key=by_cost, reverse=True)
    top5 = ranked[:5]

    def compact(x, name):
        c = {"name": name, "cost": x["cost"], "impression": x["impression"], "click": x["click"],
             "ctr": _ratio(x["click"], x["impression"])}
        if has_rev:
            c["revenue"] = x["revenue"]
            c["roas"] = _ratio(x["revenue"], x["cost"])
        else:
            c["cpc"] = _ratio(x["cost"], x["click"], 1.0)
        if has_conv:
            c["conversion"] = x["conversion"]
        return c

    top10 = ranked[:10]
    out = {
        "has_revenue": has_rev, "has_conversion": has_conv,
        "eligibility": {"min_impressions": MIN_IMPRESSIONS, "min_cost_share": MIN_COST_SHARE,
                        "media_total_cost": media_cost, "min_cost": min_cost,
                        "eligible": len(eligible), "total": len(recs), "fallback": fallback},
        "media_totals": tot,
        "s1": s1,
        "lookups": lookups,
        "top5_keys": [{k: x[k] for k in ("campaign_name", "ad_group_name", "ad_name")} for x in top5],
        "top5_names": display_names(top5),
        "top_by_cost": [compact(x, n) for x, n in zip(top10, display_names(top10))],
    }
    if payload.get("s5"):
        media = payload.get("chosen_media") or ""
        s5 = []
        for x in recs:
            row = {"media": media, "campaign": x["campaign_name"] or "", "asset_group": x["ad_group_name"] or "",
                   "ad_name": base_name(x), "impression": x["impression"], "click": x["click"],
                   "cost": x["cost"]}
            if has_rev:
                row["revenue"] = x["revenue_raw"]
            if has_conv:
                row["conversion"] = x["conversion_raw"]
            s5.append(row)
        out["s5_rows"] = s5
    return out


# ── 빌더(build_report.py)가 import해서 쓰는 헬퍼 ────────────────────────────────
def load_rank(payload):
    """빌더 입력 최상위 `rank_file`(이 스크립트 출력)을 읽는다. 없으면 None."""
    path = payload.get("rank_file")
    if not path:
        return None
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return json.load(f)


def resolve_s1(s1, rank, thumbnails, a_key):
    """`s1` 키가 있는데 랭킹 배열이 비어 있으면 rank_file의 s1을 쓰고, `thumbnails`
    ({"L1": "<image_url>"|null})로 썸네일을 채운다. `s1` 키가 없으면(None) 그대로 None."""
    if s1 is None:
        return None
    if not (s1.get(a_key) or s1.get("ctr")) and rank:
        s1 = rank.get("s1") or {}
    thumbnails = thumbnails or {}
    out = {}
    for k, lst in s1.items():
        if not isinstance(lst, list):
            out[k] = lst
            continue
        items = []
        for e in lst:
            e = dict(e)
            if not e.get("thumbnail_url") and e.get("lookup") in thumbnails:
                e["thumbnail_url"] = thumbnails[e["lookup"]] or None
            items.append(e)
        out[k] = items
    return out


def rule_note_html(rank, money):
    """section-1 하단 최소 표본 기준 각주. money: 금액 포맷 함수."""
    if not rank or not rank.get("eligibility"):
        return ""
    el = rank["eligibility"]
    rule = (f"노출 {el['min_impressions']:,}회 이상이면서 광고비가 매체 7일 총광고비의 "
            f"{el['min_cost_share'] * 100:g}%({money(el['min_cost'])}) 이상")
    if el.get("fallback"):
        text = (f"* 최소 표본 기준({rule})을 충족한 소재가 없어, 이번에는 전체 소재 {el['total']:,}개 "
                f"중에서 선정했습니다. 표본이 작은 소재의 비율 지표는 변동이 클 수 있습니다.")
    else:
        text = (f"* 표본이 작은 소재의 비율 왜곡을 막기 위해, 최소 표본 기준({rule})을 충족한 소재 "
                f"{el['eligible']:,}개(전체 {el['total']:,}개) 중에서 선정했습니다.")
    return f'<p style="font-size:11px; color:#64748b; margin:-4px 0 16px; line-height:1.5;">{text}</p>'


def main():
    # 입력: 인자로 JSON 파일 경로를 주면 그 파일, 없으면 stdin (report_kit.read_payload 와 같은 규칙)
    if len(sys.argv) > 1 and sys.argv[1] not in ("-", ""):
        with open(os.path.expanduser(sys.argv[1]), encoding="utf-8-sig") as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)
    if "candidates" in payload:
        json.dump(candidates_main(payload["candidates"]), sys.stdout, ensure_ascii=False)
        return
    if not payload.get("out"):
        raise SystemExit("out(결과 저장 경로)이 필요하다")
    out = rank_main(payload)
    path = os.path.abspath(os.path.expanduser(payload["out"]))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    summary = {k: v for k, v in out.items() if k != "s5_rows"}
    summary["out"] = path
    if "s5_rows" in out:
        summary["s5_row_count"] = len(out["s5_rows"])
    json.dump(summary, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
