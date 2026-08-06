# Daily Section 4: 최근 7일 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

---

## 분기 A: Google/Meta 브랜드

**MCP 도구:** `get_sales_performance_daily` (start_date=week_start, end_date=target_date)

### 필요 데이터
- `sales_daily.labels`: 날짜 레이블 배열 — 예: `["3/26(Thu)", ..., "4/1(Wed)"]`
- `sales_daily.revenue`: 매출 배열 ($)
- `sales_daily.ad_spend`: 광고비 배열 ($)
- `sales_daily.roas`: ROAS 배열 (%)

#
