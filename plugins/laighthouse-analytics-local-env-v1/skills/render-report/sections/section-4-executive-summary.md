# Section 4: Executive Summary

**트리거 키워드:** `Executive Summary`

---

## MCP 도구 호출: `df_dify` 서버의 분석 tool (브랜드/워크플로별 tool명 확인 필요)

`.mcp.json`에 등록된 dify MCP 서버 키는 `df_dify`이다 (예: `mcp__df_dify__<workflow-tool-name>`).
실제 tool명은 브랜드마다 연결된 Dify 워크플로에 따라 다르다(예: AquaGlow는 `AG_Daily_V1_01`) —
이 naver 브랜드에 연결된 워크플로 tool명을 확인 후 고정한다. 텍스트 분석은 dify 워크플로 tool을
그대로 재사용하면 되므로 **naver 전용 MCP 도구를 새로 만들 필요는 없다**.

```
호출 순서:
1. `target_progress`(campaign_type="sales", section-2와 동일 호출)로 수치 데이터 수집
2. `mcp__df_dify__<workflow-tool-name>` 으로 분석 요청 (1의 수치 데이터를 payload로 전달)
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
