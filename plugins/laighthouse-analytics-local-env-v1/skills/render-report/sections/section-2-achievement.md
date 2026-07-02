# Section 2: 목표 달성 현황

**트리거 키워드:** `목표 달성`

---

## MCP 도구 호출: `target-progress`

`report_type`에 따라 전달 인자가 다르다.

### daily
```json
{
  "report_type": "daily",
  "data_type": "sales"
}
```
- 최상단 섹션에는 **sales** 데이터만 표시

### weekly / mtd
```json
{
  "report_type": "weekly",
  "data_type": ["sales", "branding"]
}
```
- 응답에 sales + branding 모두 포함
- **최상단 섹션(목표 달성 현황 카드)에는 sales 데이터만 표시**
- branding 데이터는 하단 보조 섹션에 별도 표시

### monthly
```json
{
  "report_type": "monthly",
  "data_type": ["sales", "branding"]
}
```
- weekly와 동일한 규칙: 최상단 카드는 sales, 하단에 branding 보조 섹션

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

| report_type | target-progress 인자 | 최상단 카드 | branding 보조 섹션 |
|------------|---------------------|------------|------------------|
| daily | `data_type: "sales"` | sales | ❌ 표시 안 함 |
| weekly | `data_type: ["sales","branding"]` | sales | ✅ 표시 |
| mtd | `data_type: ["sales","branding"]` | sales | ✅ 표시 |
| monthly | `data_type: ["sales","branding"]` | sales | ✅ 표시 |
