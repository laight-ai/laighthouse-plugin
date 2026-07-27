# Executive-MTD Section 1: 목표 달성 현황

**report_type:** `executive-mtd` (항상 포함) — naver 기반 default generator 브랜드 전용
(남양유업 등). mtd(MK)의 `mtd-section-2-achievement.md`와 **완전히 동일한 포맷/HTML/레이블**
이다 (Monthly report의 achievement 섹션과 달리 "기간"이라는 표현을 그대로 유지한다 — 이 보고서도
MTD를 다루므로 mtd(MK)와 동일하게 부분월 표현이 맞다).

---

## MCP 도구 호출: `get_target_progress_v2`

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

> ⚠️ 범용 `target_progress` 툴을 여기 쓰지 않는다 — naver 전용 브랜드는 매출/ROAS가 전부 0으로
> 나온다. `get_target_progress_v2`는 target과 actual을 한 번의 호출로 모두 반환한다.

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
<!-- EXECUTIVE-MTD SECTION 1: 목표 달성 현황 -->
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
- `get_target_progress_v2`가 예산 미설정 메시지("No naver budget/target available for {month}.")를 반환하면 목표 관련 필드 전체를
  "목표 미설정"으로 표시한다.
- 월 목표 카드(kpi-goals) 섹션은 제거되었다 — 이 섹션(목표 달성 현황)이 executive-mtd 보고서의 첫 번째 섹션이다.
