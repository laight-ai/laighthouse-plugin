# MTD Section 2: 목표 달성 현황

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).
Meta/Google 브랜드(Saturday Skin, Aqua Glow)의 daily 보고서는 이 파일을 쓰지 않는다 —
`sections/daily/daily-section-2-overview.md`가 별도로 존재한다.

---

## MCP 도구 호출: `target_progress`

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```
- `campaign_type`을 **지정하지 않는다** (None = 전체 캠페인 합산). report-backend의
  `default/_mtd_components.py::build_target_progression`이 nvad+nvgfa_ad+nvgfa_dp+nvss 전체 광고
  소스를 하나로 합산해 "목표 달성 현황" 컴포넌트 1개만 만드는 것과 동일한 기준이다 — sales/branding
  구분이나 보조 섹션 자체가 이 브랜드군에는 없다.
- 응답 `items`(3개: monthly_budget / monthly_revenue / monthly_roas)의 `target_full_month`를
  `overview.budget_goal`/`revenue_goal`/`roas_goal`에 매핑한다.

> ⚠️ **actual_mtd 데이터 소스 검증 (2026-07-10, 다형식품 2026-05-15 MTD PDF 대조로 확인)**:
> `default/_mtd_components.py::build_target_progression`은 `cost_actual`/`sales_actual`을
> **`target_progress`의 `actual_mtd` 필드를 신뢰하는 게 아니라, naver 광고 실적 데이터(nvad+nvgfa_ad+
> nvgfa_dp+nvss)를 월초~기준일로 직접 합산해서 계산**한다. 실제 PDF의 "목표 달성 현황" 카드 실적값
> (예: 소진 ₩61,196,569, 매출 ₩342,469,164)은 `get_ad_performance_daily_table`(media=naver,
> group_by=total)을 월초~기준일로 합산한 값과 정확히 일치했다. 이 환경의 mock `target_progress`는
> `actual_mtd`를 0으로 반환하는 경우가 있었는데, 이는 실제 report-backend 동작과 다르다.
>
> **따라서 `overview.budget_spent`/`revenue_actual`(그리고 이로부터 파생되는 `budget_spent_rate`/
> `revenue_achievement_rate`/`roas_actual`)은 `target_progress.actual_mtd`를 쓰지 않고,
> `get_ad_performance_daily_table(brand_name, start_date=월초, end_date=target_date, group_by="total",
> media="naver")`로 받은 일별 `cost`/`purchase_amount`를 합산해서 계산한다.** 이 데이터는
> `mtd-section-14-daily-attributed-sales.md`가 이미 동일 호출로 받아두므로 재사용하면 되고, 별도
> API를 새로 부를 필요는 없다. `target_progress`는 `target_full_month`(목표값)만 신뢰한다.

---

## 필요 데이터

- `overview.budget_goal` / `revenue_goal` / `roas_goal` ← `target_progress` 응답의 `target_full_month`
  (roas는 소수 → % 변환, ×100)
- `overview.budget_spent` / `revenue_actual` ← `get_ad_performance_daily_table` 합산 `cost`/`purchase_amount`
- `overview.budget_spent_rate` = `budget_spent / budget_goal × 100`
- `overview.revenue_achievement_rate` = `revenue_actual / revenue_goal × 100`
- `overview.roas_actual` = `revenue_actual / budget_spent × 100`

---

## HTML

```html
<!-- MTD SECTION 2: 목표 달성 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">목표 달성 현황</div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 예산대비 소진율</div>
      <div style="font-size:32px; font-weight:700; color:#3b82f6; margin-bottom:12px;">{overview.budget_spent_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">기간 목표</div><div style="font-weight:600;">{overview.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진비용</div><div style="font-weight:600;">{overview.budget_spent}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 목표 매출 대비 달성률</div>
      <div style="font-size:32px; font-weight:700; color:#16a34a; margin-bottom:12px;">{overview.revenue_achievement_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">기간 목표</div><div style="font-weight:600;">{overview.revenue_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">기간 매출</div><div style="font-weight:600;">{overview.revenue_actual}</div></div>
      </div>
    </div>

    <div style="padding:20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 누적 ROAS</div>
      <div style="font-size:32px; font-weight:700; color:#7c3aed; margin-bottom:12px;">{overview.roas_actual}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">기간 목표</div><div style="font-weight:600;">{overview.roas_goal}%</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">기간 ROAS</div><div style="font-weight:600;">{overview.roas_actual}%</div></div>
      </div>
    </div>

  </div>
</div>
```

## Script
없음 (정적 카드)

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- `mtd-section-1-kpi-goals.md`는 이 섹션과 항상 쌍으로, 바로 위에 렌더링한다 (같은 `target_progress`
  응답 재사용, 별도 재호출 없음).
