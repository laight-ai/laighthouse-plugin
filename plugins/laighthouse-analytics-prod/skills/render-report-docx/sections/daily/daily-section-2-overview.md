# Daily Section 2: 목표 달성 현황 (Overview) — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/daily/daily-section-2-overview.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션 (분기 A)

```json
{
  "type": "kpi_cards",
  "cards": [
    {
      "label": "Period Progress",
      "value": "{sales.period_progress_pct}% ({sales.period_label})"
    },
    {
      "label": "Monthly Budget Utilization",
      "value": "{sales.budget_utilization_pct}% ({sales.budget_utilization_diff}%p)",
      "diff": "Target ${sales.budget_goal} · Current ${sales.budget_spent}",
      "diff_value": {sales.budget_utilization_diff}
    },
    {
      "label": "Monthly Revenue Achievement",
      "value": "{sales.revenue_achievement_pct}% ({sales.revenue_achievement_diff}%p)",
      "diff": "Target ${sales.revenue_goal} · Current ${sales.revenue_actual}",
      "diff_value": {sales.revenue_achievement_diff}
    },
    {
      "label": "Monthly ROAS Achievement",
      "value": "{sales.roas_achievement_pct}% ({sales.roas_achievement_diff}%p)",
      "diff": "Target {sales.roas_goal}% · Current {sales.roas_actual}%",
      "diff_value": {sales.roas_achievement_diff}
    }
  ]
}
```

- "Overview: Sales Campaign Performance"라는 상단 타이틀은 별도 `heading` 섹션으로 만들지 않고
  카드 묶음 자체로 이 섹션을 표현한다(정적 문서에서는 카드 4개로 충분).
- "Period Progress"는 원본 HTML에서 진행률 바(progress bar) 하나뿐인 요약 정보이므로 `diff`/
  `diff_value` 없이 값 하나만 있는 카드로 표현한다 — 진행률(%)과 기간 레이블을 한 문자열로
  합친다.
- 나머지 세 카드는 원본 HTML의 "목표 대비 diff%p"를 `value` 문자열 안에 괄호로 이미 포함시켜
  텍스트로 보이게 하고, 그와 별개로 **부호 판정 색칠 전용**인 `diff_value`에는 같은 값을 `%p`
  접미사 없는 순수 숫자로 한 번 더 넣는다(`build.py::_diff_color`가 `diff_value > 0`처럼 숫자
  비교를 하므로 문자열이 아니라 실제 JSON 숫자 타입이어야 한다). ⚠️ **위 JSON에서
  `"diff_value": {sales.budget_utilization_diff}`처럼 `diff_value` 자리의 플레이스홀더는 일부러
  따옴표 없이 적었다** — 실제 렌더링 시 그 자리에 숫자 리터럴(예: `-7.1`)을 그대로 채워 넣어야
  하며, `"{sales.budget_utilization_diff}"`처럼 따옴표로 감싸서 문자열로 만들면 안 된다(그렇게
  하면 `build.py`가 `TypeError`를 낸다). "Target/Current" 두 값 병기는 `diff` 문자열로 별도로
  담는다.
- `diff_color(v)`: v < 0 → 빨강, v > 0 → 초록, 0 → 회색 — 렌더러가 `diff_value`(순수 숫자)의
  부호를 보고 값 전체 텍스트에 색을 적용한다.
- **Monthly ROAS Achievement 메인 수치**: `actual_mtd × 100`
- **Monthly ROAS Achievement diff**: `(actual_mtd × 100) - (target_mtd × 100)` 단순 차이
- 금액 필드(`sales.budget_goal`/`sales.budget_spent`/`sales.revenue_goal`/`sales.revenue_actual`)는
  `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.

### 렌더링 규칙 (분기 A, 참고 — 원본 색상 로직)
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

### DOCX 섹션 (분기 B)

```json
{
  "type": "kpi_cards",
  "cards": [
    {
      "label": "기간 진척률",
      "value": "{period_progress_pct}% ({period_label})"
    },
    {
      "label": "월 예산대비 소진율",
      "value": "{overview.budget_spent_rate}% ({overview.budget_spent_diff}%p)",
      "diff": "목표 ₩{overview.budget_goal} · 소진비용 ₩{overview.budget_spent}",
      "diff_value": {overview.budget_spent_diff}
    },
    {
      "label": "월 목표 매출 대비 달성률",
      "value": "{overview.revenue_achievement_rate}% ({overview.revenue_achievement_diff}%p)",
      "diff": "목표 ₩{overview.revenue_goal} · 매출 ₩{overview.revenue_actual}",
      "diff_value": {overview.revenue_achievement_diff}
    },
    {
      "label": "월 누적 ROAS",
      "value": "{overview.roas_actual}% ({overview.roas_diff}%p)",
      "diff": "목표 {overview.roas_goal}%",
      "diff_value": {overview.roas_diff}
    }
  ]
}
```

- 제목 "목표 달성 현황"은 별도 `heading` 섹션으로 만들지 않고 카드 묶음 자체로 표현한다(분기 A와
  동일한 판단 — mtd-section-2 패턴 참고).
- "기간 진척률"은 분기 A의 "Period Progress"와 동일한 개념이므로 같은 방식(값 하나만 있는 카드)
  으로 표현한다.
- 나머지 세 카드는 분기 A와 동일하게 "목표 대비 diff%p"를 `value` 문자열 괄호 안에 텍스트로
  넣고, 부호 판정 색칠 전용인 `diff_value`에는 같은 값을 `%p` 접미사 없는 순수 숫자로 한 번 더
  넣는다(`build.py::_diff_color`가 숫자 비교를 하므로 문자열이 아니라 실제 JSON 숫자 타입이어야
  한다). ⚠️ **위 JSON에서 `"diff_value": {overview.budget_spent_diff}`처럼 `diff_value` 자리의
  플레이스홀더는 일부러 따옴표 없이 적었다** — 실제 렌더링 시 그 자리에 숫자 리터럴(예: `-7.1`)을
  그대로 채워 넣어야 하며, 따옴표로 감싸서 문자열로 만들면 안 된다(그렇게 하면 `build.py`가
  `TypeError`를 낸다). "목표/실제" 두 값 병기는 `diff` 문자열로 별도로 담는다.
- `diff_color(v)`: v < 0 → 빨강, v > 0 → 초록, 0 → 회색 — 렌더러가 `diff_value`(순수 숫자)의
  부호를 보고 값 전체 텍스트에 색을 적용한다.
- diff 값은 항상 부호 포함 표시 (예: `-7.1%p`, `+3.3%p`)
- `get_target_progress_v2`가 예산 미설정 메시지("No naver budget/target available for {month}.")를 반환하면 목표 관련 필드 전체를
  "목표 미설정"으로 표시한다.
- 금액 필드(`overview.budget_goal`/`overview.budget_spent`/`overview.revenue_goal`/
  `overview.revenue_actual`)는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어
  넣는다.

## DOCX 관련 공통 참고 (두 분기)
없음 (정적 카드 — 인터랙션 스크립트 불필요)
