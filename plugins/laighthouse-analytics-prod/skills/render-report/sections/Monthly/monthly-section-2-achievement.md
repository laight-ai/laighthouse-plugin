# Monthly Section 2: 목표 달성 현황

**report_type:** `monthly` (항상 포함) — naver 기반 default generator 브랜드 전용(남양유업 등).

포맷은 mtd(MK)의 `mtd-section-2-achievement.md`와 거의 동일하다. 차이는 두 가지뿐이다:
1. `as_of_date`를 항상 해당 월의 **마지막 날**로 준다 (monthly-section-1 참고).
2. 레이블 앞머리가 "기간"이 아니라 **"월"**이다 (예: "기간 예산대비 소진율" → "월 예산대비
   소진율") — mtd는 월 중간 시점 기준이라 "기간"을 쓰지만, monthly는 항상 월 전체를 다루므로
   "월"로 통일한다.

---

## MCP 도구 호출: `get_target_progress_v2`

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "해당 월의 마지막 날" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

> ⚠️ 범용 `target_progress` 툴을 여기 쓰지 않는다 — naver 전용 브랜드는 매출/ROAS가 전부 0으로
> 나온다 (mtd-section-2와 동일한 이유). `get_target_progress_v2`는 target과 actual을 한 번의
> 호출로 모두 반환한다.

---

## 필요 데이터

응답 필드를 그대로 매핑한다 (`target_roas`/`actual_roas`/`*_progress_ratio`는 비율값이므로
표시 시 × 100):

- `overview.budget_goal` ← `target_cost`
- `overview.budget_spent` ← `actual_cost`
- `overview.budget_spent_rate` ← `cost_progress_ratio × 100`
- `overview.revenue_goal` ← `target_revenue`
- `overview.revenue_actual` ← `actual_revenue`
- `overview.revenue_achievement_rate` ← `revenue_progress_ratio × 100`
- `overview.roas_goal` ← `target_roas × 100`
- `overview.roas_actual` ← `actual_roas × 100`

---

## HTML

```html
<!-- MONTHLY SECTION 2: 목표 달성 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">목표 달성 현황</div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 예산대비 소진율</div>
      <div style="font-size:32px; font-weight:700; color:#3b82f6; margin-bottom:12px;">{overview.budget_spent_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">월 목표</div><div style="font-weight:600;">{overview.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진비용</div><div style="font-weight:600;">{overview.budget_spent}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 목표 매출 대비 달성률</div>
      <div style="font-size:32px; font-weight:700; color:#16a34a; margin-bottom:12px;">{overview.revenue_achievement_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">월 목표</div><div style="font-weight:600;">{overview.revenue_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">월 매출</div><div style="font-weight:600;">{overview.revenue_actual}</div></div>
      </div>
    </div>

    <div style="padding:20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 누적 ROAS</div>
      <div style="font-size:32px; font-weight:700; color:#7c3aed; margin-bottom:12px;">{overview.roas_actual}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">월 목표</div><div style="font-weight:600;">{overview.roas_goal}%</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">월 ROAS</div><div style="font-weight:600;">{overview.roas_actual}%</div></div>
      </div>
    </div>

  </div>
</div>
```

## Script
없음 (정적 카드)

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- `get_target_progress_v2`가 예산 미설정 메시지("No naver budget/target available for {month}.")를 반환하면 목표 관련 필드 전체를
  "목표 미설정"으로 표시한다 — 임의로 0을 만들어 넣지 않는다.
- `monthly-section-1-kpi-goals.md`는 이 섹션과 항상 쌍으로, 바로 위에 렌더링한다 (같은
  `get_target_progress_v2` 응답 재사용, 별도 재호출 없음).
