#!/usr/bin/env python3
"""Daily Summary 작성 근거(digest) — 모델이 직접 부르지 않는다. prepare.py가 base.json으로 만들어 출력에 붙인다.

digest는 모델이 「Daily Summary」(guides/daily-summary.md)를 쓸 근거다. 값은 화면에 쓸 문자열로 만들어 두고 전일 대비
변화와 급변 구분도 미리 계산한다 — 모델은 다시 계산하지 않고 그대로 옮긴다.

입력: base.json의 `summary_input` — `levels`(매체 레벨 7일 day 응답 + 캠페인·광고그룹·광고 day 응답 경로),
`periods`(cur = 기준일, base = 전일), 그리고 `metric_keys`·`currency`.

출력:
  {"기준일", "전일", "지표": [라벨...],
   "전체": 행, "매체": [행...],
   "매체-캠페인" | "매체-캠페인-광고그룹" | "매체-캠페인-광고그룹-광고": [행...], "<단위> 생략": "...",
   "급변 기준": "..."}
  행 = {"이름", "기준일": {라벨: 값} | "-", "전일": {라벨: 값} | "-", "전일 대비": {라벨: 변화}, "구분"?: "..."}
  - 세부 단위는 기준일 광고비 상위 + 전일 대비 광고비 변동(절대액) 상위를 합친 행이다(이름 `매체 / 캠페인 / …`).
  - 집행이 없던 날은 "-"(전일 "-" = 신규 집행, 기준일 "-" = 집행 중단).
  - "구분": 신규 집행 / 집행 중단 / 광고비 급등(+30% 이상) / 광고비 급락(-30% 이하) /
    효율 급변(광고비 변화는 30% 미만인데 CPV·CPM·CTR이 20% 이상 변함) 가운데 하나. 해당 없으면 키가 없다.
  - 전주 같은 요일 값은 이 보고서의 응답에 없어 넣지 않는다.
"""
import json
import os

MEDIA_TOP = 15
LEVELS = (("매체-캠페인", ["media", "campaign_name"], 10),
          ("매체-캠페인-광고그룹", ["media", "campaign_name", "ad_group_name"], 10),
          ("매체-캠페인-광고그룹-광고", ["media", "campaign_name", "ad_group_name", "ad_name"], 5))
SPEND_JUMP = 30.0      # 광고비 급등·급락 기준(%)
EFF_JUMP = 20.0        # 효율 급변 기준(%) — CPV·CPM·CTR
VIEW_NAMES = ("조회수", "views", "video_views")   # 조회수 지표 이름 후보(역할 키에 없을 때)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _atoms(keys, metrics):
    """원자 지표(합산 가능) → 응답의 실제 지표 이름."""
    atoms = {r: keys.get(r) for r in ("cost", "impression", "click", "revenue", "conversion") if keys.get(r)}
    view = keys.get("views") or next((m for m in VIEW_NAMES if m in metrics), None)
    if view:
        atoms["views"] = view
    return atoms


def _sum(rows, atoms):
    out = {r: 0.0 for r in atoms}
    for row in rows:
        for r, k in atoms.items():
            v = row.get(k)
            if isinstance(v, (int, float)):
                out[r] += v
    return out


def _ratios(v):
    """원자 합 → 비율 지표(합의 비율). 분모가 0이면 None."""
    def div(a, b, scale=1.0):
        return a / b * scale if b else None
    out = dict(v)
    out["ctr"] = div(v.get("click", 0), v.get("impression", 0), 100)
    out["cpc"] = div(v.get("cost", 0), v.get("click", 0))
    out["cpm"] = div(v.get("cost", 0), v.get("impression", 0), 1000)
    if "views" in v:
        out["cpv"] = div(v.get("cost", 0), v["views"])
    if "revenue" in v:
        out["roas"] = div(v["revenue"], v.get("cost", 0), 100)
    return out


def _money(v, cur):
    if v is None:
        return "-"
    return f"{cur}{v:,.1f}" if abs(v) < 100 else f"{cur}{v:,.0f}"


def _labels(atoms):
    """(라벨, 역할, 종류) — 종류: money/count/pct2/pct1."""
    out = [("광고비", "cost", "money"), ("노출", "impression", "count"), ("클릭", "click", "count")]
    if "views" in atoms:
        out.append(("조회수", "views", "count"))
    if "conversion" in atoms:
        out.append(("전환", "conversion", "count"))
    if "revenue" in atoms:
        out.append(("매출", "revenue", "money"))
    out += [("CTR", "ctr", "pct2"), ("CPC", "cpc", "money"), ("CPM", "cpm", "money")]
    if "views" in atoms:
        out.append(("CPV", "cpv", "money"))
    if "revenue" in atoms:
        out.append(("ROAS", "roas", "pct1"))
    return out


def _fmt(v, kind, cur):
    if v is None:
        return "-"
    if kind == "money":
        return _money(v, cur)
    if kind == "count":
        return f"{v:,.0f}"
    return f"{v:,.{2 if kind == 'pct2' else 1}f}%"


def _change(a, b, kind):
    """전일 대비 — % 지표는 %p 차, 나머지는 변화율(소수 1자리). 비교할 수 없으면 "-"."""
    if a is None or b is None:
        return "-"
    if kind in ("pct1", "pct2"):
        return f"{a - b:+.{2 if kind == 'pct2' else 1}f}%p"
    if not b:
        return "-"
    return f"{(a - b) / abs(b) * 100:+.1f}%"


def _rate(a, b):
    return (a - b) / abs(b) * 100 if a is not None and b else None


def _kind(cur, base):
    """급변 구분 — 신규 집행·집행 중단·광고비 급등/급락·효율 급변. 해당 없으면 None."""
    c0, c1 = (cur or {}).get("cost") or 0, (base or {}).get("cost") or 0
    if c0 and not c1:
        return "신규 집행"
    if c1 and not c0:
        return "집행 중단"
    if not c0:
        return None
    r = _rate(c0, c1)
    if r is not None and r >= SPEND_JUMP:
        return "광고비 급등"
    if r is not None and r <= -SPEND_JUMP:
        return "광고비 급락"
    for k in ("cpv", "cpm", "ctr"):
        e = _rate(cur.get(k), base.get(k))
        if e is not None and abs(e) >= EFF_JUMP:
            return "효율 급변"
    return None


def _group(env, dims, atoms, day):
    """day 응답에서 한 날짜의 행을 dims로 묶어 원자 합·비율. media가 없는 행(Organic)은 뺀다."""
    out = {}
    for row in (env or {}).get("rows") or []:
        if str(row.get("date") or "")[:10] != day or row.get("media") is None:
            continue
        key = tuple("(미지정)" if row.get(d) in (None, "", "-") else str(row.get(d)) for d in dims)
        out.setdefault(key, []).append(row)
    return {k: _ratios(_sum(rows, atoms)) for k, rows in out.items()}


def build(base_path):
    base = _load(base_path)
    si = base.get("summary_input") or {}
    keys = base.get("metric_keys") or {}
    cur = base.get("currency") or "₩"
    d0, d1 = si.get("periods", {}).get("cur"), si.get("periods", {}).get("base")
    envs = [_load(p) for p in si.get("levels") or [] if os.path.exists(p)]
    metrics = {m for e in envs for m in e.get("metrics") or []}
    atoms = _atoms(keys, metrics)
    labels = _labels(atoms)

    def vals(v):
        if not v or not (v.get("cost") or v.get("impression")):
            return "-"
        return {lab: _fmt(v.get(role), kind, cur) for lab, role, kind in labels}

    def row(name, v0, v1):
        r = {"이름": name, "기준일": vals(v0), "전일": vals(v1),
             "전일 대비": {lab: _change((v0 or {}).get(role), (v1 or {}).get(role), kind) for lab, role, kind in labels}}
        k = _kind(v0, v1)
        if k:
            r["구분"] = k
        return r

    out = {"기준일": d0, "전일": d1, "지표": [lab for lab, _, _ in labels],
           "급변 기준": f"광고비 전일 대비 ±{SPEND_JUMP:.0f}% · 효율(CPV·CPM·CTR) ±{EFF_JUMP:.0f}%"}
    by_dims = {tuple(d for d in e.get("dimensions") or [] if d != "date"): e for e in envs}
    media_env = by_dims.get(("media",))
    if media_env:
        g0, g1 = _group(media_env, ["media"], atoms, d0), _group(media_env, ["media"], atoms, d1)
        tot0 = _ratios({r: sum(v.get(r, 0) for v in g0.values()) for r in atoms})
        tot1 = _ratios({r: sum(v.get(r, 0) for v in g1.values()) for r in atoms})
        out["전체"] = row("전체", tot0, tot1)
        names = sorted(set(g0) | set(g1), key=lambda k: -((g0.get(k) or {}).get("cost") or 0))
        out["매체"] = [row(k[0], g0.get(k), g1.get(k)) for k in names[:MEDIA_TOP]]
    for name, dims, top in LEVELS:
        env = by_dims.get(tuple(dims))
        if not env:
            continue
        g0, g1 = _group(env, dims, atoms, d0), _group(env, dims, atoms, d1)
        keys_all = set(g0) | set(g1)
        c = lambda k, g: (g.get(k) or {}).get("cost") or 0  # noqa: E731
        by_cost = sorted(keys_all, key=lambda k: (-c(k, g0), k))[:top]
        by_move = sorted(keys_all, key=lambda k: (-abs(c(k, g0) - c(k, g1)), k))[:top]
        pick = sorted(set(by_cost) | set(by_move), key=lambda k: (-c(k, g0), k))
        out[name] = [row(" / ".join(k), g0.get(k), g1.get(k)) for k in pick]
        if len(keys_all) > len(pick):
            out[name + " 생략"] = f"기준일 광고비 상위 {top}개 + 광고비 변동 상위 {top}개만 — 나머지 {len(keys_all) - len(pick)}개"
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    json.dump(build(sys.argv[1]), sys.stdout, ensure_ascii=False, indent=1)
