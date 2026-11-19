#!/usr/bin/env python3
"""Executive Summary 작성 근거(digest) — prepare.py가 base.json으로 만든다(모델이 직접 import 하지 않는다).

monthly-report·mtd-report가 같은 파일을 쓴다(스킬 폴더 이름으로 기간 라벨만 다르다). 요약 가이드
(monthly: guides/executive-summary.md, mtd: guides/weekly-summary.md)의 [소진]·[효율]을 쓸 숫자를 화면에 쓸 문자열로
미리 만들어 둔다 — 모델은 값을 다시 계산하지 않고 그대로 옮긴다.

입력: base.json의 summary_input
  levels      — [매체 6개월 month 응답, 캠페인, 광고그룹, 광고 month 응답] 경로(없는 레벨은 빠진다)
  periods     — {"cur": "YYYY-MM", "base": "YYYY-MM"}
  budget      — 브랜드 월 목표 {"cost", "revenue"}(없으면 빈 dict)
  media_budget— {매체: {"cost", "revenue"}}
값 "-"는 그 기간 집행이 없었다는 뜻이다(변화 "신규" = 전월에 없음, "중단" = 당월에 없음).
출력: {"기간", "전체", "예산"?, "매체": [...], "매체-캠페인": [...], "매체-캠페인-광고그룹": [...], "매체-캠페인-광고그룹-광고": [...],
       "<단위> 생략"?} — 행은 {"이름", <당월>, <전월>, <전월 대비>} (값은 표시 문자열)
"""
import calendar
import json
import os
from datetime import date

SKILL = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).rsplit(":", 1)[-1]
MTD = SKILL == "mtd-report"
CUR, BASE, CHANGE = ("당월", "전월 동기", "전월 동기 대비") if MTD else ("당월", "전월", "전월 대비")

VIEW_NAMES = ("조회수", "views", "video_views", "동영상 조회수")   # CPV를 계산할 수 있는 원자 지표
LEVELS = (("매체-캠페인", ["media", "campaign_name"], 10),
          ("매체-캠페인-광고그룹", ["media", "campaign_name", "ad_group_name"], 10),
          ("매체-캠페인-광고그룹-광고", ["media", "campaign_name", "ad_group_name", "ad_name"], 5))


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _z(v, d):
    """반올림해 -0.0을 +0.0으로 — "-0.0%" 표기를 막는다."""
    return round(v, d) + 0.0


def atoms_of(keys, metrics):
    """역할 → 응답 지표 이름. 조회수는 역할 맵에 없어 이름으로 찾는다."""
    out = {r: keys[r] for r in ("cost", "impression", "click", "revenue", "conversion") if keys.get(r)}
    views = next((m for m in VIEW_NAMES if m in metrics), None)
    if views:
        out["views"] = views
    return out


def group(env, dims, period, atoms):
    """봉투에서 period 달의 행을 dims 묶음별로 합친다(광고 매체 행만) → {묶음: {역할: 합}}."""
    out = {}
    for r in (env or {}).get("rows") or []:
        if not str(r.get("month") or r.get("date") or "").startswith(period) or r.get("media") is None:
            continue
        k = tuple("(미지정)" if r.get(d) in (None, "", "-") else str(r.get(d)) for d in dims)
        slot = out.setdefault(k, {a: 0 for a in atoms})
        for a, m in atoms.items():
            v = _num(r.get(m))
            if v is not None:
                slot[a] += v
    return out


def ratios(v):
    """원자 합 → 효율 지표(합의 비율)."""
    cost, imp, clk = v.get("cost"), v.get("impression"), v.get("click")
    out = dict(v)
    out["ctr"] = clk / imp * 100 if imp else None
    out["cpc"] = cost / clk if clk else None
    out["cpm"] = cost / imp * 1000 if imp else None
    if "views" in v:
        out["cpv"] = cost / v["views"] if v["views"] else None
    if "revenue" in v:
        out["roas"] = v["revenue"] / cost * 100 if cost else None
    return out


def make_fmt(atoms, currency):
    money = lambda v: "-" if v is None else (f"{currency}{v:,.0f}" if abs(v) >= 100 else f"{currency}{v:,.1f}")  # noqa: E731
    count = lambda v: "-" if v is None else f"{round(v):,}"  # noqa: E731
    pct = lambda d: (lambda v: "-" if v is None else f"{v:,.{d}f}%")  # noqa: E731
    # (표시 이름, 키, 포맷, %지표 여부) — 지표가 응답에 없으면 뺀다
    spec = [("광고비", "cost", money, False), ("노출", "impression", count, False), ("클릭", "click", count, False)]
    if "views" in atoms:
        spec.append(("조회수", "views", count, False))
    if "conversion" in atoms:
        spec.append(("전환", "conversion", count, False))
    if "revenue" in atoms:
        spec.append(("매출", "revenue", money, False))
    if "views" in atoms:
        spec.append(("CPV", "cpv", money, False))
    spec += [("CPM", "cpm", money, False), ("CTR", "ctr", pct(2), True), ("CPC", "cpc", money, False)]
    if "revenue" in atoms:
        spec.append(("ROAS", "roas", pct(1), True))

    # 광고비가 없는 기간(행이 없거나 0)은 집행 없음 — 값은 모두 "-", 변화는 모두 "신규"/"중단"
    def fmt(v):
        v = ratios(v) if v and v.get("cost") else {}
        return {name: f(v.get(k)) if v else "-" for name, k, f, _ in spec}

    def change(a, b):
        ca, cb = (a or {}).get("cost") or 0, (b or {}).get("cost") or 0
        if not ca or not cb:
            word = "-" if not ca and not cb else ("신규" if ca else "중단")
            return {name: word for name, *_ in spec}
        a, b = ratios(a), ratios(b)
        out = {}
        for name, k, _, is_pct in spec:
            x, y = a.get(k), b.get(k)
            if x is None or y is None:
                out[name] = "-"
            elif is_pct:
                out[name] = f"{_z(x - y, 2 if name == 'CTR' else 1):+.{2 if name == 'CTR' else 1}f}%p"
            elif not y:
                out[name] = "-"
            else:
                out[name] = f"{_z((x - y) / abs(y) * 100, 1):+.1f}%"
        return out

    return fmt, change


def build(base_path):
    base = _load(base_path)
    si = base.get("summary_input") or {}
    keys, currency = base.get("metric_keys") or {}, base.get("currency") or "₩"
    cur, prev = si["periods"]["cur"], si["periods"]["base"]
    envs = [_load(p) for p in si.get("levels") or []]
    if not envs:
        return {}
    atoms = atoms_of(keys, set(envs[0].get("metrics") or []))
    fmt, change = make_fmt(atoms, currency)

    def row(name, a, b):
        return {"이름": name, CUR: fmt(a), BASE: fmt(b), CHANGE: change(a, b)}

    T = date.fromisoformat(base["target_date"])
    if MTD:
        pd = min(T.day, calendar.monthrange(int(prev[:4]), int(prev[5:]))[1])
        period = {CUR: f"{cur}-01~{T.isoformat()}", BASE: f"{prev}-01~{prev}-{pd:02d}"}
    else:
        period = {CUR: f"{cur} (1일~{T.day}일)", BASE: f"{prev} (한 달 전체)"}
    out = {"기간": period}

    m_cur, m_prev = group(envs[0], ["media"], cur, atoms), group(envs[0], ["media"], prev, atoms)
    tot = lambda g: {a: sum(v[a] for v in g.values()) for a in atoms} if g else {}  # noqa: E731
    t0, t1 = tot(m_cur), tot(m_prev)
    if t0:
        out["전체"] = row("전체", t0, t1)
    bud = _num((si.get("budget") or {}).get("cost"))
    if bud and t0:
        b = {"월예산": fmt({"cost": bud, "impression": 0, "click": 0})["광고비"],
             "소진율": f"{t0['cost'] / bud * 100:.1f}%"}
        if MTD:
            b["월 진행률"] = f"{T.day / calendar.monthrange(T.year, T.month)[1] * 100:.1f}%"
        out["예산"] = b

    names = sorted(set(m_cur) | set(m_prev), key=lambda k: (-(m_cur.get(k) or {}).get("cost", 0), k))
    total_cost = t0.get("cost") or 0
    mb = si.get("media_budget") or {}
    media = []
    for k in names:
        a = m_cur.get(k) or {}
        r = row(k[0], a, m_prev.get(k) or {})
        r["광고비비중"] = f"{(a.get('cost') or 0) / total_cost * 100:.1f}%" if total_cost else "-"
        mbud = _num((mb.get(k[0]) or {}).get("cost"))
        if mbud:
            r["월예산"] = fmt({"cost": mbud, "impression": 0, "click": 0})["광고비"]
            r["소진율"] = f"{(a.get('cost') or 0) / mbud * 100:.1f}%"
        media.append(r)
    if media:
        out["매체"] = media

    dims_of = lambda e: set(e.get("dimensions") or [])  # noqa: E731
    for name, ds, top in LEVELS:
        env = next((e for e in envs[1:] if dims_of(e) - {"month", "date"} == set(ds)), None)
        if env is None:
            continue
        g0, g1 = group(env, ds, cur, atoms), group(env, ds, prev, atoms)
        keys_ = set(g0) | set(g1)
        c = lambda k, g: (g.get(k) or {}).get("cost", 0)  # noqa: E731
        by_cost = sorted(keys_, key=lambda k: (-c(k, g0), k))[:top]   # 같은 값이면 이름순(실행마다 같게)
        by_move = sorted(keys_, key=lambda k: (-abs(c(k, g0) - c(k, g1)), k))[:top]
        pick = sorted(set(by_cost) | set(by_move), key=lambda k: (-c(k, g0), k))
        out[name] = [row(" / ".join(k), g0.get(k) or {}, g1.get(k) or {}) for k in pick]
        if len(keys_) > len(pick):
            out[name + " 생략"] = f"광고비 상위 {top}개 + 광고비 변동 상위 {top}개만 — 나머지 {len(keys_) - len(pick)}개"
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(build(sys.argv[1]), ensure_ascii=False, indent=1))
