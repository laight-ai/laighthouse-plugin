# MTD Section 6: 광고 그룹별 심층 분석

**report_type:** `mtd` (항상 포함)

---

## MCP 도구 호출: `df_dify` 서버의 분석 tool (텍스트), `get_naver_sa_performance_daily` (수치, mtd-section-7과 동일 호출)

`mcp__df_dify__<workflow-tool-name>`으로 분석 텍스트를 가져온다. 응답에서 `analysis_by_ad_group` key의 값을 사용한다.

```
호출 순서:
1. `get_naver_sa_performance_daily`(group_by="ad-group", start_date=월초, end_date=target_date)
   로 광고그룹별 노출/클릭/비용/전환 수치 데이터 수집 (mtd-section-7 그룹별 성과 호출과 동일, 데이터 재사용)
2. mcp__df_dify__<workflow-tool-name> 으로 분석 요청 (1의 수치 데이터 전달)
3. 응답의 analysis_by_ad_group 값을 렌더링
```

dify 응답 실패 시 mtd-section-7(그룹별 성과) 수치 기반으로 AI가 직접 생성한다.

---

## 응답 데이터 구조

```json
{
  "analysis_by_ad_group": "우수한 수준의 매출 발생률과, 새로 진입했음에도 개선 효과가 있는 것으로 예상되는 광고그룹을 4개를 선정하였습니다.\n\n01_브랜드_케이워드(소원검색, 국내분유)\n이번 달 클릭수는 82만건으로...\n\n01_공용스토어(브랜드검색, 공용스토어)\nCTR이 이번 달 8.5%로..."
}
```

- `analysis_by_ad_group`는 `\n\n`으로 구분된 블록으로 구성
- 각 블록의 첫 줄이 안내문 또는 광고그룹명이면 `<h4>` 소제목으로 렌더링 (첫 블록은 인트로 문단이라 `<p>`만)
- 나머지 문장은 `<p>`로 렌더링

---

## HTML

```html
<!-- MTD SECTION 6: 광고 그룹별 심층 분석 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">광고 그룹별 심층 분석</div>
  <div style="font-size:13px; color:#374151; line-height:1.8;">
    <!-- analysis_by_ad_group를 \n\n 기준으로 분리, 첫 블록은 <p> 인트로, 이후 블록은 <h4>+<p> -->
    {AD_GROUP_ANALYSIS_BLOCKS}
  </div>
</div>
```

블록 렌더링 예시 (첫 블록 = 인트로, 이후 블록 = 그룹별 소제목):

```html
<p>우수한 수준의 매출 발생률과, 새로 진입했음에도 개선 효과가 있는 것으로 예상되는 광고그룹을 4개를 선정하였습니다.</p>

<h4 style="font-size:14px; font-weight:700; margin:16px 0 6px;">01_브랜드_케이워드 (소원검색, 국내분유)</h4>
<p>이번 달 클릭수는 82만건으로...</p>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- 강조 수치는 `<strong>` 태그 사용
- `⚠`로 시작하는 문장은 `color:#d97706` (주황) 처리
