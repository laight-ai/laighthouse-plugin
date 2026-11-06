#!/usr/bin/env python3
"""get_target_progress_v2 응답 읽기(prepare_kit.parse_targets) 자체 검사(표준 라이브러리만). 성공하면 "ok".

    python3 tests/test_target_progress.py

같은 데이터를 예전 서버의 markdown 표와 새 서버의 JSON 객체로 하나씩 손으로 적었다(JSON은 markdown을 보고
옮겨 적은 것이다). 두 형식과 래퍼 모양 전부가 같은 결과로 읽히는지, 저장 훅을 거쳐도 같은지 Claude Code판과
GPT판 두 복사본에서 모두 본다. 기대값도 손으로 셌다(목표 열만 읽는다 — actual·비율은 쓰지 않는다).
"""

import importlib.util
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
COPY_ROOTS = {"prod": os.path.join(REPO, "plugins", "laighthouse-analytics-prod"),
              "gpt": os.path.join(REPO, "laighthouse-analytics-gpt")}


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_copies():
    """복사본마다 (prepare_kit, save_responses). report_kit은 그 복사본 것을 쓰고, 끝나면 sys.modules를 되돌린다."""
    copies, saved = {}, sys.modules.get("report_kit")
    for label, root in COPY_ROOTS.items():
        assets = os.path.join(root, "shared", "assets")
        sys.path.insert(0, assets)
        sys.modules.pop("report_kit", None)
        try:
            kit = _load(os.path.join(assets, "prepare_kit.py"), f"prepare_kit_{label}")
        finally:
            sys.path.remove(assets)
        copies[label] = (kit, _load(os.path.join(root, "hooks", "save_responses.py"), f"save_responses_{label}"))
    sys.modules.pop("report_kit", None)
    if saved is not None:
        sys.modules["report_kit"] = saved
    return copies


COPIES = _load_copies()

# ── 같은 데이터, 두 형식 (media 생략 = 전체 매체) ────────────────────────────────

MD_ALL = """month: 2026-10
as_of_date: 2026-10-31
media: all
fee_basis: net

| metric | target | actual | progress_ratio |
| --- | --- | --- | --- |
| cost | 161400000 | 190828604 | 1.1823 |
| revenue | 300000000 | 255000000 | 0.85 |
| roas | 1.8587 | 1.3363 | 0.7189 |

| media | campaign_name | included | metric | target | actual | achievement |
| --- | --- | --- | --- | --- | --- | --- |
| Google | - | - | cost | 31300000 | 65858985 | 2.1041 |
| Google | - | - | revenue | 100000000 | 98000000 | 0.98 |
| Google | 2609_현대카드 카텔란_VRC ~10/5 | Y | cost | 5000000 | 4100000 | 0.82 |
| Google | 2609_현대카드 카텔란_VRC ~10/5 | Y | cpv | 28 | - | - |
| Meta | - | - | cost | 130100000 | 124969619 | 0.9606 |
| Meta | - | - | revenue | 200000000 | 157000000 | 0.785 |
| Meta | - | - | ctr | 1.2 | 0.9871 | 0.8226 |
| Meta | 리타겟팅 상시 | N | cost | 2000000 | 1830000 | 0.915 |
| 네이버 | - | - | cost | 0 | 0 | - |
| 네이버 | - | - | click | 5000 | 4210 | 0.842 |

| media | fee_mode | rate |
| --- | --- | --- |
| Google | commission | 10 |
| Meta | commission | 15 |"""

JSON_ALL = {
    "status": "ok",
    "message": None,
    "month": "2026-10",
    "as_of_date": "2026-10-31",
    "media": "all",
    "fee_basis": "net",
    "summary": [
        {"metric": "cost", "target": 161400000, "actual": 190828604, "progress_ratio": 1.1823},
        {"metric": "revenue", "target": 300000000, "actual": 255000000, "progress_ratio": 0.85},
        {"metric": "roas", "target": 1.8587, "actual": 1.3363, "progress_ratio": 0.7189},
    ],
    "scopes": [
        {"media": "Google", "campaign_name": None, "included": None, "metric": "cost",
         "target": 31300000, "actual": 65858985, "achievement": 2.1041},
        {"media": "Google", "campaign_name": None, "included": None, "metric": "revenue",
         "target": 100000000, "actual": 98000000, "achievement": 0.98},
        {"media": "Google", "campaign_name": "2609_현대카드 카텔란_VRC ~10/5", "included": True, "metric": "cost",
         "target": 5000000, "actual": 4100000, "achievement": 0.82},
        {"media": "Google", "campaign_name": "2609_현대카드 카텔란_VRC ~10/5", "included": True, "metric": "cpv",
         "target": 28, "actual": None, "achievement": None},
        {"media": "Meta", "campaign_name": None, "included": None, "metric": "cost",
         "target": 130100000, "actual": 124969619, "achievement": 0.9606},
        {"media": "Meta", "campaign_name": None, "included": None, "metric": "revenue",
         "target": 200000000, "actual": 157000000, "achievement": 0.785},
        {"media": "Meta", "campaign_name": None, "included": None, "metric": "ctr",
         "target": 1.2, "actual": 0.9871, "achievement": 0.8226},
        {"media": "Meta", "campaign_name": "리타겟팅 상시", "included": False, "metric": "cost",
         "target": 2000000, "actual": 1830000, "achievement": 0.915},
        {"media": "네이버", "campaign_name": None, "included": None, "metric": "cost",
         "target": 0, "actual": 0, "achievement": None},
        {"media": "네이버", "campaign_name": None, "included": None, "metric": "click",
         "target": 5000, "actual": 4210, "achievement": 0.842},
    ],
    "fees": [
        {"media": "Google", "fee_mode": "commission", "rate": 10},
        {"media": "Meta", "fee_mode": "commission", "rate": 15},
    ],
}

# 첫 표 cost·revenue 행 target, 두 번째 표의 매체 행(캠페인 행 제외)의 cost·revenue target. 0은 목표 없음(None).
EXPECTED_ALL = {
    "all": {"cost": 161400000.0, "revenue": 300000000.0},
    "by_media": {"Google": {"cost": 31300000.0, "revenue": 100000000.0},
                 "Meta": {"cost": 130100000.0, "revenue": 200000000.0},
                 "네이버": {"cost": None, "revenue": None}},
}

# ── 같은 데이터, 두 형식 (매체 1개, Gross, 매출 목표 0) ─────────────────────────

MD_GOOGLE = """month: 2026-10
as_of_date: 2026-10-15
media: Google
fee_basis: gross

| metric | target | actual | progress_ratio |
| --- | --- | --- | --- |
| cost | 34777778 | 30120500 | 0.8661 |
| revenue | 0 | - | - |
| roas | 0.0 | - | - |

| media | campaign_name | included | metric | target | actual | achievement |
| --- | --- | --- | --- | --- | --- | --- |
| Google | - | - | cost | 34777778 | 30120500 | 0.8661 |

| media | fee_mode | rate |
| --- | --- | --- |
| Google | commission | 10 |"""

JSON_GOOGLE = {
    "status": "ok",
    "message": None,
    "month": "2026-10",
    "as_of_date": "2026-10-15",
    "media": "Google",
    "fee_basis": "gross",
    "summary": [
        {"metric": "cost", "target": 34777778, "actual": 30120500, "progress_ratio": 0.8661},
        {"metric": "revenue", "target": 0, "actual": None, "progress_ratio": None},
        {"metric": "roas", "target": 0.0, "actual": None, "progress_ratio": None},
    ],
    "scopes": [
        {"media": "Google", "campaign_name": None, "included": None, "metric": "cost",
         "target": 34777778, "actual": 30120500, "achievement": 0.8661},
    ],
    "fees": [{"media": "Google", "fee_mode": "commission", "rate": 10}],
}

EXPECTED_GOOGLE = {"all": {"cost": 34777778.0, "revenue": None},
                   "by_media": {"Google": {"cost": 34777778.0, "revenue": None}}}

NO_TARGET = {"all": {"cost": None, "revenue": None}, "by_media": {}}

# 표 대신 오는 한 줄(예전 서버) ↔ status·message(새 서버)
NON_OK = [
    ("no_target", "No all budget/target available for 2026-10."),
    ("no_cost_metric", "No cost metric in the brand's data mart (looked for 광고비, cost); available metrics: 노출, 클릭."),
    ("no_media_dimension", "No 'media' dimension in the brand's data mart, so Google-only actuals cannot be computed."),
]


def _non_ok(status, message):
    return {"status": status, "message": message, "month": "2026-10", "as_of_date": "2026-10-31", "media": "all",
            "fee_basis": "net", "summary": [], "scopes": [], "fees": []}


def _shapes(md, obj):
    """호스트·훅이 넘길 수 있는 모양 전부 — (이름, 응답)."""
    text = json.dumps(obj, ensure_ascii=False)
    pretty = json.dumps(obj, ensure_ascii=False, indent=2)
    return [
        ("markdown", md),
        ("{result: markdown}", {"result": md}),
        ("{result: markdown} 문자열", json.dumps({"result": md}, ensure_ascii=False)),
        ("markdown 텍스트 블록", [{"type": "text", "text": md}]),
        ("JSON 문자열", text),
        ("JSON 문자열(들여쓰기)", pretty),
        ("JSON dict", obj),
        ("JSON 텍스트 블록", [{"type": "text", "text": pretty}]),
        ("JSON 텍스트 블록 문자열", json.dumps([{"type": "text", "text": text}], ensure_ascii=False)),
        ("{result: JSON 문자열}", {"result": text}),
    ]


def test_every_wrapped_shape_reads_the_same():
    for label, (kit, _) in COPIES.items():
        for md, obj, expected in ((MD_ALL, JSON_ALL, EXPECTED_ALL), (MD_GOOGLE, JSON_GOOGLE, EXPECTED_GOOGLE)):
            for name, resp in _shapes(md, obj):
                got = kit.parse_targets(resp)
                assert got == expected, (label, name)
                # prepare_kit은 by_media를 순서대로 훑으므로 순서도 같아야 한다
                assert list(got["by_media"]) == list(expected["by_media"]), (label, name)


def test_non_ok_status_and_old_plain_line_are_no_target():
    for label, (kit, _) in COPIES.items():
        for status, message in NON_OK:
            for name, resp in _shapes(message, _non_ok(status, message)):
                assert kit.parse_targets(resp) == NO_TARGET, (label, status, name)
        # status가 "ok"가 아니면 무엇이 들어 있어도 목표 없음이다(모르는 새 status 포함).
        assert kit.parse_targets(dict(JSON_ALL, status="something_new")) == NO_TARGET, label
        for resp in (None, "", "Error executing tool get_target_progress_v2: Unknown brand 'x'"):
            assert kit.parse_targets(resp) == NO_TARGET, (label, resp)


def _hook_then_prepare(kit, hook, tool_response):
    """저장 훅(save_responses.main)이 tool_response를 저장하게 하고, prepare_kit이 그 파일을 골라 읽은 결과."""
    tool_input = {"brand_name": "자사", "month": "2026-10", "as_of_date": "2026-10-31"}
    payload = {"session_id": "s", "tool_name": "mcp__laighthouse__get_target_progress_v2",
               "tool_input": tool_input, "tool_response": tool_response}
    old_hook_root, old_kit_root, old_stdin = hook.ROOT, kit.ROOT, sys.stdin
    with tempfile.TemporaryDirectory() as root:
        hook.ROOT = kit.ROOT = root
        sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
                                     encoding="utf-8")
        try:
            hook.main()
            store = kit.Store("자사")
            assert len(store.records) == 1, "훅이 응답을 저장해야 한다"
            return kit.parse_targets(store.text(kit.target("2026-10", "2026-10-31")))
        finally:
            hook.ROOT, kit.ROOT, sys.stdin = old_hook_root, old_kit_root, old_stdin


def test_hook_saved_responses_read_the_same():
    pretty = json.dumps(JSON_ALL, ensure_ascii=False, indent=2)
    responses = [
        ("markdown", MD_ALL),
        ("{result: markdown}", {"result": MD_ALL}),
        ("markdown 텍스트 블록", [{"type": "text", "text": MD_ALL}]),
        ("JSON 문자열", pretty),
        ("JSON dict", JSON_ALL),
        ("JSON 텍스트 블록", [{"type": "text", "text": pretty}]),
        ("{content, structuredContent}", {"content": [{"type": "text", "text": pretty}], "structuredContent": JSON_ALL}),
    ]
    for label, (kit, hook) in COPIES.items():
        for name, resp in responses:
            assert _hook_then_prepare(kit, hook, resp) == EXPECTED_ALL, (label, name)
        status, message = NON_OK[0]
        assert _hook_then_prepare(kit, hook, _non_ok(status, message)) == NO_TARGET, label
        assert _hook_then_prepare(kit, hook, message) == NO_TARGET, label


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
