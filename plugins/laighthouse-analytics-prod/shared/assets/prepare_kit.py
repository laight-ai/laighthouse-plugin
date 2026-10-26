"""prepare 공용 킷 — 저장 훅이 남긴 MCP 응답 원본에서 빌더 기본 입력(base.json)과 요약 근거(facts)를 만든다.

각 스킬의 `assets/prepare.py`가 `prepare_kit.main("<스킬명>")`으로 부른다(모델이 직접 import 하지 않는다).

흐름: 스킬 SKILL.md의 MCP 호출을 한 메시지에 동시에 보낸다 → 플러그인 저장 훅(`hooks/save_responses.py`)이
응답 원본을 `<tmp>/laighthouse_mcp_responses/<session>/`에 남긴다 → `prepare.py --brand <브랜드> --target-date <T>`
→ 이 모듈이 (도구 + 인자)로 응답을 골라 base.json과 facts를 출력한다 → 모델은 응답 원문을 읽거나 옮겨 적지
않고, facts만 보고 요약 문장(s2 등)을 써서 `build_report.py`에 `{"base": <경로>, "s2": ...}`로 넘긴다.

응답 선택: 브랜드·날짜·grain·group_by·day_offset·filters·metrics가 계획과 같은 응답 중 가장 최근 것 하나.
다른 브랜드·날짜·인자의 응답은 무시한다. 같은 폴더 형식을 쓰는 laighthouse-plugin-external의 저장 훅
(`hooks/save_mcp_response.py`)이 남긴 응답도 그대로 읽는다.

출력(stdout JSON): {"base": 경로, "mode": {...}, "facts": {...}, "missing": [...], "errors": [...], "ask_user": {...}?}
- missing: 저장된 응답이 없는 호출 — 그 호출만 다시 보내고 prepare.py를 재실행한다.
- errors: 에러로 끝난 호출(응답 첫 줄 포함) — 해당 섹션은 base에서 빠져 "데이터 준비 중"이 된다.
- ask_user: 필수 지표 역할(cost/impression/click)을 못 찾았거나 모호할 때만 — 사용자에게 한 번에 묻고,
  답을 `--metric-keys '<JSON>'`으로 넘겨 재실행한다.
"""
import argparse
import calendar
import io
import json
import os
import re
import sys
import tempfile
import time
from datetime import date, timedelta

import report_kit as kit

ROOT = os.path.join(tempfile.gettempdir(), "laighthouse_mcp_responses")
WORK_ROOT = os.path.join(tempfile.gettempdir(), "laighthouse_prepare")
MAX_AGE = 24 * 3600
SPILL_RE = re.compile(r"Output has been saved to (\S+?)\.?\s*$", re.M)

# ── 응답 저장소 ───────────────────────────────────────────────────────────────


def _unwrap(text):
    """Cowork/Desktop의 {"result": "<본문>"} 래퍼를 벗긴다(중첩까지). JSON이 아니면 그대로."""
    for _ in range(3):
        if not isinstance(text, str) or not text.lstrip().startswith(("{", "[")):
            return text
        try:
            obj = json.loads(text)
        except ValueError:
            return text
        if isinstance(obj, dict) and "result" in obj and len(obj) == 1:
            inner = obj["result"]
            text = inner if isinstance(inner, str) else json.dumps(inner, ensure_ascii=False)
        elif isinstance(obj, list) and obj and all(isinstance(b, dict) and "text" in b for b in obj):
            text = "\n".join(b["text"] for b in obj)   # [{"type":"text","text":...}] 블록 리스트
        else:
            return text
    return text


def _response_text(rec):
    text = rec.get("response")
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False)
    m = SPILL_RE.search(text) if len(text) < 5000 else None
    path = rec.get("spilled_path") or (m.group(1) if m else None)
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            pass
    return _unwrap(text)


def load_records(brand):
    """저장 폴더 전체에서 이 브랜드의 응답 레코드(최근 MAX_AGE 이내)를 오래된 순으로."""
    recs = []
    now = time.time()
    try:
        sessions = os.listdir(ROOT)
    except OSError:
        return recs
    for s in sessions:
        folder = os.path.join(ROOT, s)
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if not name.endswith(".json"):
                continue
            path = os.path.join(folder, name)
            try:
                if now - os.path.getmtime(path) > MAX_AGE:
                    continue
                with open(path, encoding="utf-8") as f:
                    rec = json.load(f)
            except (OSError, ValueError):
                continue
            ti = rec.get("tool_input") or {}
            if not isinstance(ti, dict) or ti.get("brand_name") != brand:
                continue
            rec["_path"] = path
            rec["_tool"] = str(rec.get("tool_name") or "").rsplit("__", 1)[-1]
            recs.append(rec)
    recs.sort(key=lambda r: (r.get("saved_at") or 0, r["_path"]))
    return recs


def _norm_list(v):
    return [str(x) for x in v] if isinstance(v, list) else None


def _same_perf(ti, call):
    if str(ti.get("start_date") or "")[:10] != call["start_date"] or str(ti.get("end_date") or "")[:10] != call["end_date"]:
        return False
    if (ti.get("time_grain") or "day") != call["time_grain"]:
        return False
    if (_norm_list(ti.get("group_by")) or []) != call.get("group_by", []):
        return False
    off = ti.get("day_offset")
    if (int(off) if off not in (None, "") else None) != call.get("day_offset"):
        return False
    if ti.get("metrics") is not None:            # metrics 생략 호출만 (전체 지표)
        return False
    f = ti.get("filters") or {}
    want = call.get("filters") or {}
    return {k: sorted(map(str, v)) for k, v in f.items() if v} == {k: sorted(v) for k, v in want.items()}


def _matches(rec, call):
    ti = rec.get("tool_input") or {}
    if rec["_tool"] != call["tool"]:
        return False
    if call["tool"] == "get_ad_performance":
        return _same_perf(ti, call)
    if call["tool"] == "get_target_progress_v2":
        media = ti.get("media")
        media = None if media in (None, "", "all") else str(media)
        return (str(ti.get("month")) == call["month"] and str(ti.get("as_of_date") or "")[:10] == call["as_of_date"]
                and media == call.get("media"))
    if call["tool"] == "list_promotions":
        return (str(ti.get("start_date") or "")[:10] == call["start_date"]
                and str(ti.get("end_date") or "")[:10] == call["end_date"])
    return False


class Store:
    def __init__(self, brand):
        self.records = load_records(brand)
        self.missing, self.errors = [], []

    def find(self, call, required=True):
        """계획한 호출과 같은 최근 응답 → (텍스트, 레코드) | (None, None)."""
        hits = [r for r in self.records if _matches(r, call)]
        if not hits:
            if required:
                self.missing.append(describe(call))
            return None, None
        rec = hits[-1]
        return _response_text(rec), rec

    def envelope(self, call, required=True):
        """get_ad_performance 응답 봉투(dict) | None. 에러면 errors에 기록."""
        text, rec = self.find(call, required)
        if text is None:
            return None
        try:
            env = json.loads(text)
        except ValueError:
            env = None
        if not isinstance(env, dict) or not isinstance(env.get("rows"), list):
            self.errors.append({"call": describe(call), "response": str(text).strip().split("\n", 1)[0][:300]})
            return None
        return env

    def text(self, call, required=True):
        text, _ = self.find(call, required)
        return text


def describe(call):
    keys = ("tool", "start_date", "end_date", "time_grain", "group_by", "day_offset", "filters", "month", "as_of_date", "media")
    return {k: call[k] for k in keys if call.get(k) not in (None, [], {})}


def perf(start, end, grain, group_by=("media",), day_offset=None, filters=None):
    return {"tool": "get_ad_performance", "start_date": str(start), "end_date": str(end), "time_grain": grain,
            "group_by": list(group_by), "day_offset": day_offset, "filters": filters or {}}


def target(month, as_of, media=None):
    return {"tool": "get_target_progress_v2", "month": month, "as_of_date": str(as_of), "media": media}


def promotions(start, end):
    return {"tool": "list_promotions", "start_date": str(start), "end_date": str(end)}

# ── 날짜 ─────────────────────────────────────────────────────────────────────


def month_shift(d, delta):
    idx = d.year * 12 + d.month - 1 + delta
    return date(idx // 12, idx % 12 + 1, 1)


def ym(d):
    return f"{d.year:04d}-{d.month:02d}"

# ── 응답 해석 ─────────────────────────────────────────────────────────────────


def _md_tables(text):
    tables, cur = [], []
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                cur.append(cells)
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    return [[dict(zip(t[0], r)) for r in t[1:]] for t in tables if len(t) > 1]


def _num(v):
    try:
        x = float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def parse_targets(text):
    """get_target_progress_v2 응답 → {"all": {"cost", "revenue"}, "by_media": {media: {"cost", "revenue"}}}.
    한 줄 메시지·에러·0 표는 목표 없음(None). actual 열은 쓰지 않는다."""
    out = {"all": {"cost": None, "revenue": None}, "by_media": {}}
    tables = _md_tables(text)
    if not tables:
        return out
    for row in tables[0]:
        if row.get("metric") in ("cost", "revenue"):
            out["all"][row["metric"]] = _num(row.get("target"))
    for row in (tables[1] if len(tables) > 1 else []):
        if row.get("campaign_name", "-") not in ("-", "") or row.get("metric") not in ("cost", "revenue"):
            continue
        slot = out["by_media"].setdefault(row.get("media"), {"cost": None, "revenue": None})
        slot[row["metric"]] = _num(row.get("target"))
    return out


def match_media(name, keys):
    """목표 표의 media 값 → 응답 media 값. 정확 일치 → 대소문자 무시."""
    if name in keys:
        return name
    low = {str(k).lower(): k for k in keys}
    return low.get(str(name).lower())


def parse_promotions(text):
    try:
        obj = json.loads(text) if isinstance(text, str) else text
    except ValueError:
        return []
    if isinstance(obj, dict):
        obj = obj.get("result") or obj.get("promotions") or []
    return [{"title": p.get("title", ""), "start_date": str(p.get("start_date") or p.get("date_begin") or "")[:10],
             "end_date": str(p.get("end_date") or p.get("date_end") or "")[:10],
             "type": p.get("promotion_type")} for p in obj if isinstance(p, dict)]


def _per(r):
    return str(r.get("month") or r.get("date") or "")


def ad_rows(env, period=None):
    """광고 매체 행(media non-null). period가 있으면 그 월/일 행만."""
    rows = []
    for r in (env or {}).get("rows") or []:
        if r.get("media") is None:
            continue
        if period is not None and not str(r.get("month") or r.get("date") or "").startswith(period):
            continue
        rows.append(r)
    return rows


def role_sum(rows, key):
    if not key:
        return None
    vals = [r.get(key) for r in rows if isinstance(r.get(key), (int, float))]
    return sum(vals) if vals else 0


def role_values(rows, keys):
    return {role: role_sum(rows, k) for role, k in keys.items()}


def kpis(v, has_revenue):
    """역할 원자 값 → 효율 지표(합의 비율)."""
    out = {}
    if has_revenue:
        out["roas"] = kit.ratio(v.get("revenue"), v.get("cost"))
    out["ctr"] = kit.ratio(v.get("click"), v.get("impression"))
    out["cpc"] = kit.ratio(v.get("cost"), v.get("click"), 1.0)
    if v.get("conversion") is not None:
        out["cpa"] = kit.ratio(v.get("cost"), v.get("conversion"), 1.0)
    return out


def change(cur, base):
    """증감률(%) — base가 없거나 0이면 None."""
    if cur is None or base in (None, 0):
        return None
    return (cur - base) / base * 100


def rnd(v, d=1):
    if isinstance(v, float):
        return round(v, 2) if abs(v) < 10 else round(v, d) if abs(v) < 1000 else round(v)
    return v


def clean(obj):
    """facts 출력용 — 소수 반올림, None 제거."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items() if v is not None and v != [] and v != {}}
    if isinstance(obj, list):
        return [clean(v) for v in obj]
    return rnd(obj)


def with_kpis(v, has_revenue):
    out = dict(v)
    out.update(kpis(v, has_revenue))
    return out


def brief(v, has_revenue):
    """캠페인·광고그룹 facts용 — 서술에 쓰는 지표만 남긴다(출력 크기 절감)."""
    keep = ("cost", "revenue", "conversion", "click", "roas", "cpa", "cpc") if has_revenue else ("cost", "click", "impression", "ctr", "cpc", "conversion")
    return {k: v.get(k) for k in keep if v.get(k) is not None}


def roles_of(env_list, metric_keys_override=None):
    """디스커버리 대신 — 받은 media 봉투들로 media_list/has_organic/metric_keys/currency를 정한다."""
    rows, metrics, units, dims = [], [], {}, ["media"]
    for env in env_list:
        if not env:
            continue
        rows += env.get("rows") or []
        for m in env.get("metrics") or []:
            if m not in metrics:
                metrics.append(m)
        units.update({k: v for k, v in (env.get("metric_units") or {}).items() if v or k not in units})
    disc = kit.resolve_roles({"dimensions": dims, "metrics": metrics, "metric_units": units, "rows": rows})
    if metric_keys_override:
        disc["metric_keys"].update(metric_keys_override)
        disc["missing"] = [r for r in disc["missing"] if r not in metric_keys_override]
        disc["ambiguous"] = {k: v for k, v in disc["ambiguous"].items() if k not in metric_keys_override}
        disc["has_revenue"] = "revenue" in disc["metric_keys"]
    return disc


def overlapping_promos(promos, start, end, lead_days=7):
    """[start, end]와 겹치거나 start 직전 lead_days 안에 끝난 프로모션."""
    out = []
    for p in promos:
        try:
            s, e = date.fromisoformat(p["start_date"]), date.fromisoformat(p["end_date"])
        except ValueError:
            continue
        if e >= start - timedelta(days=lead_days) and s <= end:
            out.append(p)
    return out


def daily_dips(env, keys, roles, threshold=0.5):
    """매체별 일별 급감 — 그 매체 일 중앙값의 threshold 미만인 날. {media: {role: {"median", "days": [...]}}}"""
    by = {}
    for r in ad_rows(env):
        by.setdefault(r["media"], []).append(r)
    out = {}
    for media, rows in by.items():
        rows.sort(key=lambda r: str(r.get("date")))
        for role in roles:
            k = keys.get(role)
            vals = [r.get(k) for r in rows if isinstance(r.get(k), (int, float))]
            if len(vals) < 5:
                continue
            med = sorted(vals)[len(vals) // 2]
            if med <= 0:
                continue
            days = [{"date": str(r.get("date"))[:10], "value": r.get(k)} for r in rows
                    if isinstance(r.get(k), (int, float)) and r.get(k) < med * threshold]
            if days:
                out.setdefault(media, {})[role] = {"median": med, "days": days}
    return out


def total_daily_dips(env, keys, roles, threshold=0.5):
    """광고 매체 합계 기준 일별 급감 — 합계 일 중앙값의 threshold 미만인 날. {role: {"median", "days"}}"""
    by_day = {}
    for r in ad_rows(env):
        by_day.setdefault(str(r.get("date"))[:10], []).append(r)
    out = {}
    for role in roles:
        k = keys.get(role)
        series = sorted((d, role_sum(rows, k)) for d, rows in by_day.items())
        vals = [v for _, v in series if v is not None]
        if len(vals) < 5:
            continue
        med = sorted(vals)[len(vals) // 2]
        days = [{"date": d, "value": v} for d, v in series if med > 0 and v is not None and v < med * threshold]
        out[role] = {"median": med, "days": days}
    return out


def campaign_facts(env, cur, base, keys, has_revenue, top=12, shift=20.0):
    """캠페인 레벨 봉투(month grain, 전월 동기+당월) → 당월 광고비 상위 캠페인 + 효율 급변 캠페인."""
    vals = {}
    for r in ad_rows(env):
        slot = "cur" if _per(r).startswith(cur) else "base" if _per(r).startswith(base) else None
        if not slot:
            continue
        key = (r["media"], r.get("campaign_name") or kit.UNSET_LABEL)
        vals.setdefault(key, {})[slot] = {role: r.get(k) for role, k in keys.items()}
    eff = "roas" if has_revenue else "ctr"
    items = []
    for (media, name), v in vals.items():
        c = with_kpis(v.get("cur") or {}, has_revenue)
        b = with_kpis(v.get("base") or {}, has_revenue) if v.get("base") else None
        items.append({"media": media, "campaign": name, "cur": brief(c, has_revenue), "base": brief(b, has_revenue) if b else None,
                      "eff_change": change(c.get(eff), b.get(eff)) if b else None,
                      "cost_change": change(c.get("cost"), b.get("cost")) if b else None})
    items.sort(key=lambda x: -(x["cur"].get("cost") or 0))
    top_items = items[:top]
    shifted = [x for x in items[:40] if x not in top_items and x["eff_change"] is not None and abs(x["eff_change"]) >= shift
               and (x["cur"].get("cost") or 0) > 0]
    for x in top_items + shifted:
        x["eff_shift"] = x["eff_change"] is not None and abs(x["eff_change"]) >= shift
        # s5 후보 순위 — 광고비 × 효율 변화 폭이 큰 순 (같은 점수면 광고비 큰 순)
        x["pick_score"] = (x["cur"].get("cost") or 0) * abs(x["eff_change"] or 0) / 100
    return top_items, shifted[:8]


def adgroup_facts(env, campaigns, cur, base, keys, has_revenue, per=5):
    """상위 캠페인의 광고그룹(당월 광고비 상위 per개, 전월 동기에 없으면 new)."""
    want = {(c["media"], c["campaign"]) for c in campaigns}
    vals = {}
    for r in ad_rows(env):
        k = (r["media"], r.get("campaign_name") or kit.UNSET_LABEL)
        if k not in want:
            continue
        slot = "cur" if _per(r).startswith(cur) else "base" if _per(r).startswith(base) else None
        if slot:
            vals.setdefault(k, {}).setdefault(r.get("ad_group_name") or kit.UNSET_LABEL, {})[slot] = \
                {role: r.get(kk) for role, kk in keys.items()}
    out = []
    for c in campaigns:
        groups = vals.get((c["media"], c["campaign"]), {})
        rows = [{"ad_group": g, "new": "base" not in v, "cur": brief(with_kpis(v.get("cur") or {}, has_revenue), has_revenue),
                 "base": brief(with_kpis(v["base"], has_revenue), has_revenue) if v.get("base") else None}
                for g, v in groups.items() if v.get("cur")]
        rows.sort(key=lambda x: -(x["cur"].get("cost") or 0))
        out.append({"media": c["media"], "campaign": c["campaign"], "ad_groups": rows[:per],
                    "ad_group_count": len(rows), "new_count": sum(1 for x in rows if x["new"])})
    return out

# ── 작업 폴더·파생 봉투 ───────────────────────────────────────────────────────


def work_dir(brand, skill, target_date):
    safe = re.sub(r"[^\w.-]", "_", f"{brand}_{skill}_{target_date}")
    path = os.path.join(WORK_ROOT, safe)
    os.makedirs(path, exist_ok=True)
    return path


def save_envelope(folder, name, env):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(env, f, ensure_ascii=False)
    return path


def period_envelope(env, period):
    """봉투에서 한 기간(월/일) 행만 남긴 사본 — 범례의 기간 전체 값 등에 쓴다."""
    out = dict(env)
    out["rows"] = [r for r in env.get("rows") or [] if str(r.get("month") or r.get("date") or "").startswith(period)]
    out["row_count"] = len(out["rows"])
    return out


def merge_envelopes(envs):
    """매체별로 나눠 받은 같은 레벨 봉투들을 하나로 (폴백)."""
    envs = [e for e in envs if e]
    if not envs:
        return None
    out = dict(envs[0])
    out["rows"] = [r for e in envs for r in e.get("rows") or []]
    out["row_count"] = len(out["rows"])
    return out

# ── 스킬별 계획 ──────────────────────────────────────────────────────────────


def _s3_arrays(env, periods, keys):
    """광고 매체 행의 기간별 역할 합 배열(s3 차트)."""
    return {role: [role_sum(ad_rows(env, p), k) for p in periods] for role, k in keys.items()
            if role in ("cost", "revenue", "impression", "click")}


def _s1(tgt, month_rows, keys):
    v = role_values(month_rows, keys)
    s1 = {"목표_예산": tgt["all"]["cost"], "소진액": v.get("cost")}
    if keys.get("revenue"):
        s1.update({"목표_매출": tgt["all"]["revenue"], "기간_매출": v.get("revenue")})
    else:
        s1.update({"기간_노출": v.get("impression"), "기간_클릭": v.get("click")})
    return s1


def _level_env(store, start, end, grain, dims, day_offset, media_list):
    """계층 표 레벨 봉투 — 필터 없는 1회 응답, 없으면 매체별 응답을 합친다(5만 행 한도 폴백)."""
    call = perf(start, end, grain, dims, day_offset)
    env = store.envelope(call, required=False)
    if env:
        return env
    parts = [store.envelope(perf(start, end, grain, dims, day_offset, {"media": [m]}), required=False)
             for m in media_list]
    if any(parts):
        for m, part in zip(media_list, parts):
            if not part:
                store.missing.append(describe(perf(start, end, grain, dims, day_offset, {"media": [m]})))
        return merge_envelopes(parts)
    store.missing.append(describe(call))
    return None


def _levels(store, start, end, grain, day_offset, media_list):
    camp = _level_env(store, start, end, grain, ["media", "campaign_name"], day_offset, [])
    adg = _level_env(store, start, end, grain, ["media", "campaign_name", "ad_group_name"], day_offset, media_list)
    ad = _level_env(store, start, end, grain, ["media", "campaign_name", "ad_group_name", "ad_name"], day_offset, media_list)
    return camp, adg, ad


def _compare_rows(env, media_list, base, cur, keys, has_organic, names):
    """매체 성과 비교 표 rows — [{"name", <base 이름>: {역할: 값}, <cur 이름>: {...}}], Organic은 마지막."""
    nb, nc = names
    rows = []
    for m in media_list:
        rows.append({"name": m,
                     nb: role_values([r for r in ad_rows(env, base) if r["media"] == m], keys),
                     nc: role_values([r for r in ad_rows(env, cur) if r["media"] == m], keys)})
    if has_organic and keys.get("revenue"):
        org = [r for r in (env or {}).get("rows") or [] if r.get("media") is None]
        okeys = {k: v for k, v in keys.items() if k in ("revenue", "conversion")}
        rows.append({"name": "Organic",
                     nb: role_values([r for r in org if _per(r).startswith(base)], okeys),
                     nc: role_values([r for r in org if _per(r).startswith(cur)], okeys)})
    return rows


def _compare_facts(env, media_list, base, cur, keys, has_rev, labels):
    """facts의 total/by_media — 두 기간 합계·매체별 실적과 증감률(%)."""
    lb, lc = labels

    def pair(rows_b, rows_c):
        b = with_kpis(role_values(rows_b, keys), has_rev)
        c = with_kpis(role_values(rows_c, keys), has_rev)
        return {lc: c, lb: b, "change_pct": {k: change(c.get(k), b.get(k)) for k in c}}

    total = pair(ad_rows(env, base), ad_rows(env, cur))
    by_media = []
    for m in media_list:
        item = {"media": m}
        item.update(pair([r for r in ad_rows(env, base) if r["media"] == m],
                         [r for r in ad_rows(env, cur) if r["media"] == m]))
        by_media.append(item)
    return total, by_media


def _organic(env, keys, periods, has_organic):
    """Organic 매출과 비중(%) — Organic 있고 매출 있음 모드일 때만."""
    if not (has_organic and keys.get("revenue")):
        return None
    org = [r for r in (env or {}).get("rows") or [] if r.get("media") is None]
    out = {}
    for label, p in periods.items():
        o = role_sum([r for r in org if _per(r).startswith(p)], keys["revenue"])
        ad = role_sum(ad_rows(env, p), keys["revenue"])
        out[label] = {"organic_revenue": o, "ad_revenue": ad,
                      "organic_share_pct": kit.ratio(o, (o or 0) + (ad or 0)) if (o or ad) else None}
    return out


def _monthly_trend(env, T, keys, has_rev):
    return [dict(month=m, **with_kpis(role_values(ad_rows(env, m), keys), has_rev)) for m in kit.month_keys(T)]


def _mode(disc):
    keys = disc["metric_keys"]
    return {"has_revenue": bool(keys.get("revenue")), "has_organic": disc["has_organic"] and bool(keys.get("revenue")),
            "has_conversion": "conversion" in keys, "currency": disc["currency"]}


def _base_common(brand, skill, title, T, disc):
    return {"title": title, "target_date": str(T),
            "out": f"~/Downloads/laighthouse-reports/{brand}_{skill}_{T}.html",
            "metric_keys": disc["metric_keys"], "has_organic": disc["has_organic"], "currency": disc["currency"]}


def _pacing(T, tgt, spent, revenue, has_rev):
    days = calendar.monthrange(T.year, T.month)[1]
    return {"month_progress_pct": T.day / days * 100, "budget_burn_pct": kit.ratio(spent, tgt["all"]["cost"]),
            "target_budget": tgt["all"]["cost"], "target_revenue": tgt["all"]["revenue"] if has_rev else None,
            "target_roas": kit.ratio(tgt["all"]["revenue"], tgt["all"]["cost"]) if has_rev else None,
            "revenue_achievement_pct": kit.ratio(revenue, tgt["all"]["revenue"]) if has_rev else None}


def _discover(envs, override):
    disc = roles_of(envs, override)
    if disc["missing"] or disc["ambiguous"]:
        return disc, {"ask_user": {"missing": disc["missing"], "ambiguous": disc["ambiguous"],
                                   "metric_names": disc["metric_names"]}}
    return disc, None


def _finish(folder, base_input, facts):
    path = save_envelope(folder, "base.json", base_input)
    return {"base": path.replace("\\", "/"), "facts": facts}


def _campaign_block(facts, camp, adg, cur, base, keys, has_rev):
    if camp:
        top, shifted = campaign_facts(camp, cur, base, keys, has_rev)
        facts["campaigns_top_by_cost"] = top
        facts["campaigns_efficiency_shift"] = shifted
        if adg:
            facts["top_campaign_ad_groups"] = adgroup_facts(adg, top[:6], cur, base, keys, has_rev)


def _prev_same_period(T):
    m1 = month_shift(T, -1)
    return f"{m1}~{m1.replace(day=min(T.day, calendar.monthrange(m1.year, m1.month)[1]))}"


MONTH_TITLES = {"mtd-detailed": "MTD 보고서", "mtd-summary": "Executive MTD 보고서",
                "monthly-detailed": "월간 보고서", "monthly-summary": "Executive 월간 보고서"}


def _plan_month_family(store, brand, T, override, skill):
    """mtd-detailed / mtd-summary / monthly-detailed / monthly-summary — 6개월 month grain(day_offset) 공유 응답."""
    first = T.replace(day=1)
    m5, m1 = month_shift(T, -5), month_shift(T, -1)
    cur, base = ym(T), ym(m1)
    detailed = skill.endswith("detailed")
    promo_start = first if skill == "mtd-detailed" else first - timedelta(days=30)
    six = store.envelope(perf(m5, T, "month", ["media"], T.day))
    day = store.envelope(perf(first, T, "day", ["media"])) if skill == "mtd-detailed" else None
    tgt_text = store.text(target(cur, T))
    promo_text = store.text(promotions(promo_start, T))
    if not six:
        return None
    disc, ask = _discover([six] + ([day] if day else []), override)
    if ask:
        return ask
    keys, media_list = disc["metric_keys"], disc["media_list"]
    has_rev = bool(keys.get("revenue"))
    camp = adg = ad = None
    if detailed:
        camp, adg, ad = _levels(store, m1, T, "month", T.day, media_list)
    tgt = parse_targets(tgt_text)
    promos = parse_promotions(promo_text) if promo_text else []
    folder = work_dir(brand, skill, T)
    b = _base_common(brand, skill, f"{brand} {MONTH_TITLES[skill]}", T, disc)
    cur_rows = ad_rows(six, cur)
    b["s1"] = _s1(tgt, cur_rows, keys)
    b["s3"] = _s3_arrays(six, kit.month_keys(T), keys)
    six_path = save_envelope(folder, "six_month_media.json", six)
    level_files = [six_path] + [save_envelope(folder, f"level{i}.json", e)
                                for i, e in ((2, camp), (3, adg), (4, ad)) if e]
    compare = _compare_rows(six, media_list, base, cur, keys, disc["has_organic"], ("m1", "m0"))

    unmatched = []
    if skill == "mtd-detailed":
        if day:
            b["s4"] = {"json_files": [save_envelope(folder, "day_media.json", day)],
                       "total_json_files": [save_envelope(folder, "mtd_media_total.json", period_envelope(six, cur))],
                       "promotions": promos}
        by_media_tgt = {}
        for name, t in tgt["by_media"].items():
            hit = match_media(name, media_list)
            if hit:
                by_media_tgt[hit] = t
            else:
                unmatched.append(name)
        rows6 = []
        for m in media_list:
            v = role_values([r for r in cur_rows if r["media"] == m], keys)
            t = by_media_tgt.get(m, {})
            row = {"name": m, "월_예산": t.get("cost"), "목표_매출": t.get("revenue") if has_rev else None}
            row.update({k: v.get(k) for k in ("cost", "revenue", "impression", "click") if k in v})
            rows6.append(row)
        b["s6"] = {"rows": rows6}
        b["s7"] = {"json_files": level_files}
    elif skill == "monthly-detailed":
        b["s4"] = {"rows": compare}
        b["s5"] = {"json_files": level_files}
    else:   # mtd-summary / monthly-summary
        b["s4"] = {"json_files": [six_path]}
        b["s5"] = {"rows": compare}

    lb, lc = ("prev_same_period", "mtd") if skill.startswith("mtd") else ("prev_month", "this_month")
    total, by_media = _compare_facts(six, media_list, base, cur, keys, has_rev, (lb, lc))
    facts = {"mode": _mode(disc),
             "period": {lc: f"{first}~{T}", lb: _prev_same_period(T)},
             "pacing": _pacing(T, tgt, total[lc].get("cost"), total[lc].get("revenue"), has_rev),
             "total": total, "by_media": by_media,
             "promotions": overlapping_promos(promos, first, T, lead_days=7 if skill == "mtd-detailed" else 30)}
    if skill == "mtd-detailed":
        for item, row in zip(facts["by_media"], b["s6"]["rows"]):
            item.update({"budget": row["월_예산"], "target_revenue": row.get("목표_매출"),
                         "burn_pct": kit.ratio(item[lc].get("cost"), row["월_예산"])})
        if day:
            roles = ["cost", "revenue" if has_rev else "click"]
            facts["daily_dips_total"] = total_daily_dips(day, keys, roles)
            facts["daily_dips_by_media"] = daily_dips(day, keys, roles)
    else:
        facts["monthly_trend"] = _monthly_trend(six, T, keys, has_rev)
    org = _organic(six, keys, {lc: cur, lb: base}, disc["has_organic"])
    if org:
        facts["organic"] = org
    _campaign_block(facts, camp, adg, cur, base, keys, has_rev)
    if unmatched:
        facts["target_media_unmatched"] = unmatched
    return _finish(folder, b, facts)


def _plan_day_family(store, brand, T, override, skill):
    """daily-detailed / daily-summary — 7일 day grain 공유 응답 + 당월 month grain(목표 카드 실적)."""
    first = T.replace(day=1)
    d6, d1 = T - timedelta(days=6), T - timedelta(days=1)
    detailed = skill == "daily-detailed"
    promo_start = d6 if detailed else T - timedelta(days=7)
    month = store.envelope(perf(first, T, "month", ["media"]))
    week = store.envelope(perf(d6, T, "day", ["media"]))
    week_total = None if detailed else store.envelope(perf(d6, T, "total", ["media"]))
    tgt_text = store.text(target(ym(T), T))
    promo_text = store.text(promotions(promo_start, T))
    if not week:
        return None
    disc, ask = _discover([e for e in (month, week) if e], override)
    if ask:
        return ask
    keys, media_list = disc["metric_keys"], disc["media_list"]
    has_rev = bool(keys.get("revenue"))
    camp = adg = ad = None
    if detailed:
        camp, adg, ad = _levels(store, d1, T, "day", None, media_list)
    tgt = parse_targets(tgt_text)
    promos = parse_promotions(promo_text) if promo_text else []
    folder = work_dir(brand, skill, T)
    title = f"{brand} 데일리 보고서" if detailed else f"{brand} Executive 데일리 보고서"
    b = _base_common(brand, skill, title, T, disc)
    days = kit.day_keys(d6, T)
    month_rows = ad_rows(month, ym(T)) if month else []
    if month:
        b["s1"] = _s1(tgt, month_rows, keys)
    b["s3"] = dict(_s3_arrays(week, days, keys),
                   promotions=[{k: p[k] for k in ("title", "start_date", "end_date")} for p in promos])
    week_path = save_envelope(folder, "week_media.json", week)
    if detailed:
        b["s4"] = {"json_files": [week_path] + [save_envelope(folder, f"level{i}.json", e)
                                                for i, e in ((2, camp), (3, adg), (4, ad)) if e]}
    else:
        b["s4"] = {"json_files": [week_path], "promotions": promos}
        if week_total:
            b["s4"]["total_json_files"] = [save_envelope(folder, "week_total.json", week_total)]
        b["s5"] = {"rows": _compare_rows(week, media_list, str(d1), str(T), keys, disc["has_organic"], ("d1", "d0"))}

    total, by_media = _compare_facts(week, media_list, str(d1), str(T), keys, has_rev, ("d1", "d0"))
    facts = {"mode": _mode(disc), "period": {"d0": str(T), "d1": str(d1), "week": f"{d6}~{T}"},
             "total": total, "by_media": by_media,
             "daily_7d": [dict(date=d, **with_kpis(role_values(ad_rows(week, d), keys), has_rev)) for d in days],
             "promotions": overlapping_promos(promos, d6 if detailed else T, T, lead_days=7)}
    if month:
        mv = role_values(month_rows, keys)
        facts["pacing"] = _pacing(T, tgt, mv.get("cost"), mv.get("revenue"), has_rev)
        facts["mtd"] = with_kpis(mv, has_rev)
    org = _organic(week, keys, {"d0": str(T), "d1": str(d1)}, disc["has_organic"])
    if org:
        facts["organic"] = org
    _campaign_block(facts, camp, adg, str(T), str(d1), keys, has_rev)
    return _finish(folder, b, facts)


def _bind(fn, skill):
    return lambda store, brand, T, override: fn(store, brand, T, override, skill)


PLANS = {s: _bind(_plan_month_family, s) for s in MONTH_TITLES}
PLANS.update({s: _bind(_plan_day_family, s) for s in ("daily-detailed", "daily-summary")})


# ── creative (소재 단위 7일 total·day + 매체 total) ──────────────────────────────

CREATIVE_DIMS = ["media", "campaign_name", "ad_group_name", "ad_name"]


def _import_asset(assets_dir, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(assets_dir, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _halves(series, head=3):
    """일별 시리즈 → {"first3_avg", "last4_avg", "change_pct"} (None 제외 평균)."""
    def avg(xs):
        xs = [x for x in xs if isinstance(x, (int, float))]
        return sum(xs) / len(xs) if xs else None
    a, b = avg(series[:head]), avg(series[head:])
    return {"first3_avg": a, "last4_avg": b, "change_pct": change(b, a)}


def _plan_creative(store, brand, T, override, skill, media=None, assets_dir=None):
    """creative-detailed / creative-summary — 필터 없는 소재 단위 7일 응답에서 매체를 고르고 랭킹·시리즈를 만든다."""
    d6 = T - timedelta(days=6)
    media_env = store.envelope(perf(d6, T, "total", ["media"]))
    if not media_env:
        return None
    disc, ask = _discover([media_env], override)
    if ask:
        return ask
    keys, media_list = disc["metric_keys"], disc["media_list"]
    tot = _level_env(store, d6, T, "total", CREATIVE_DIMS, None, media_list)
    day = _level_env(store, d6, T, "day", CREATIVE_DIMS, None, media_list)
    if not tot:
        return None
    rank_mod = _import_asset(assets_dir, "rank_creatives")
    series_mod = _import_asset(assets_dir, "creative_daily_series")

    named = {}
    for r in tot.get("rows") or []:
        if r.get("media") is not None and rank_mod.has_ad_name(r.get("ad_name")):
            named[r["media"]] = named.get(r["media"], 0) + 1
    candidates = [m for m in media_list if named.get(m)]
    if media:
        hit = match_media(media, media_list)
        if not hit:
            return {"ask_user": {"choose_media": candidates, "reason": f"'{media}'는 이 브랜드의 매체가 아니다",
                                 "media_list": media_list}}
        chosen = hit
    elif len(candidates) == 1:
        chosen = candidates[0]
    elif not candidates:
        return {"stop": "소재 단위 데이터(소재명)가 있는 매체가 없다 — 보고서를 만들 수 없다고 사용자에게 알린다.",
                "media_list": media_list}
    else:
        return {"ask_user": {"choose_media": candidates, "named_ad_count": {m: named[m] for m in candidates},
                             "excluded": {m: "소재명 있는 행 없음" for m in media_list if m not in candidates}},
                "note": "MCP를 다시 부르지 않는다 — 사용자가 고른 매체로 prepare.py를 --media <매체>로 재실행한다."}

    folder = work_dir(brand, f"{skill}_{chosen}", T)
    rows = [r for r in tot.get("rows") or [] if r.get("media") == chosen]
    if not rows:
        return {"ask_user": {"choose_media": candidates, "reason": f"{chosen}에 최근 7일 소재 행이 없다"}}
    rank = rank_mod.rank_main({"rows": rows, "metric_keys": keys, "chosen_media": chosen,
                               "s5": skill == "creative-detailed"})
    rank_path = save_envelope(folder, "rank.json", rank)
    dates = kit.day_keys(d6, T)
    series = None
    if day:
        drows = [r for r in day.get("rows") or [] if r.get("media") == chosen]
        mk = series_mod.resolve_metric_keys(set(day.get("metrics") or []), keys)
        series = {"dates": dates, "has_revenue": bool(mk.get("revenue")),
                  "overall": series_mod.compute_overall(drows, dates, mk)}
        if rank.get("top5_keys"):
            series["top5"] = series_mod.compute_top5(drows, dates, rank["top5_keys"], mk)
    title = f"{brand} 소재 보고서" if skill == "creative-detailed" else f"{brand} Executive 소재 보고서"
    b = {"title": title, "target_date": str(T), "out": f"~/Downloads/laighthouse-reports/{brand}_{skill}_{T}.html",
         "metric_keys": keys, "currency": disc["currency"], "rank_file": rank_path.replace("\\", "/"),
         "s1": {}, "s3": {}, "s4": {}, "s5": {}}
    if series:
        b["series_file"] = save_envelope(folder, "series.json", series).replace("\\", "/")
    else:
        for k in ("s3", "s4") + (("s5",) if skill == "creative-summary" else ()):
            b.pop(k)
    facts = {"mode": _mode(disc), "period": f"{d6}~{T}", "chosen_media": chosen, "candidates": candidates,
             "media_totals": rank.get("media_totals"), "eligibility": rank.get("eligibility"),
             "best": rank.get("s1"), "top_by_cost": rank.get("top_by_cost"),
             "top5": [dict(name=n, **{k: v for k, v in tot5.items()},
                           ctr_series=series["top5"]["ctr_series"][i],
                           **({"roas_series": series["top5"]["roas_series"][i]} if series and series.get("has_revenue")
                              else {"click_series": series["top5"]["click_series"][i]}))
                      for i, (n, tot5) in enumerate(zip(rank.get("top5_names") or [], (series or {}).get("top5", {}).get("totals") or []))]
             if series and series.get("top5") else None,
             "overall_daily": {k: v for k, v in ((series or {}).get("overall") or {}).items() if k != "totals"} or None,
             "dates": dates}
    # 추이 판단용 — 앞 3일 vs 뒤 4일 평균 (섹션 문서의 "초반 vs 후반" 비교)
    for item in facts.get("top5") or []:
        item["trend"] = {k: _halves(item[k]) for k in ("ctr_series", "roas_series", "click_series") if k in item}
    if facts.get("overall_daily"):
        facts["overall_trend"] = {k: _halves(v) for k, v in facts["overall_daily"].items() if isinstance(v, list)}
    out = _finish(folder, b, facts)
    out["lookups"] = rank.get("lookups") or []
    return out


PLANS.update({s: (lambda n: (lambda store, brand, T, override, **kw: _plan_creative(store, brand, T, override, n, **kw)))(s)
              for s in ("creative-detailed", "creative-summary")})

# ── 진입점 ───────────────────────────────────────────────────────────────────


def main(skill, argv=None, assets_dir=None):
    ap = argparse.ArgumentParser(description=f"{skill} prepare")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--metric-keys", default=None, help='사용자 답으로 정한 역할 키 JSON, 예: {"revenue":"매출_AB"}')
    ap.add_argument("--media", default=None, help="소재 보고서: 분석할 매체(사용자가 지정했거나 고른 값)")
    a = ap.parse_args(argv)
    T = date.fromisoformat(a.target_date)
    store = Store(a.brand)
    override = json.loads(a.metric_keys) if a.metric_keys else None
    kw = {"media": a.media, "assets_dir": assets_dir} if skill.startswith("creative") else {}
    result = PLANS[skill](store, a.brand, T, override, **kw) or {}
    if "facts" in result:
        result["facts"] = clean(result["facts"])
    result["missing"] = store.missing
    result["errors"] = store.errors
    if not store.records:
        result["note"] = (f"저장된 응답이 없다({ROOT}). 플러그인 저장 훅이 꺼져 있으면 응답이 남지 않는다 — "
                          "SKILL.md의 '훅이 없을 때' 절차를 따른다.")
    # 소재 스크립트 import가 sys.stdout을 다시 감쌀 수 있어 fd 1에 바로 쓴다(Windows cp949 콘솔에서도 UTF-8).
    sys.stdout.flush()
    os.write(1, json.dumps(result, ensure_ascii=False).encode("utf-8"))
