---
name: mid-month-optimizer
description: >
  월중(mid-month) 예산 최적화 플로우 가이드. "월중 예산 최적화", "이번 달 남은 예산 조정",
  "mid-month 예산", "주간 예산 조정안" 요청 시 사용. laighthouse MCP 툴
  optimize_mid_month_budget을 2회 호출하는 플로우와, 월 예산 유무에 따른 시나리오별
  조정안 표 렌더링 형식을 정의한다.
metadata:
  version: "1.0.0"
---

## 역할

`optimize_mid_month_budget` MCP 툴의 호출 플로우를 진행하고, 결과를 **월 예산 유무로
분기한 표**로 렌더링하는 스킬. 조정안 수치의 산출 근거는 툴이 돌려주는
`budget_reference.groups[].references[]`(과거 같은 성과 국면 구간의 광고비 변화율·후보액)와
사용자 답변뿐이다.

## 데이터 처리 원칙 (절대 지침)

> 🚫 MCP 응답 값을 의심·재집계·보정하지 않는다. 이 스킬에서 허용되는 계산은 아래
> **허용 계산식** 3개와 조정안 산출(references 기반 주간 예산 결정)뿐이다.

**허용 계산식** (이 스킬에 명시된 표기 변환):
1. **월 잔여예산** = `monthly_budget − month_to_date_cost`
2. **잔여 기간 편성 합계** = `주간 조정안 × remaining_weeks` (매체별·총계 동일)
3. **일평균 환산** = `주간 금액 ÷ 7` (Scenario 2 전용)
4. **증감률 Δ%** = (조정안 ÷ base_value − 1) × 100
5. **일당 예산 (기존 → 변경)** = base_value ÷ 7 → 조정안 ÷ 7, 괄호에 Δ% 표기

## 플로우

1. **1차 호출**: `optimize_mid_month_budget(brand_name=...)` — `decisions` 없이.
   - `stage="needs_user_input"`이면 `questions`의 질문을 사용자에게 그대로 물은 뒤,
     답변을 해당 인자(`can_increase_budget` / `increase_limit_note` /
     `unlisted_promotion_note` / `must_exhaust_budget`)에 담아 재호출한다.
     `collected`의 기존 답변은 바꾸지 말고 그대로 함께 전달한다.
   - `stage="context"`가 나올 때까지 반복.
2. **조정안 산출**: `context.budget_reference.groups[].references[]`의
   `cost_change_rate_pct`·`candidate_weekly_budget` 목록 전체와 사용자 답변
   (증액 가능 여부·한도, 프로모션, 예산 소진 필요 여부)을 근거로 매체별 **주간** 예산
   1개 값을 정한다. 아래 **산출 규칙**을 반드시 지킨다.
3. **표 렌더링**: 아래 시나리오 판정에 따라 표를 사용자에게 보여준다.
4. **동의 후 2차 호출**: 사용자가 채팅에서 명시적으로 동의하면
   `decisions=[{"media", "final_weekly_budget", "rationale"}, ...]` + 1차 답변 4개 인자를
   그대로 담아 재호출한다. `stage="needs_user_approval"`이면 `message`를 보여주고 동의를
   받은 뒤 `approved=true`로 재호출(거절이면 `approved=false`). **사용자에게 보여주고
   동의받기 전에 `approved=true`를 설정하지 않는다.**

## 산출 규칙

- **네이버 브랜드검색(`NAVER:BRS`) 예산은 증감하지 않는다** — `base_value`를 그대로 넣고
  rationale에 '유지'라고 적는다.
- **±20% 초과 변경은 서버가 확인을 요구한다** — 2차 호출에서 어떤 매체든
  |조정안 − base_value| ÷ base_value가 20%를 넘으면 툴이 확인 elicitation을 띄우거나,
  elicitation 불가 환경에서는 `stage="needs_user_input"`으로 `over_change_confirmed`
  질문을 돌려준다. 그 경우 초과 매체 목록(+Δ%)을 사용자에게 그대로 보여주고 명시적
  동의를 받은 뒤 같은 인자에 `over_change_confirmed=true`를 더해 재호출한다
  (거절 시 `over_change_confirmed=false`). **사용자에게 보여주고 동의받기 전에는
  절대 true로 설정하지 않는다.**
- 변경 없는 매체도 `decisions`에 base_value 그대로 + rationale '유지'로 **전부** 포함한다.

## 시나리오 판정

`context.budget_reference.monthly_budget`이 **null도 0도 아니면 Scenario 1(월 예산 있음)**,
**null 또는 0이면 Scenario 2(월 예산 없음)**.

## Scenario 1 — 월 예산이 있는 경우

표 위에 컨텍스트 문장을 먼저 쓴다 (X월 X일은 budget_reference.week_end_date — 집계 기준일, 소진율은 허용 계산식 1의 재료로 계산):

> 지금까지 집계된 예산은 X월 X일까지이며, 이번 달 예산 {monthly_budget}원 중
> {month_to_date_cost ÷ monthly_budget × 100:.0f}%가 소진되었습니다.
> **월 잔여예산: {monthly_budget − month_to_date_cost}원**

MTD 컬럼 데이터 수집 지침 (표 렌더링 전에 매체별로 조회):
- media가 `NAVER:채널` 형식(예: `NAVER:BRS`)이면
  `get_naver_channel_budget_progress(brand_name, month="당월 YYYY-MM", as_of_date=week_end_date)`를
  호출해 해당 채널 행의 `spent`를 쓴다. 채널 라벨 매핑: BRS→네이버 브랜드검색,
  PLINK→네이버 파워링크, NVSHOP→네이버 쇼핑검색.
- media가 최상위 매체명(naver/google/meta/tiktok)이면
  `get_target_progress_v2(brand_name, month, media, as_of_date=week_end_date)`의 cost 행
  actual 값을 쓴다.
- 매핑 실패·데이터 없음이면 해당 칸은 '-'로 표기하고 추정하지 않는다.

표 (매체별 1행, 금액은 천 단위 콤마):

| 매체 | X월 X일까지 집행된 예산 | 조정안 (주간) | 일당 예산 (기존 → 변경) | 잔여 기간({remaining_weeks}주) 편성 합계 |
|---|---:|---:|---:|---:|
| {media} | {mtd_spent 또는 '-'} | {final_weekly_budget} | {base_value ÷ 7:,}원 → {final_weekly_budget ÷ 7:,}원 (Δ% 표기: 증가면 `+X.X% 증가`, 감소면 `−X.X% 감소`, 0이면 `변동 없음`) | {final_weekly_budget × remaining_weeks} |
| **합계** | {Σmtd_spent (수집된 값만 합산, '-' 제외 시 '*' 각주)} | {Σfinal} | {Σbase ÷ 7:,}원 → {Σfinal ÷ 7:,}원 (Δ% 표기: 증가면 `+X.X% 증가`, 감소면 `−X.X% 감소`, 0이면 `변동 없음`) | {Σfinal × remaining_weeks} |

"X월 X일"은 `budget_reference.week_end_date`(집계 기준일, 위 컨텍스트 문장과 동일 기준)를 쓴다.

표 아래 월 전망 한 줄:

> 월 전망: 집행 {month_to_date_cost} + 잔여 {remaining_weeks}주 × {Σfinal}
> = {month_to_date_cost + remaining_weeks × Σfinal}원 (월 예산 대비 {…:.0f}%)

## Scenario 2 — 월 예산이 없는 경우

잔여예산 컬럼 없이 **일평균 기준**으로 렌더링한다 (허용 계산식 3):

| 매체 | 기존 일평균 (base_value ÷ 7) | 조정 일평균 (조정안 ÷ 7) | Δ |
|---|---:|---:|---:|
| {media} | {base_value ÷ 7} | {final_weekly_budget ÷ 7} | {(조정÷기존 − 1) × 100:+.1f}% |
| **합계** | {Σbase ÷ 7} | {Σfinal ÷ 7} | {…:+.1f}% |

`monthly_budget`이 없으므로 월 잔여예산·월 전망 문장은 쓰지 않는다.

기존 일평균이 0이면 Δ는 계산하지 않고 '-'로 표기한다.
