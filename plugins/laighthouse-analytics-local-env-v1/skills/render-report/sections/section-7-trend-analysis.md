# Section 7: 제품 판매 트렌드 분석

**트리거 키워드:** `제품 판매 트렌드`

## MCP 도구 호출: `df_dify` 서버의 분석 tool (텍스트만; 수치 소스는 section-5/6 — `get_naver_item_sales_daily`)

텍스트는 `mcp__df_dify__<workflow-tool-name>`으로 생성한다. section-5/6에서 이미 수집한
`get_naver_item_sales_daily` 결과를 payload로 전달한다.

## 필요 데이터 (MCP)
- `trend_analysis.period`: 분석 기간 레이블 (예: '2026년 4월')
- `trend_analysis.items`: 분석 텍스트 배열 (카테고리별 불릿 항목)
  - MCP에서 받은 텍스트가 없으면 섹션 5~6 데이터 기반으로 AI가 직접 생성

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
- 카테고리명은 `<strong>` 또는 굵게 표시
