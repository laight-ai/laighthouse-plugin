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

### PPT 섹션 (분기 A)

```json
{
  "type": "kpi_cards",
  "cards": [
    { "label": "Monthly Budget Plan", "value": "${sales.budget_goal}" },
    { "label": "Monthly Revenue Target", "value": "${sales.revenue_goal}" },
    { "label": "Monthly ROAS Target", "value": "{sales.roas_goal}%" }
  ]
}
```

- 이 세 카드는 목표값만 표시하는 정적 카드이므로 `diff`/`diff_value`는 넣지 않는다.
- 금액 필드(`sales.budget_goal`/`sales.revenue_goal`)는 `toLocaleString()` 스타일 천 단위 콤마
  포맷 문자열로 만들어 넣는다.

---

## 분기 B: naver 브랜드 ⭐ 신규

mtd(MK)의 `mtd-section-1-kpi-goals.md`와 **완전히 동일한 포맷/HTML/도구**다 — daily는 하루 기준
스냅샷이므로 `as_of_date`를 항상 사용자가 지정한 기준일(`target_date`) 그대로 쓴다.

**MCP 도구 호출: `get_target_progress_v2`** (daily-section-2-overview.md와 동일 호출 재사용)

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

> ⚠️ **범용 `target-progress`(v1)를 naver 브랜드에 쓰지 않는다** — v1은 `aw_compiled`/
> `fb_compiled`(Google/Meta) 실적 테이블만 보므로 naver 전용 브랜드는 매출/ROAS 목표·실적이
> 전부 0으로 나온다. `get_target_progress_v2`(v2)가 유일한 정확한 소스다.

### 필요 데이터 (MCP)
응답 필드를 그대로 매핑한다 (roas는 비율값이므로 표시 시 × 100):
- `monthly_budget_goal` ← `target_cost`
- `monthly_revenue_goal` ← `target_revenue`
- `monthly_roas_goal` ← `target_roas × 100`

### PPT 섹션 (분기 B)

```json
{
  "type": "kpi_cards",
  "cards": [
    { "label": "월 예산 목표", "value": "₩{monthly_budget_goal}" },
    { "label": "월 매출 목표", "value": "₩{monthly_revenue_goal}" },
    { "label": "월 ROAS 목표", "value": "{monthly_roas_goal}%" }
  ]
}
```

- 이 세 카드는 목표값만 표시하는 정적 카드이므로 `diff`/`diff_value`는 넣지 않는다.
- 금액 필드(`monthly_budget_goal`/`monthly_revenue_goal`)는 `toLocaleString()` 스타일 천 단위
  콤마 포맷 문자열로 만들어 넣는다.
