# Section 4: Executive Summary

**트리거 키워드:** `Executive Summary`

---

## MCP 도구 호출: `dify`

`mcp__dify__*` 도구를 호출하여 분석 텍스트를 가져온다.
응답에서 `executive_summary` key의 값을 사용한다.

```
호출 순서:
1. mcp__laighthouse__* 로 수치 데이터 수집
2. mcp__dify__* 로 분석 요청 (수치 데이터 전달)
3. 응답의 executive_summary 값을 렌더링
```

dify 응답 실패 시 수치 기반으로 AI가 직접 생성한다.

---

## 응답 데이터 구조

```json
{
  "executive_summary": "2026년 4월 퍼포먼스 마케팅 성과는 좋았습니다. 광고비를 월 목표 대비..."
}
```

- `executive_summary` 값이 문자열이면 그대로 `<p>`로 렌더링
- 줄바꿈(`\n`) 기준으로 분리하여 각 줄을 `<li>`로 렌더링

---

## HTML

```html
<!-- SECTION 4: Executive Summary -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Executive Summary</div>
  <ul style="padding-left:20px; line-height:1.9; font-size:13px; color:#374151;">
    <!-- executive_summary를 줄바꿈 기준으로 분리하여 <li>로 렌더링 -->
    {EXECUTIVE_SUMMARY_ITEMS}
  </ul>
</div>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- `executive_summary` 문자열을 `\n` 기준으로 split → 각 줄을 `<li>` 태그로 변환
- 빈 줄은 건너뜀
- `⚠`로 시작하는 항목은 `color:#d97706` (주황) 처리
- 강조 수치는 `<strong>` 태그 사용
