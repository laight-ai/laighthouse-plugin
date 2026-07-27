# Daily Section 2: 목표 달성 현황 (Overview)

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

---

## 분기 A: Google/Meta 브랜드

**MCP 도구:** `target-progress` → `sales` 데이터

### 필요 데이터
- `sales.period_progress_pct`: 기간 진행률 (%) — 예: 3.3
- `sales.period_label`: 기간 레이블 — 예: "1/30 days"
- `sales.budget_utilization_pct`: Monthly Budget Utilization (%)
- `sales.budget_utilization_diff`: 목표 대비 차이 (%p) — 음수면 빨강
- `sales.budget_goal`, `sales.budget_spent`: 목표/현재 ($)
- `sales.revenue_achievement_pct`: Monthly Revenue Achievement (%)
- `sales.revenue_achievement_diff`: 목표 대비 차이 (%p)
- `sales.revenue_goal`, `sales.revenue_actual`: 목표/현재 ($)
- `sales.roas_achievement_pct`: Monthly ROAS Achievement (%)
- `sales.roas_achievement_diff`: 목표 대비 차이 (%p)
- `sales.roas_goal`, `sales.roas_actual`: 목표/현재 (%)

### HTML

```html
<!-- DAILY SECTION 2 (Google/Meta): Overview -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="font-size:15px; font-weight:700; color:#1e293b; margin-bottom:16px;">Overview: Sales Campaign Performance</div>

  <div style="background:#f8fafc; border-radius:8px; padding:14px 18px; margin-bottom:16px;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <span style="font-size:12px; color:#64748b; background:#e2e8f0; border-radius:4px; padding:2px 8px;">Period Progress</span>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
      <span style="font-size:22px; font-weight:700; color:#1e293b; min-width:60px;">{sales.period_progress_pct}%</span>
      <span style="font-size:13px; color:#3b82f6; font-weight:600; min-width:80px;">{sales.period_label}</span>
      <div style="flex:1; position:relative; height:10px; background:#e2e8f0; border-radius:99px; overflow:visible;">
        <div style="height:100%; width:{sales.period_progress_pct}%; background:#3b82f6; border-radius:99px; position:relative;">
          <span style="position:absolute; right:-18px; top:-14px; font-size:11px; color:#3b82f6; font-weight:600; white-space:nowrap;">{sales.period_progress_pct}%</span>
        </div>
        <span style="position:absolute; left:0; bottom:-16px; font-size:11px; color:#94a3b8;">0%</span>
        <span style="position:absolute; right:0; bottom:-16px; font-size:11px; color:#94a3b8;">100%</span>
      </div>
    </div>
  </div>

  <div style="display:grid; grid-template-columns:repeat(3,1fr); border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; margin-top:8px;">
    <div style="padding:18px 20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">Monthly Budget Utilization</div>
      <div style="font-size:26px; font-weight:700; color:#1e293b; margin-bottom:4px;">
        {sales.budget_utilization_pct}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(sales.budget_utilization_diff)};">{sales.budget_utilization_diff}%p</span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:10px;">
        <div><div style="color:#94a3b8;">Target</div><div style="font-weight:600;">${sales.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">Current</div><div style="font-weight:600;">${sales.budget_spent}</div></div>
      </div>
    </div>
    <div style="padding:18px 20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">Monthly Revenue Achievement</div>
      <div style="font-size:26px; font-weight:700; color:#1e293b; margin-bottom:4px;">
        {sales.revenue_achievement_pct}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(sales.revenue_achievement_diff)};">{sales.revenue_achievement_diff}%p</span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:10px;">
        <div><div style="color:#94a3b8;">Target</div><div style="font-weight:600;">${sales.revenue_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">Current</div><div style="font-weight:600;">${sales.revenue_actual}</div></div>
      </div>
    </div>
    <div style="padding:18px 20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">Monthly ROAS Achievement</div>
      <div style="font-size:26px; font-weight:700; color:#1e293b; margin-bottom:4px;">
        {sales.roas_achievement_pct}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(sales.roas_achievement_diff)};">{sales.roas_achievement_diff}%p</span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:10px;">
        <div><div style="color:#94a3b8;">Target</div><div style="font-weight:600;">{sales.roas_goal}%</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">Current</div><div style="font-weight:600;">{sales.roas_actual}%</div></div>
      </div>
    </div>
  </div>
</div>
```

### 렌더링 규칙 (분기 A)
- `diff_color(v)`: v < 0 → `#ef4444`, v > 0 → `#16a34a`, 0 → `#6b7280`
- diff 값은 항상 부호 포함 표시
- **Monthly ROAS Achievement 메인 수치**: `actual_mtd × 100`
- **Monthly ROAS Achievement diff**: `(actual_mtd × 100) - (target_mtd × 100)` 단순 차이

---

## 분기 B: naver 브랜드 ⭐ 신규

mtd(MK)의 `mtd-section-2-achievement.md`와 **거의 동일한 포맷**이지만, 상단에 "기간 진척률"
진행바(분기 A의 Period Progress와 동일한 개념 — 이번 달 중 며칠이 지났는지)가 추가된다
(스크린샷 Daily_1 참고: "기간 진척률 93.3% 28/30일").

**MCP 도구 호출: `get_target_progress_v2`** (daily-section-1과 동일 호출 재사용, 별도
재호출 없음)

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

### 필요 데이터 (MCP)
- `period_progress_pct` = `target_date.day / 그 달의 총 일수 × 100` (이 스킬이 직접 계산 —
  `get_target_progress_v2` 응답에 없는 값이다. 예: 4월 28일 → 28/30 × 100 = 93.3%)
- `period_label` = `"{target_date.day}/{그 달의 총 일수}일"` (예: "28/30일")
- `overview.budget_goal` ← `target_cost`
- `overview.budget_spent` ← `actual_cost`
- `overview.budget_spent_rate` ← `cost_progress_ratio × 100`
- `overview.budget_spent_diff` = `overview.budget_spent_rate - period_progress_pct` (소진 페이스가
  기간 진행률보다 빠른지/느린지 — 스크린샷의 "-7.1%p"에 해당)
- `overview.revenue_goal` ← `target_revenue`
- `overview.revenue_actual` ← `actual_revenue`
- `overview.revenue_achievement_rate` ← `revenue_progress_ratio × 100`
- `overview.revenue_achievement_diff` = `overview.revenue_achievement_rate - period_progress_pct`
- `overview.roas_goal` ← `target_roas × 100`
- `overview.roas_actual` ← `actual_roas × 100`
- `overview.roas_diff` = `overview.roas_actual - overview.roas_goal`

> ⚠️ **budget/revenue의 "diff"는 목표 ROAS처럼 target 대비가 아니라 "기간 진척률" 대비다** —
> 스크린샷에서 소진율 diff(-7.1%p)와 달성률 diff(+3.3%p)는 각각 `budget_spent_rate` /
> `revenue_achievement_rate`에서 `period_progress_pct`(93.3%)를 뺀 값이다. 즉 "이 날짜까지
> 균등하게 진행됐을 때의 기대치" 대비 실제 진행 속도를 보여준다. 반면 ROAS diff는 목표 ROAS
> 대비 단순 차이다 (기간 진척률과 무관 — ROAS는 원래 누적 페이스 개념이 없는 지표).

### HTML

```html
<!-- DAILY SECTION 2 (naver): 목표 달성 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">목표 달성 현황</div>

  <!-- 기간 진척률 바 -->
  <div style="background:#f8fafc; border-radius:8px; padding:14px 18px; margin-bottom:16px;">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 진척률</div>
    <div style="display:flex; align-items:center; gap:16px;">
      <span style="font-size:22px; font-weight:700; color:#1e293b; min-width:60px;">{period_progress_pct}%</span>
      <span style="font-size:13px; color:#3b82f6; font-weight:600; min-width:60px;">{period_label}</span>
      <div style="flex:1; position:relative; height:10px; background:#e2e8f0; border-radius:99px;">
        <div style="height:100%; width:{period_progress_pct}%; background:#3b82f6; border-radius:99px; position:relative;">
          <span style="position:absolute; right:-18px; top:-14px; font-size:11px; color:#3b82f6; font-weight:600; white-space:nowrap;">{period_progress_pct}%</span>
        </div>
        <span style="position:absolute; left:0; bottom:-16px; font-size:11px; color:#94a3b8;">0%</span>
        <span style="position:absolute; right:0; bottom:-16px; font-size:11px; color:#94a3b8;">100%</span>
      </div>
    </div>
  </div>

  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 예산대비 소진율</div>
      <div style="font-size:32px; font-weight:700; color:#3b82f6; margin-bottom:4px;">
        {overview.budget_spent_rate}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(overview.budget_spent_diff)};">{overview.budget_spent_diff}%p</span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:8px;">
        <div><div style="color:#94a3b8;">목표</div><div style="font-weight:600;">₩{overview.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진비용</div><div style="font-weight:600;">₩{overview.budget_spent}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 목표 매출 대비 달성률</div>
      <div style="font-size:32px; font-weight:700; color:#16a34a; margin-bottom:4px;">
        {overview.revenue_achievement_rate}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(overview.revenue_achievement_diff)};">{overview.revenue_achievement_diff}%p</span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:8px;">
        <div><div style="color:#94a3b8;">목표</div><div style="font-weight:600;">₩{overview.revenue_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">매출</div><div style="font-weight:600;">₩{overview.revenue_actual}</div></div>
      </div>
    </div>

    <div style="padding:20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 누적 ROAS</div>
      <div style="font-size:32px; font-weight:700; color:#7c3aed; margin-bottom:4px;">
        {overview.roas_actual}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(overview.roas_diff)};">{overview.roas_diff}%p</span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:8px;">
        <div><div style="color:#94a3b8;">목표</div><div style="font-weight:600;">{overview.roas_goal}%</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">ROAS</div><div style="font-weight:600;">{overview.roas_actual}%</div></div>
      </div>
    </div>

  </div>
</div>
```

### 렌더링 규칙 (분기 B)
- `diff_color(v)`: v < 0 → `#dc2626`, v > 0 → `#16a34a`, 0 → `#6b7280`
- diff 값은 항상 부호 포함 표시 (예: `-7.1%p`, `+3.3%p`)
- `get_target_progress_v2`가 예산 미설정 메시지("No naver budget/target available for {month}.")를 반환하면 목표 관련 필드 전체를
  "목표 미설정"으로 표시한다.

## Script (두 분기 공통)
없음 (정적 카드)
