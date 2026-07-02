# Section 4: Executive Summary

**트리거 키워드:** `Executive Summary`

## 필요 데이터 (MCP)
- `executive_summary`: 분석 텍스트 배열 (문자열 배열)
  - MCP에서 받은 텍스트가 없을 경우 섹션 1~3 수치를 기반으로 AI가 생성

## HTML

```html
<!-- SECTION 4: Executive Summary -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Executive Summary</div>
  <ul style="padding-left:20px; line-height:1.9; font-size:13px; color:#374151;">
    <!-- executive_summary 배열의 각 항목을 <li>로 렌더링 -->
    {EXECUTIVE_SUMMARY_ITEMS}
    <!-- 예시:
    <li>2026년 4월 퍼포먼스 마케팅 성과는 좋았습니다. 광고비를 월 목표 대비 약 920만 원(8.2%) 적게 사용하면서도 매출 목표를 초과 달성하였고, ROAS 510.3%는 목표(464.4%) 대비 45.9%p 높은 수준으로 13개월 내 최고치를 기록하였습니다.</li>
    <li>국내분유 카테고리에서 광고를 경유하지 않은 자체 매출이 늘어나는 긍정적 구조 변화가 확인됩니다.</li>
    -->
  </ul>
</div>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- `executive_summary` 배열의 각 항목 → `<li>` 태그로 변환
- 강조 표시가 필요한 텍스트는 `<strong>` 태그 사용
- 권고/경고 항목은 앞에 `⚠` 이모지 추가
