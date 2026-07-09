# Section 2: 목표 달성 현황

**트리거 키워드:** `목표 달성`

---

## MCP 도구 호출: `target_progress`

도구 시그니처: `target_progress(brand_name, month, ctx, as_of_date=None, revenue_source="ad", campaign_type=None)`.
`campaign_type`(`"sales"` | `"branding"`)만 지원하며 `report_type`/`data_type` 인자는 없다 — sales/branding을
한 번에 반환하지 않으므로 **campaign_type을 바꿔 두 번 호출**한다. 응답은 `items`(3개: monthly_budget /
monthly_revenue / monthly_roas)의 `target_full_month`(목표)·`actual_mtd`(실적)를 사용해 아래 매핑을 재구성한다.

### daily
```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date", "campaign_type": "sales" }
```
- 최상단 섹션에는 **sales** 응답만 표시 (`campaign_type=sales` 1회 호출)

### weekly / mtd / monthly
```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date", "campaign_type": "sales" }
```
```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date", "campaign_type": "branding" }
```
- **최상단 섹션(목표 달성 현황 카드)에는 sales 응답만 표시**
- branding 응답은 하단 보조 섹션에 별도 표시

> ⚠️ **데이터 갭**: `target_progress`는 budget/revenue/roas 3개 지표만 반환한다. 브랜딩 보조 섹션의
> `impression_achievement_rate`/`impression_goal`/`impression_actual`/`cpm_goal`/`cpm_actual`은 이 도구로
> 채울 수 없다 (impression/CPM에 대한 "목표"는 어떤 generic 도구에도 존재하지 않음 — 실적만
> `get_branding_performance_monthly`로 조회 가능). 목표값이 없는 한 브랜딩 보조 섹션의 노출/CPM 카드는
> "목표 미설정" 표시로 대체하거나 생략한다. **naver 전용 도구를 새로 만들어 이 갭을 메우지 않는다.**

---

## 응답 데이터 구조

```json
{
  "sales": {
    "budget_spent_rate": 91.8,
    "budget_goal": "$112,181,818",
    "budget_spent": "$102,965,902",
    "revenue_achievement_rate": 100.9,
    "revenue_goal": "$521,000,000",
    "revenue_actual": "$525,452,088",
    "roas_goal": 464,
    "roas_actual": 510
  },
  "branding": {
    "budget_spent_rate": 88.2,
    "budget_goal": "$30,000,000",
    "budget_spent": "$26,460,000",
    "impression_achievement_rate": 102.3,
    "impression_goal": "5,000,000",
    "impression_actual": "5,115,000",
    "cpm_goal": 6000,
    "cpm_actual": 5810
  }
}
```

---

## HTML

### 최상단 카드 (sales — daily/weekly/monthly 공통)

```html
<!-- SECTION 2: 목표 달성 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">목표 달성 현황</div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{기간} 예산대비 소진율</div>
      <div style="font-size:32px; font-weight:700; color:#3b82f6; margin-bottom:12px;">{sales.budget_spent_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">{기간} 목표</div><div style="font-weight:600;">{sales.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진비용</div><div style="font-weight:600;">{sales.budget_spent}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{기간} 목표 매출 대비 달성률</div>
      <div style="font-size:32px; font-weight:700; color:#16a34a; margin-bottom:12px;">{sales.revenue_achievement_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">{기간} 목표</div><div style="font-weight:600;">{sales.revenue_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">{기간} 매출</div><div style="font-weight:600;">{sales.revenue_actual}</div></div>
      </div>
    </div>

    <div style="padding:20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{기간} 누적 ROAS</div>
      <div style="font-size:32px; font-weight:700; color:#7c3aed; margin-bottom:12px;">{sales.roas_actual}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">{기간} 목표</div><div style="font-weight:600;">{sales.roas_goal}%</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">{기간} ROAS</div><div style="font-weight:600;">{sales.roas_actual}%</div></div>
      </div>
    </div>

  </div>
</div>
```

### branding 보조 섹션 (weekly / monthly 에만 추가 렌더링)

`report_type`이 `weekly` 또는 `monthly`일 때만 아래 블록을 sales 카드 바로 아래에 추가한다.

```html
<!-- SECTION 2-B: 브랜딩 목표 달성 현황 (weekly/monthly only) -->
<div class="card" style="margin-bottom:16px; border-left:4px solid #8b5cf6;">
  <div class="section-title" style="color:#7c3aed;">브랜딩 목표 달성 현황</div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">예산 소진율</div>
      <div style="font-size:32px; font-weight:700; color:#8b5cf6; margin-bottom:12px;">{branding.budget_spent_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표</div><div style="font-weight:600;">{branding.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진</div><div style="font-weight:600;">{branding.budget_spent}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">노출수 달성률</div>
      <div style="font-size:32px; font-weight:700; color:#16a34a; margin-bottom:12px;">{branding.impression_achievement_rate}%</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표</div><div style="font-weight:600;">{branding.impression_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">실적</div><div style="font-weight:600;">{branding.impression_actual}</div></div>
      </div>
    </div>

    <div style="padding:20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">CPM</div>
      <div style="font-size:32px; font-weight:700; color:#0891b2; margin-bottom:12px;">${branding.cpm_actual}</div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표</div><div style="font-weight:600;">${branding.cpm_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">실적</div><div style="font-weight:600;">${branding.cpm_actual}</div></div>
      </div>
    </div>

  </div>
</div>
```

---

## Script
없음 (정적 카드)

---

## 렌더링 규칙 요약

| report_type | target_progress 호출 | 최상단 카드 | branding 보조 섹션 |
|------------|---------------------|------------|------------------|
| daily | `campaign_type=sales` 1회 | sales | ❌ 표시 안 함 |
| weekly | `campaign_type=sales`+`branding` 2회 | sales | ✅ 표시 (impression/CPM 목표는 갭) |
| mtd | `campaign_type=sales`+`branding` 2회 | sales | ✅ 표시 (impression/CPM 목표는 갭) |
| monthly | `campaign_type=sales`+`branding` 2회 | sales | ✅ 표시 (impression/CPM 목표는 갭) |
