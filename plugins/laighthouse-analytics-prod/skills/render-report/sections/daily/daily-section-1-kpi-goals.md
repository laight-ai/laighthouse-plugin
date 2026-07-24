# Daily Section 1: 월 목표 카드

**report_type:** `daily` (항상 포함)

⚠️ **`daily`는 브랜드의 광고 매체에 따라 두 개의 분기로 나뉜다** — `mtd`/`monthly`/
`executive-mtd`처럼 별도 폴더로 나누지 않고, **이 섹션 파일 하나가 두 분기를 모두 처리**한다.
어떤 분기를 쓸지는 브랜드의 실제 광고 매체로 판단한다:

- **분기 A — Google/Meta 브랜드** (Aqua Glow, Saturday Skin 등, `saturdayskin` generator)
- **분기 B — naver 브랜드** (다형식품, 남양유업 등, `default` generator) ⭐ 신규 지원

---

## 분기 A: Google/Meta 브랜드

**MCP 도구:** `target-progress` → `sales` 데이터

### 필요 데이터
- `sales.budget_goal`: Monthly Budget Plan ($)
- `sales.revenue_goal`: Monthly Revenue Target ($)
- `sales.roas_goal`: Monthly ROAS Target (%)

### HTML

```html
<!-- DAILY SECTION 1 (Google/Meta): 월 목표 카드 -->
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; margin-bottom:16px; background:white;">
  <div style="padding:20px 24px; border-right:1px solid #e2e8f0;">
    <div style="font-size:12px; color:#3b82f6; font-weight:500; margin-bottom:10px;">Monthly Budget Plan</div>
    <div style="font-size:28px; font-weight:700; color:#1e293b;">${sales.budget_goal}</div>
  </div>
  <div style="padding:20px 24px; border-right:1px solid #e2e8f0;">
    <div style="font-size:12px; color:#3b82f6; font-weight:500; margin-bottom:10px;">Monthly Revenue Target</div>
    <div style="font-size:28px; font-weight:700; color:#1e293b;">$ {sales.revenue_goal}</div>
  </div>
  <div style="padding:20px 24px;">
    <div style="font-size:12px; color:#3b82f6; font-weight:500; margin-bottom:10px;">Monthly ROAS Target</div>
    <div style="font-size:28px; font-weight:700; color:#1e293b;">{sales.roas_goal} %</div>
  </div>
</div>
```

---

## 분기 B: naver 브랜드 ⭐ 신규

mtd(MK)의 `mtd-section-1-kpi-goals.md`와 **완전히 동일한 포맷/HTML/도구**다 — daily는 하루 기준
스냅샷이므로 `as_of_date`를 항상 사용자가 지정한 기준일(`target_date`) 그대로 쓴다.

**MCP 도구 호출: `get_naver_target_progress`** (daily-section-2-overview.md와 동일 호출 재사용)

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```

> ⚠️ **범용 `target-progress`(v1)를 naver 브랜드에 쓰지 않는다** — v1은 `aw_compiled`/
> `fb_compiled`(Google/Meta) 실적 테이블만 보므로 naver 전용 브랜드는 매출/ROAS 목표·실적이
> 전부 0으로 나온다. `get_naver_target_progress`(v2)가 유일한 정확한 소스다.

### 필요 데이터 (MCP)
응답 필드를 그대로 매핑한다 (roas는 비율값이므로 표시 시 × 100):
- `monthly_budget_goal` ← `target_cost`
- `monthly_revenue_goal` ← `target_revenue`
- `monthly_roas_goal` ← `target_roas × 100`

### HTML

```html
<!-- DAILY SECTION 1 (naver): 월 목표 카드 -->
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:16px;">
  <div class="card">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 예산 목표</div>
    <div style="font-size:22px; font-weight:700; color:#1e293b;">₩{monthly_budget_goal}</div>
  </div>
  <div class="card">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 매출 목표</div>
    <div style="font-size:22px; font-weight:700; color:#1e293b;">₩{monthly_revenue_goal}</div>
  </div>
  <div class="card">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 ROAS 목표</div>
    <div style="font-size:22px; font-weight:700; color:#1e293b;">{monthly_roas_goal}%</div>
  </div>
</div>
```

## Script
없음 (두 분기 모두 정적 카드)
