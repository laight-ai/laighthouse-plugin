"""소재 Summary 요약 근거(digest) — prepare.py가 base.json으로 부른다. 모델이 직접 부르지 않는다.

guides/creative-summary.md(노션 "소재 Summary" 가이드 사본)가 쓰는 수치를 화면에 쓸 문자열로 만들어 둔다. 직전 같은 길이
기간 대비 변화도 미리 계산한다 — 모델은 값을 다시 계산하지 않고 그대로 옮긴다. agency 플러그인 creative-report의
creative_digest.py를 따르되, 이 보고서는 매체 하나(chosen_media)만 다룬다.

base.json에서 읽는 것: tot_file(이번 기간 선택 매체 소재 total) · prev_file(직전 기간, 없을 수 있음) · media_day_file(선택
매체 일별, 없으면 「일별 추이」를 빼낸다) · metric_keys · currency · chosen_media · period · prev_period.
"""
import json
import os

MIN_IMP, MIN_SHARE = 1000, 0.01   # 최소 표본 — rank_creatives.py eligibility와 같다(노출 ≥ 1,000, 광고비 ≥ 매체 광고비의 1%)
ATOMS = ("cost", "impression", "click", "conversion", "revenue")
ZERO_DECIMAL = ("₩", "¥", "원", "")
TOP = 5


def money(v, cur):
    if v is None:
        return "-"
    d = (0 if abs(v) >= 100 or v == 0 else 1) if cur in ZERO_DECIMAL else 2
    body = format(v, ",.%df" % d)
    return body + cur if cur == "원" else cur + body


def count(v):
    return "-" if v is None else format(round(v), ",")


def pct(v, digits=1):
    return "-" if v is None else format(v, ",.%df" % digits) + "%"


def _signed(v, digits):
    v = round(v, digits) + 0.0   # -0.0 → 0.0 ("-0.0%" 방지)
    return format(v, "+,.%df" % digits)


def change(cur, prev, pp=False, digits=1):
    """직전 기간 대비. 비율 지표는 %p 차(digits는 값 표기와 같은 자릿수), 나머지는 변화율.
    직전 값이 0·없음이면 '신규', 이번 값이 0이면 '중단'."""
    if cur is None or prev is None:
        return "-"
    if pp:
        return _signed(cur - prev, digits) + "%p"
    if not prev:
        return "신규" if cur else "-"
    if not cur:
        return "중단"
    return _signed((cur - prev) / abs(prev) * 100, 1) + "%"


def ratios(e):
    imp, clk, cost = e["impression"], e["click"], e["cost"]
    e["ctr"] = clk / imp * 100 if imp else None
    e["cpc"] = cost / clk if clk else None
    e["cvr"] = e["conversion"] / clk * 100 if clk else None
    e["roas"] = e["revenue"] / cost * 100 if cost else None
    return e


def total(rows):
    t = {k: 0 for k in ATOMS}
    for e in rows:
        for k in ATOMS:
            t[k] += e[k]
    return ratios(t)


def has_name(v):
    return v is not None and str(v).strip() not in ("", "-")


def load(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def creative_rows(env, keys):
    """봉투 행 → 소재 dict. 같은 (캠페인, 광고그룹, 소재명)은 합친다(원자 지표만)."""
    if env is None:
        return None
    merged = {}
    for r in env.get("rows") or []:
        k = (r.get("campaign_name") or "", r.get("ad_group_name") or "", r.get("ad_name") or "")
        e = merged.setdefault(k, dict({a: 0 for a in ATOMS}, campaign_name=k[0], ad_group_name=k[1], ad_name=k[2]))
        for a in ATOMS:
            mk = keys.get(a)
            v = r.get(mk) if mk else None
            if isinstance(v, (int, float)):
                e[a] += v
    return [ratios(e) for e in merged.values()]


def key(e):
    return (e["campaign_name"], e["ad_group_name"], e["ad_name"])


def card(e, p, cur, has):
    """지표 묶음(값 + 직전 대비). p가 None이면 비교 없이 값만."""
    out = {"광고비": money(e["cost"], cur), "노출": count(e["impression"]), "클릭": count(e["click"]),
           "CTR": pct(e["ctr"], 2), "CPC": money(e["cpc"], cur)}
    if has["conversion"]:
        out.update({"전환": count(e["conversion"]), "CVR": pct(e["cvr"])})
    if has["revenue"]:
        out["ROAS"] = pct(e["roas"])
    if p is not None:
        diff = {"광고비": change(e["cost"], p["cost"]), "노출": change(e["impression"], p["impression"]),
                "클릭": change(e["click"], p["click"]), "CTR": change(e["ctr"], p["ctr"], True, 2),
                "CPC": change(e["cpc"], p["cpc"])}
        if has["conversion"]:
            diff.update({"전환": change(e["conversion"], p["conversion"]), "CVR": change(e["cvr"], p["cvr"], True)})
        if has["revenue"]:
            diff["ROAS"] = change(e["roas"], p["roas"], True)
        out["직전 대비"] = diff
    return out


def labeler(media, items):
    """소재 이름: '매체 / 소재명'. 같은 소재명이 여럿이면 캠페인·광고그룹을 덧붙여 구분한다."""
    names = {}
    for e in items:
        names.setdefault(e["ad_name"], set()).add(key(e))

    def label(e):
        name = e["ad_name"] if has_name(e["ad_name"]) else f"{e['ad_group_name'] or '-'} (소재명 없음)"
        if len(names.get(e["ad_name"], ())) > 1:
            name += " (" + " / ".join(p for p in (e["campaign_name"], e["ad_group_name"]) if p) + ")"
        return f"{media} / {name}"
    return label


def eligible(items):
    tc = sum(e["cost"] for e in items)
    return [e for e in items if e["impression"] >= MIN_IMP and e["cost"] >= tc * MIN_SHARE]


def daily_trend(env, keys, cur, dates):
    """선택 매체 일별 광고비 — 앞 절반(3일)·뒤 절반(4일) 일평균, 가장 많이 쓴 날, 집행일 수."""
    by = {d: 0 for d in dates}
    ck = keys.get("cost")
    for r in (env or {}).get("rows") or []:
        d = str(r.get("date") or "")[:10]
        v = r.get(ck)
        if d in by and isinstance(v, (int, float)):
            by[d] += v
    vals = [by[d] for d in dates]
    head, tail = vals[:len(vals) // 2], vals[len(vals) // 2:]
    a = sum(head) / len(head) if head else None
    b = sum(tail) / len(tail) if tail else None
    top = max(dates, key=lambda d: by[d]) if dates else None
    return {"앞 절반 일평균 광고비": money(a, cur), "뒤 절반 일평균 광고비": money(b, cur), "변화": change(b, a),
            "가장 많이 쓴 날": f"{top} ({money(by[top], cur)})" if top and by[top] else "-",
            "집행일 수": f"{sum(1 for v in vals if v > 0)}일 / {len(vals)}일"}


def dates_of(period):
    from datetime import date, timedelta
    s, e = (date.fromisoformat(x) for x in period.split("~"))
    return [(s + timedelta(days=i)).isoformat() for i in range((e - s).days + 1)]


def build(base_path):
    with open(base_path, encoding="utf-8") as f:
        base = json.load(f)
    keys = base.get("metric_keys") or {}
    cur = base.get("currency") or "₩"
    media = base.get("chosen_media") or ""
    has = {"revenue": bool(keys.get("revenue")), "conversion": bool(keys.get("conversion"))}
    rows = creative_rows(load(base.get("tot_file")), keys) or []
    prev_rows = creative_rows(load(base.get("prev_file")), keys)
    cmp_ = prev_rows is not None
    pmap = {key(e): e for e in prev_rows or []}
    label = labeler(media, rows + list(prev_rows or []))
    tc = sum(e["cost"] for e in rows)

    d = {"기간": base.get("period"), "직전 기간": base.get("prev_period") if cmp_ else "없음(비교하지 않는다)",
         "전체": card(total(rows), total(prev_rows) if cmp_ else None, cur, has)}
    md = {"매체": media, "소재 수": len(rows), "성과": d["전체"], "광고비 상위 소재": []}
    for e in sorted(rows, key=lambda x: -x["cost"])[:TOP]:
        c = card(e, pmap.get(key(e)) if cmp_ else None, cur, has)
        if cmp_ and key(e) not in pmap:
            c["직전 대비"] = "신규 집행"
        md["광고비 상위 소재"].append(dict({"소재": label(e), "광고비 비중": pct(e["cost"] / tc * 100 if tc else None)}, **c))
    pool = eligible(rows)
    eff_key, eff_label = ("roas", "ROAS") if has["revenue"] else ("ctr", "CTR")
    for k, lab in ((eff_key, eff_label), ("cpc", "CPC")):
        cand = [e for e in pool if e[k] is not None]
        if len(cand) < 2:
            continue
        best = sorted(cand, key=lambda x: (x[k] if k != "cpc" else -x[k]), reverse=True)
        fmt = (lambda v: money(v, cur)) if k == "cpc" else (lambda v: pct(v, 2 if k == "ctr" else 1))
        n = 2 if len(best) >= 4 else 1   # 소재가 적으면 위아래 하나씩만 — 우수·저조가 겹치지 않게
        row = lambda e: {"소재": label(e), lab: fmt(e[k]), "광고비": money(e["cost"], cur)}  # noqa: E731
        md["%s 우수" % lab] = [row(e) for e in best[:n]]
        md["%s 저조" % lab] = [row(e) for e in best[::-1][:n]]
    md["최소 표본"] = "노출 %s 이상·광고비 %s 이상 소재 %d개(우수·저조는 이 소재만 비교)" % (
        format(MIN_IMP, ","), money(tc * MIN_SHARE, cur), len(pool))
    d["매체"] = [md]
    if cmp_:   # 직전 기간 대비 광고비 변동(절대액)이 큰 소재 — 신규 집행·집행 중단 포함
        moves = [(abs(e["cost"] - (pmap[key(e)]["cost"] if key(e) in pmap else 0)), e, pmap.get(key(e))) for e in rows]
        cur_keys = {key(e) for e in rows}
        moves += [(p["cost"], None, p) for k, p in pmap.items() if k not in cur_keys and p["cost"]]
        moves.sort(key=lambda x: -x[0])
        d["광고비 변동 상위 소재"] = [
            {"소재": label(e or p), "광고비": "%s → %s" % (money(p["cost"] if p else 0, cur), money(e["cost"] if e else 0, cur)),
             "변화": "신규 집행" if not p or not p["cost"] else "집행 중단" if not e or not e["cost"] else change(e["cost"], p["cost"])}
            for amt, e, p in moves[:TOP] if amt]
    day_env = load(base.get("media_day_file"))
    if base.get("period") and day_env is not None:   # 매체 일별 응답이 없으면 추이를 쓰지 않는다(0원으로 지어내지 않게)
        d["일별 추이"] = daily_trend(day_env, keys, cur, dates_of(base["period"]))
    return d
