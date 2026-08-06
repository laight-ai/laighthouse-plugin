# Daily Section 5: 캠페인 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

naver 분기는 **캠페인 단위 표**를 쓴다 — mtd(MK)의 캠페인별 성과(mtd-section-9)와 동일한 패턴이다.

---

## 분기 A: Google/Meta 브랜드 (변경 없음)

**MCP 도구:** `get_sales_by_campaign_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

### 필요 데이터
- `sales_by_campaign`: 캠페인 배열
  ```json
  [
    { "media": "Google Ads", "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "impression": 3548, "click": 62, "ctr": 1.75, "cost": 53, "revenue": 46, "roas": 86.8 }
  ]
  ```

#
