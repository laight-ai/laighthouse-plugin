# Daily Section 6: 광고 그룹 및 키워드 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

⚠️ **이 파일은 기존 "daily-section-7-asset-group-table.md"를 대체한다.** 번호가 하나 당겨졌고
(옛 section 5 DTC Revenue 삭제로), naver 분기는 **4단계 트리(채널→캠페인→광고그룹→키워드) →
2단계 트리(광고그룹→키워드)**로 축소 재설계되었다 — 채널/캠페인 레벨은 이제
daily-section-5(캠페인 성과)가 전담하므로, 이 섹션은 그보다 한 단계 더 깊은 광고그룹/키워드
드릴다운만 담당한다.

---

## 분기 A: Google/Meta 브랜드 (변경 없음)

⚠️ "Asset Group"은 Google Performance Max 캠페인 전용 개념이라 naver에는 대응 개념이 없고,
PMax는 키워드 타겟팅 자체가 없는 상품이라 "키워드" 열은 이 분기에는 적용되지 않는다 (에셋그룹
레벨까지만 존재).

**MCP 도구:** `get_sales_by_asset_group_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

### 필요 데이터
- `sales_by_asset_group`: 에셋그룹 배열
  ```json
  [
    { "media": "Google Ads", "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "asset_group": "CITRUS Kiwi overlay pack assets", "impression": 509, "click": 15, "ctr": 2.95,
      "cost": 10, "revenue": 0 }
  ]
  ```
  ※ ROAS 컬럼 없음 (이미지 참조)

#
