#!/usr/bin/env python3
"""PostToolUse 캡처 훅: `get_ad_performance_daily_table`의 대용량 응답을 파일로 우회시킨다.

왜 존재하나: `group_by`가 `campaign`/`ad-set`/`ad`인 응답(특히 Naver는 키워드 단위)은 수만~수십만
자까지 커진다. 이 원본이 모델 컨텍스트에 통째로 들어가고, asset 스크립트(dxd_table_rows.py 등)에
넘기려면 모델이 그 전문을 heredoc으로 **다시 타이핑**해야 했다 — 보고서 생성 시간의 최대 병목이자,
"응답이 너무 커서 대체/추정하겠다"는 데이터 무결성 사고의 반복 원인이었다.

무엇을 하나 (Claude Code가 이 훅을 도구 응답 직후, 모델이 보기 전에 실행한다):
1. stdin으로 받은 훅 입력(JSON)에서 `tool_input.group_by`가 campaign/ad-set/ad이고 응답 텍스트가
   충분히 크면(MIN_CHARS 초과), 응답 원본을 임시 디렉터리에 .md 파일로 저장한다.
2. `hookSpecificOutput.updatedToolOutput`으로 모델에게 보이는 응답을 "저장 경로 + 행 통계 +
   사용법 + 미리보기" 스텁으로 교체한다 — 원본은 컨텍스트에 들어가지 않는다.
3. 조건에 안 맞으면(작은 응답, group_by total/media, 파싱 실패 등) 아무것도 출력하지 않고
   종료한다 → 원본이 그대로 모델에게 전달된다 (안전한 폴백).

이 훅이 실패해도 보고서 생성은 깨지지 않는다 — 응답이 예전처럼 원본 그대로 전달될 뿐이고,
스킬들은 기존 heredoc(`markdown` 배열) 경로로 동작한다.
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

# Windows 콘솔 기본 인코딩(cp949)에서도 한글/기호가 깨지지 않도록 항상 UTF-8로 고정
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CAPTURE_GROUP_BY = {"campaign", "ad-set", "ad"}
MIN_CHARS = 1500          # 이보다 작은 응답은 스텁으로 바꿀 실익이 없다 — 원본 그대로 통과
STALE_SECS = 3 * 24 * 3600  # 3일 지난 세션 캡처 디렉터리는 정리

CAPTURE_ROOT = os.path.join(tempfile.gettempdir(), "laighthouse_mcp_capture")


def extract_text(resp):
    """tool_response에서 텍스트를 꺼낸다 — str / {"text":...} / {"content":[...]} / [블록들]
    어떤 shape이 와도 방어적으로 처리한다."""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        if isinstance(resp.get("text"), str):
            return resp["text"]
        if "content" in resp:
            return extract_text(resp["content"])
        return None
    if isinstance(resp, list):
        parts = []
        for block in resp:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts) if parts else None
    return None


def rebuild_like(resp, new_text):
    """updatedToolOutput은 원래 도구 출력과 같은 shape이어야 한다 — 받은 tool_response의
    구조를 그대로 유지한 채 텍스트만 교체해서 돌려준다."""
    if isinstance(resp, str):
        return new_text
    if isinstance(resp, dict):
        if isinstance(resp.get("text"), str):
            out = dict(resp)
            out["text"] = new_text
            return out
        if "content" in resp:
            out = dict(resp)
            out["content"] = rebuild_like(resp["content"], new_text)
            return out
        return new_text
    if isinstance(resp, list):
        return [{"type": "text", "text": new_text}]
    return new_text


def unwrap_json_result(text):
    """Cowork(Claude Desktop)는 툴 응답 본문을 `{"result": "<본문>"}` JSON 문자열로 감싸서
    훅에 넘긴다 — 이대로 저장하면 줄바꿈이 리터럴 \\n으로 박혀 마크다운 파서가 전체를 한 줄로
    읽는다(실측: 2026-08-12, section-4가 빈 배열을 반환한 원인). JSON 래퍼면 벗겨서 본문만
    돌려주고, 아니면 그대로 돌려준다. 중첩 래핑도 방어적으로 푼다."""
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


def markdown_stats(text):
    """마크다운 표에서 (헤더 줄, 첫 데이터 줄, 총 데이터 행 수, media별 행 수)를 뽑는다."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return None, None, 0, {}
    header_line = lines[0]
    headers = [c.strip() for c in header_line.strip().strip("|").split("|")]
    try:
        media_idx = headers.index("media")
    except ValueError:
        media_idx = None
    first_row = None
    n_rows = 0
    by_media = {}
    for ln in lines[1:]:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(c == "" or set(c) <= {"-"} for c in cells):
            continue  # 구분선
        n_rows += 1
        if first_row is None:
            first_row = ln
        if media_idx is not None and media_idx < len(cells):
            by_media[cells[media_idx]] = by_media.get(cells[media_idx], 0) + 1
    return header_line, first_row, n_rows, by_media


def prune_stale():
    try:
        now = time.time()
        for name in os.listdir(CAPTURE_ROOT):
            p = os.path.join(CAPTURE_ROOT, name)
            if os.path.isdir(p) and now - os.path.getmtime(p) > STALE_SECS:
                shutil.rmtree(p, ignore_errors=True)
    except OSError:
        pass


def _breadcrumb(message):
    """훅이 실행됐는지 여부를 사후 진단할 수 있도록 남기는 한 줄 로그 —
    스텁 교체가 일어나지 않은 실행에서도 '훅 자체는 돌았는가'를 구분하게 해준다."""
    try:
        os.makedirs(CAPTURE_ROOT, exist_ok=True)
        with open(os.path.join(CAPTURE_ROOT, "hook.log"), "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except OSError:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        _breadcrumb("ran: stdin not json — pass-through")
        return  # 입력이 이상하면 조용히 통과

    tool_input = data.get("tool_input") or {}
    group_by = tool_input.get("group_by")
    _breadcrumb(f"ran: tool={data.get('tool_name')} group_by={group_by} session={data.get('session_id')}")
    if group_by not in CAPTURE_GROUP_BY:
        return

    # 호스트마다 응답 필드명이 다를 수 있다 (Claude Code: tool_response; 다른 호스트 방어)
    resp = None
    resp_field = None
    for field in ("tool_response", "tool_output", "tool_result"):
        if data.get(field) is not None:
            resp = data[field]
            resp_field = field
            break
    if resp is None:
        _breadcrumb(f"skip: no response field; stdin keys={sorted(data.keys())}")
        return

    text = extract_text(resp)
    text = unwrap_json_result(text)
    if not text:
        sample = json.dumps(resp, ensure_ascii=False, default=str)[:400]
        _breadcrumb(f"skip: text extraction failed; field={resp_field} type={type(resp).__name__} sample={sample}")
        return

    # Cowork는 초대형 응답을 스스로 파일로 빼고 "Output has been saved to <경로>" 안내만 넘긴다
    # (실측: naver group_by="ad" 101,905자 → 1,325자 안내문). 그 파일을 직접 읽어 정상 캡처로
    # 전환한다 — 모델이 offset/limit으로 원본을 더듬는 경로를 원천 차단.
    saved_match = re.search(r"saved to (\S+?\.txt)", text)
    if len(text) <= MIN_CHARS and saved_match:
        saved_path = saved_match.group(1)
        try:
            with open(saved_path, encoding="utf-8") as f:
                redirected = unwrap_json_result(f.read())
        except OSError:
            _breadcrumb(f"skip: oversized notice but cannot read {saved_path} — pass-through")
            return
        if redirected:
            _breadcrumb(f"redirect: oversized output read from {saved_path} chars={len(redirected)}")
            text = redirected

    if len(text) <= MIN_CHARS:
        sample = text[:400].replace("\n", "\\n")
        _breadcrumb(f"skip: small response ({len(text)} chars <= {MIN_CHARS}) sample={sample}")
        return

    session = re.sub(r"[^A-Za-z0-9_-]", "_", str(data.get("session_id") or "nosession"))[:48]
    capture_dir = os.path.join(CAPTURE_ROOT, session)
    os.makedirs(capture_dir, exist_ok=True)
    prune_stale()

    media = str(tool_input.get("media") or "all")
    start = str(tool_input.get("start_date") or "")
    end = str(tool_input.get("end_date") or "")
    seq = len([f for f in os.listdir(capture_dir) if f.endswith(".md")]) + 1
    fname = f"daily_table_{seq:02d}_{media}_{group_by}_{start}_{end}.md"
    fname = re.sub(r"[^A-Za-z0-9._-]", "_", fname)
    path = os.path.join(capture_dir, fname)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    _breadcrumb(f"captured: {path} chars={len(text)}")

    header_line, first_row, n_rows, by_media = markdown_stats(text)
    media_summary = ", ".join(f"{k}={v}" for k, v in sorted(by_media.items())) or "n/a"
    preview = "\n".join(x for x in (header_line, first_row) if x)

    stub = (
        f"[laighthouse-capture-hook] 이 도구 응답 원본({len(text):,}자, 데이터 {n_rows}행; "
        f"media={media}, group_by={group_by}, {start}~{end})은 아래 파일에 전문 저장됨:\n"
        f"{path}\n"
        f"media별 행 수: {media_summary}\n"
        f"⚠️ 원본을 컨텍스트에 다시 타이핑하지 말 것. asset 스크립트(dxd_table_rows.py 등)에 넘길 때는 "
        f'{{"markdown_files": ["{path}", ...]}} 입력 형태(경로 배열)를 heredoc으로 넘기고, '
        f"그 외 집계가 필요하면 Bash에서 이 파일을 직접 읽어(cat/grep/awk) 처리한다. "
        f"수치를 요약·추정으로 대체하지 않는다.\n"
        f"미리보기(헤더+첫 행):\n{preview}"
    )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "updatedToolOutput": rebuild_like(resp, stub),
                }
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
