# MTD Section 5: 성과에 대한 개괄

**report_type:** `mtd` (항상 포함)

---

## MCP 도구 호출: `df_dify` 서버의 분석 tool (텍스트), `get_naver_target_progress` (수치)

`mcp__df_dify__<workflow-tool-name>`으로 분석 텍스트를 가져온다 (`.mcp.json`의 dify 서버 키는
`df_dify`; 실제 tool명은 브랜드 워크플로에 맞게 확인). 응답에서 `performance_overview` key의 값을 사용한다.

```
호출 순서:
1. `get_naver_target_progress`로 매출/예산/ROAS 수치 수집 — mtd-section-2(목표 달성 현황)와 동일한
   호출을 재사용한다 (범용 `target_progress`가 아님 — mtd-section-2의 버그 설명 참고).
2. `mcp__df_dify__<workflow-tool-name>` 으로 분석 요청 (1의 수치 데이터 전달)
3. 응답의 performance_overview 값을 렌더링
```

dify 응답 실패 시 수치 기반으로 AI가 직접 생성한다 (매출 발생 현황 / 예산 소진 현황 / ROAS 현황
3개 하위 항목 구조를 유지).

---

## 응답 데이터 구조

```json
{
  "performance_overview": "1. 매출 발생 현황:\n2026년 5월 1일부터 15일까지...\n\n2. 예산 소진 현황:\n2026년 5월 1일부터...\n\n3. ROAS 현황:\n2026년 5월 1일부터..."
}
```

- `performance_overview`는 `\n\n`으로 구분된 3개 블록(매출/예산/ROAS)으로 구성
- 각 블록의 첫 줄(`1. ...:`, `2. ...:`, `3. ...:`)은 `<strong>` 소제목으로 렌더링
- 나머지 문장은 `<p>`로 렌더링

---

## HTML

```html
<!-- MTD SECTION 1: 성과에 대한 개괄 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">성과에 대한 개괄</div>
  <div style="font-size:13px; color:#374151; line-height:1.8;">
    <!-- performance_overview를 \n\n 기준으로 분리, 각 블록의 첫 줄은 굵게 -->
    {PERFORMANCE_OVERVIEW_BLOCKS}
  </div>
</div>
```

각 블록 렌더링 예시:

```html
<div style="margin-bottom:14px;">
  <div style="font-weight:700; margin-bottom:4px;">1. 매출 발생 현황:</div>
  <p>2026년 5월 1일부터 15일까지 실제 발생한 매출은 약 4,247만 원으로...</p>
</div>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- `⚠`로 시작하는 문장은 `color:#d97706` (주황) 처리
- 강조 수치는 `<strong>` 태그 사용
- dify 응답이 없으면 섹션 2(목표 달성 현황)의 sales 수치를 근거로 동일한 3블록 구조를 AI가 생성
