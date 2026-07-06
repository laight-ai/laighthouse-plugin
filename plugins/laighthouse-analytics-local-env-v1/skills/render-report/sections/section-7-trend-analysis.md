# Section 7: 제품 판매 트렌드 분석

**트리거 키워드:** `제품 판매 트렌드`

---

## MCP 도구 호출: `dify` (분석 결과)

트렌드 분석 텍스트는 `mcp__dify__*` 도구를 호출하여 가져온다.
카테고리별 매출 데이터를 dify에 전달하면 분석 텍스트를 반환한다.

```
호출 순서:
1. mcp__laighthouse__* 로 카테고리별 수치 데이터 수집
2. mcp__dify__* 로 트렌드 분석 텍스트 요청 (카테고리 데이터 전달)
3. dify 응답을 trend_analysis.items 배열로 사용
```

dify 도구가 응답하지 않거나 결과가 없을 경우 수치 기반으로 AI가 직접 생성한다.

---

## 응답 데이터 구조

```json
{
  "trend_analysis": {
    "period": "2026년 4월",
    "items": [
      "국내분유는 약 9,300만 원의 매출을 기록하며 전년 동기 대비 약 113.8% 성장하였고...",
      "커피는 약 6,620만 원의 매출을 기록하였으며...",
      "우유/요거트는 약 2,020만 원의 매출로 4개월 연속 상승세를..."
    ]
  }
}
```

---

## HTML

```html
<!-- SECTION 7: 제품 판매 트렌드 분석 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">제품 판매 트렌드 분석</div>
  <div style="font-size:13px; font-weight:600; color:#374151; margin-bottom:10px;">
    카테고리별 광고 운영 및 매출 분석 요약 ({trend_analysis.period})
  </div>
  <ul style="padding-left:20px; line-height:1.9; font-size:13px; color:#374151;">
    <!-- trend_analysis.items 배열의 각 항목을 <li>로 렌더링 -->
    {TREND_ANALYSIS_ITEMS}
  </ul>
</div>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- 각 항목은 `<li>` 태그
- 수치 강조는 `<strong>` 태그
- 카테고리명은 `<strong>` 처리
