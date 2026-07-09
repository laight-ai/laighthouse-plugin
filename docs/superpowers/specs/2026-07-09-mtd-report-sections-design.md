# MTD 보고서 신규 섹션 설계

## 배경

`render-report` 스킬은 daily/weekly/mtd/monthly 보고서를 공용 섹션(section-1~8)으로 렌더링한다.
참고 PDF(`다형식품2026-02-18mtd.pdf`)를 보면 실제 MTD 보고서에는 공용 섹션 외에 9개의 MTD 전용
섹션이 추가로 존재한다. 이 설계는 해당 9개 섹션을 `sections/mtd/` 하위에 신규 파일로 추가하고,
`report_type: mtd`일 때 항상(키워드 조건 없이) 렌더링되도록 `SKILL.md`를 갱신한다.

## 파일 구조

```
sections/mtd/
  mtd-section-1-performance-overview.md      (dify: performance_overview)
  mtd-section-2-product-cumulative-sales.md  (테이블)
  mtd-section-3-product-deep-dive.md         (dify: product_analysis)
  mtd-section-4-media-budget-progress.md     (테이블, 진행바)
  mtd-section-5-campaign-performance.md      (테이블, 페이지네이션)
  mtd-section-6-ad-group-deep-dive.md         (dify: ad_group_analysis)
  mtd-section-7-group-performance.md         (테이블, 페이지네이션)
  mtd-section-8-keyword-performance.md        (테이블, 페이지네이션)
  mtd-section-9-daily-attributed-sales.md     (테이블)
```

## 렌더링 순서 (report_type: mtd)

기존 공용 섹션과 인터리빙되며, 아래 순서를 `SKILL.md`에 고정 시퀀스로 명시한다 (daily와 동일하게
키워드 조건 없이 항상 포함):

1. 월 목표 카드 (section-1)
2. 목표 달성 현황 (section-2, sales + branding 보조)
3. Executive Summary (section-4)
4. **mtd-section-1**: 성과에 대한 개괄
5. 월별 광고 성과 차트 (section-3)
6. **mtd-section-2**: 상품별 누적 판매액 테이블
7. 일일 카테고리별 매출 현황 차트 (section-6)
8. **mtd-section-3**: 제품 판매 성과의 심층 분석
9. **mtd-section-4**: 매체별 예산 소진 현황 테이블
10. **mtd-section-5**: 캠페인별 성과 테이블
11. **mtd-section-6**: 광고 그룹별 심층 분석
12. **mtd-section-7**: 그룹별 성과 테이블
13. **mtd-section-8**: 키워드별 성과 테이블
14. **mtd-section-9**: 일별 광고기여 매출 분석 테이블

카테고리별 매출액 비교(section-5)와 제품 판매 트렌드 분석(section-7)은 여전히 키워드 기반 선택
섹션으로 남는다 (mtd-section-3이 더 상세한 대체 서술이므로, mtd 보고서 프롬프트에서는 통상
section-7 키워드를 함께 지정하지 않는 것을 권장 — 강제하지 않음).

## dify 연동 (서술형 3개: mtd-section-1, 3, 6)

Executive Summary(section-4)와 동일한 패턴:
- 수치 데이터 수집 → `mcp__dify__*` 호출 → 응답에서 각 key 추출
- `performance_overview`, `product_analysis`, `ad_group_analysis` — 3개 섹션 각각 독립 key로 응답
- dify 실패 시 수치 데이터 기반으로 AI가 직접 생성 (폴백)
- 렌더링 규칙은 section-4와 동일: `\n` 분리 → `<li>`, `⚠` 시작 항목은 주황색, 수치는 `<strong>`

## 섹션별 데이터 스키마 & HTML

### mtd-section-1: 성과에 대한 개괄
```json
{ "performance_overview": "1. 매출 발생 현황:\n...\n2. 예산 소진 현황:\n...\n3. ROAS 현황:\n..." }
```
- Executive Summary 카드와 동일한 `<ul><li>` 렌더링, 섹션 제목만 "성과에 대한 개괄"

### mtd-section-2: 상품별 누적 판매액 테이블
```json
{
  "product_cumulative_sales": [
    { "category": "국내분유", "sales": 64295126, "discount_rate": 91.75,
      "refund_rate": 41.86, "mom": 49.19 }
  ]
}
```
- 컬럼: 상품 카테고리(s) / 판매액 / 할인율 / 환불금액 비율 / MoM(%)
- 검색창 + 페이지 크기 선택(10개) — 클라이언트 JS 페이지네이션

### mtd-section-3: 제품 판매 성과의 심층 분석
```json
{ "product_analysis": "Overview\n...\n국내분유\n...\n커피\n..." }
```
- section-7과 달리 소제목(카테고리명, "Overview")을 `<h4>`로 별도 렌더링, 본문은 `<p>`

### mtd-section-4: 매체별 예산 소진 현황 테이블
```json
{
  "media_budget_progress": {
    "channel_group": "SA / DA",
    "rows": [
      { "media": "네이버 브랜드검색", "spent_rate": 55.9, "budget_goal": 19099909,
        "spent": 9237537, "daily_budget": 10669754, "daily_spent": 8421155 }
    ],
    "total": { "spent_rate": 47.9, "budget_goal": 127636363, "spent": 61759532,
      "daily_budget": 61196569, "daily_spent": 66439794 }
  }
}
```
- 예산 소진율 컬럼에 인라인 progress bar (`spent_rate`%)
- 합계 행은 굵게 강조

### mtd-section-5: 캠페인별 성과 테이블
```json
{
  "campaign_performance": [
    { "campaign": "05_GT케이(SPBR)_MO", "channel": "NVSHOP", "revenue": 1320543,
      "ad_cost": 129801, "roas": 1017, "impressions": 12778, "clicks": 53,
      "ctr": 0.41, "cpc": 2449.08, "purchases": 17, "avg_price": 77679 }
  ]
}
```
- 컬럼: 캠페인 / 네이버 광고 채널명 / 매출 / 광고비 / ROAS / 노출 / 클릭 / CTR / CPC / 구매 / 평균단가
- 검색 + 10/20/50개 페이지네이션 (건수가 많음)

### mtd-section-6: 광고 그룹별 심층 분석
```json
{ "ad_group_analysis": "네이버 광고 그룹 단위 성과 분석입니다...\n01_브랜드_케이워드...\n..." }
```
- mtd-section-3과 동일한 렌더링 규칙 (소제목 + 본문)

### mtd-section-7: 그룹별 성과 테이블
```json
{
  "group_performance": [
    { "group": "002_브랜드_공용_통합", "impressions": 3528, "clicks": 108,
      "cpc": 346.41, "ad_cost": 37412, "revenue": 666438 }
  ]
}
```
- 컬럼: 광고그룹 / 노출 / 클릭 / CPC / 광고비 / 매출
- 페이지네이션 (10개, PDF 기준 15페이지 규모)

### mtd-section-8: 키워드별 성과 테이블
```json
{
  "keyword_performance": [
    { "keyword": "알파카리그린티라떼", "impressions": 9076, "clicks": 659,
      "ad_cost": 353722, "cpc": 536.76, "ctr": 7.26, "cpm": 38973.34,
      "purchases": 183, "revenue": 8057615, "roas": 2278 }
  ]
}
```
- 컬럼: 키워드 / 노출 / 클릭 / 광고비 / CPC / 클릭률 / CPM / 구매수 / 매출 / ROAS
- 검색 + 페이지네이션 (PDF 기준 130페이지 규모 — 대량 데이터 전제, 서버에서 페이지 단위로 넘겨줄 수도
  있으나 이번 구현은 클라이언트 페이지네이션으로 통일)

### mtd-section-9: 일별 광고기여 매출 분석 테이블
```json
{
  "daily_attributed_sales": [
    { "date": "2026-05-01", "ad_cost": 3957831, "clicks": 4376,
      "purchases": 564, "revenue": 22699384 }
  ]
}
```
- 컬럼: 날짜 / 광고비 / 클릭 / 구매 / 매출
- 페이지네이션 없음 (기간 내 일자 수만큼, MTD 최대 31행)

## 공통 구현 규칙

- 모든 신규 섹션은 기존 `.card` / `section-title` 클래스, `fmtUSD`/`toLocaleString` 포맷 규칙을 그대로 사용.
- 페이지네이션이 있는 테이블(NEW-2,5,7,8)은 각 섹션 스크립트 내부에 자체 포함된 IIFE로 구현
  (다른 섹션과 전역 변수 충돌 없도록 섹션별 고유 id 사용: `mtdSec2Table`, `mtdSec5Table` 등).
- 데이터 부족 시 기존 규칙과 동일하게 "데이터 준비 중" 카드로 대체.

## SKILL.md 변경 사항

- `## 섹션 Import 목록`에 `report_type: mtd` 전용 하위 표 추가 (9개 파일 + 고정 렌더링 순서)
- 기존 `report_type: weekly / mtd / monthly` 통합 표에서 `mtd`를 분리하여 "공용 섹션은 그대로
  키워드 기반, mtd 전용 섹션 9개는 항상 포함"이라는 규칙을 명시
- dify 호출 섹션에 대한 설명(4단계)에 `performance_overview`, `product_analysis`,
  `ad_group_analysis` 3개 key도 함께 언급
