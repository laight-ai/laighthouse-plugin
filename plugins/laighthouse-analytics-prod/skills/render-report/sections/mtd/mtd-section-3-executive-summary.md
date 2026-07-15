# MTD Section 3: Executive Summary

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).

---

## 텍스트 생성: AI가 직접 작성 (`df_dify` MCP 호출 안 함)

⚠️ **`df_dify` MCP 서버는 현재 호출하지 않는다** (연결 불안정으로 타임아웃 시 빈 응답이 돌아옴).

```
작성 순서:
1. `get_naver_target_progress`로 수치 데이터 수집 — mtd-section-2(목표 달성 현황)와 동일한 호출을
   재사용한다 (범용 `target_progress`가 아님 — mtd-section-2의 버그 설명 참고).
2. dify 호출 없이, 1의 수치 데이터를 근거로 AI가 executive_summary 텍스트를 직접 작성한다.
```

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
