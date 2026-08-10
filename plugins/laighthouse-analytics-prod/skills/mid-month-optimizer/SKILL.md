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
> **허용 계산식** 6개와 조정안 산출(references 기반 주간 예산 결정)뿐이다.

**허용 계산식** (이 스킬에 명시된 표기 변환):
1. **월 잔여예산** = `monthly_budget − month_to_date_cost`
2. **잔여 기간 편성 합계** = `주간 조정안 × remaining_weeks` (매체별·총계 동일)
3. **일평균 환산** = `주간 금액 ÷ 7` (Scenario 2 전용)
4. **증감률 Δ%** = (조정안 ÷ base_value − 1) × 100
5. **일당 예산 (기존 → 변경)** = base_value ÷ 7 → 조정안 ÷ 7, 괄호에 주간과 동일한 Δ% 표기
6. **잔여 예산** = 매체별 월 예산(budget_goal/target) − 집행된 예산(spent/actual); 합계 행은 monthly_budget − month_to_date_cost

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
3. **20% 초과 증액 게이트 (증액이 있을 때만)**: 조정안 중 기존(base_value) 대비 20%를
   넘는 **증액** 매체가 하나라도 있으면, 표를 렌더링하기 전에
   `decisions=[...]` + 1차 답변 4개 인자로 2차를 조기 호출해 서버 게이트를 트리거한다
   (`approved`/`over_change_confirmed`는 넣지 않는다). 증액 매체가 없으면 이 단계를
   건너뛰고 바로 4단계(표 렌더링)로 간다.
   - elicitation 가능한 클라이언트에서는 확인 대화상자가 직접 뜨고, 사용자가 확인하면
     `stage="over_change_confirmed"`로 돌아온다 — 아직 아무것도 저장되지 않았다.
   - 불가 환경에서는 `stage="needs_user_input"`으로 돌아온다 — `questions[0].question`
     (서버가 작성한 초과 증액 목록 질문)을 **문구 그대로** 사용자에게 보여주고 답을
     기다린다. 스스로 질문을 다시 작문하거나 예고만 하고 넘어가는 것은 금지다.
   - 사용자가 동의하면 이후 호출에 `over_change_confirmed=true`를 더하고, 거절하면
     해당 매체 조정안을 재산출해 2단계부터 다시 진행한다.
4. **표 렌더링**: 아래 시나리오 판정에 따라 표를 사용자에게 보여준다. 저장 여부는 아직
   묻지 않은 상태다.
5. **승인 후 저장 (2단계 핸드셰이크)**: 표를 사용자에게 보여준 뒤 2차를 호출한다
   (게이트를 통과한 경우 `over_change_confirmed=true` 포함, `approved`는 넣지 않는다).
   이 호출은 저장하지 않고 `stage="needs_user_approval"`과 최종안 요약(`message`)만
   돌려준다 — 저장 대화상자는 뜨지 않는다. 요약을 표와 함께 사용자에게 보여주고
   채팅에서 명시적 동의를 받은 뒤에만 같은 인자에 `approved=true`를 더해 다시 호출해
   저장한다(거절이면 `approved=false`). **표를 보여주고 동의받기 전에는 절대
   `approved=true`를 설정하지 않는다. phase 2를 표 렌더링 전에 미리 호출하지 않는다.**

## 산출 규칙

- **증액 불가 = 월 총액 고정**: can_increase_budget=false는 이번 달 총 예산을 늘릴 수 없다는 뜻이지, 개별 매체 증액 금지가 아니다. 총액 한도 내에서 한 매체를 늘리고 다른 매체를 줄이는 재배분은 허용되며, 참고치의 양수 후보도 재배분 범위에서는 선택할 수 있다. 성과 하락 근거가 없는 매체는 base_value 유지가 기본값이다. 이 경우 주간 합계의 상한은 (monthly_budget − month_to_date_cost) ÷ remaining_weeks다 — 월 전망이 월 예산을 넘는 조정안은 서버가 오류로 거부한다.
- **참고치 후보는 근거이지 선택지가 아니다**: 총액 상한 등 제약에 걸리면 방향이 다른 후보로 갈아타지 말고, 원래 근거가 가리키는 방향을 유지한 채 상한에 맞춰 금액을 보정한다. 예: 참고치가 +33.5%를 가리키는데 상한이 +27.4%까지만 허용하면 +27.4%로 보정하고, rationale에 "참고치 +33.5%를 총액 상한에 맞춰 +27.4%로 보정"이라고 명시한다. 제약 때문에 증액 근거 매체를 감액으로 뒤집는 것은 금지다.
- **네이버 브랜드검색(`NAVER:BRS`) 예산은 증감하지 않는다** — `base_value`를 그대로 넣고
  rationale에 '유지'라고 적는다.
- **20%를 초과하는 증액은 증액 매체가 있을 때만 서버가 확인을 요구한다** — 20%를 초과하는 증액 확인은 위 플로우 3단계의 2차 조기 호출로 서버 게이트에 맡긴다 — LLM이 질문을 대필하지 말고 서버가 돌려준 질문 문구를 그대로 중계한다. 2차 호출에서 어떤 매체든
  (조정안 − base_value) ÷ base_value가 20%를 넘는 증액이면 툴이 확인 elicitation을 띄우거나,
  elicitation 불가 환경에서는 `stage="needs_user_input"`으로 `over_change_confirmed`
  질문을 돌려준다. 그 경우 초과 매체 목록(+Δ%)을 사용자에게 그대로 보여주고 명시적
  동의를 받은 뒤 같은 인자에 `over_change_confirmed=true`를 더해 재호출한다
  (거절 시 `over_change_confirmed=false`). **사용자에게 보여주고 동의받기 전에는
  절대 true로 설정하지 않는다.** 감액은 게이트 대상이 아니며 폭 제한도 없다 — 확인을 피하려고 감액 폭을 20%로 잘라 맞추지 말고, 참고 구간이 가리키는 값을 그대로 제안한다.
- 변경 없는 매체도 `decisions`에 base_value 그대로 + rationale '유지'로 **전부** 포함한다.

## 시나리오 판정

`context.budget_reference.monthly_budget`이 **null도 0도 아니면 Scenario 1(월 예산 있음)**,
**null 또는 0이면 Scenario 2(월 예산 없음)**.

## Scenario 1 — 월 예산이 있는 경우

표 위에 컨텍스트 문장을 먼저 쓴다 (X월 X일은 budget_reference.week_end_date — 집계 기준일, 소진율은 허용 계산식 1의 재료로 계산):

> 지금까지 집계된 예산은 X월 X일까지이며, 이번 달 예산 {monthly_budget}원 중
> {month_to_date_cost ÷ monthly_budget × 100:.0f}%가 소진되었습니다.
> **월 잔여예산: {monthly_budget − month_to_date_cost}원**

예산 소진량 컬럼 데이터 수집 지침 (표 렌더링 전에 매체별로 조회):
- media가 `NAVER:채널` 형식(예: `NAVER:BRS`)이면
  `get_naver_channel_budget_progress(brand_name, month="당월 YYYY-MM", as_of_date=week_end_date)`를
  호출해 해당 채널 행의 `spent`를 쓴다. 채널 라벨 매핑: BRS→네이버 브랜드검색,
  PLINK→네이버 파워링크, NVSHOP→네이버 쇼핑검색, GFA_AD→네이버 GFA 애드부스트, GFA_DP→네이버 GFA 디스플레이. 잔여 예산 컬럼은 같은 응답의 해당 채널 `budget_goal − spent`를 쓴다.
- media가 최상위 매체명(naver/google/meta/tiktok)이면
  `get_target_progress_v2(brand_name, month, media, as_of_date=week_end_date)`의 cost 행
  actual 값을 쓴다. 이 툴의 응답은 JSON이 아니라 마크다운 표 문자열이므로, 표에서 cost 행의 actual 칸 값을 읽어낸다. 잔여 예산 컬럼은 같은 응답의 cost 행 `target − actual`을 쓴다.
- 이 조회는 표 렌더링 전에 **반드시 실제로 호출**한다 — 호출을 생략하고 '-'로 채우는 것은 금지다. brand_name은 이 플로우에서 지금까지 쓰던 값을 그대로 쓴다. 호출이 실패하거나 응답에 해당 채널이 없을 때만 그 칸을 '-'로 표기하고, 실패 사실(어떤 툴이 어떤 오류였는지)을 표 아래에 한 줄로 알린다. 값을 추정하거나 기억으로 채우지 않는다.

표 (매체별 1행, 금액은 천 단위 콤마):

| 매체 | 예산 소진량 (X월 X일까지) | 잔여 예산 | 기존 → 조정안 (주간) | 잔여 기간({remaining_weeks}주) 편성 합계 | 일당 예산 (기존 → 변경) |
|---|---:|---:|---:|---:|---:|
| {media} | {mtd_spent 또는 '-'} | {remaining_budget} | {base_value:,} → {final_weekly_budget:,} ({Δ%:+.1f}%) 또는 (+0.0% 유지) | {final_weekly_budget × remaining_weeks} | {base_value ÷ 7:,}원 → {final_weekly_budget ÷ 7:,}원 ({Δ%:+.1f}%) 또는 (+0.0% 유지) |
| **합계** | {Σmtd_spent (수집된 값만 합산, '-' 제외 시 '*' 각주)} | {monthly_budget − month_to_date_cost} | {Σbase:,} → {Σfinal:,} ({(Σfinal ÷ Σbase − 1) × 100:+.1f}%) | {Σfinal × remaining_weeks} | {Σbase ÷ 7:,}원 → {Σfinal ÷ 7:,}원 ({(Σfinal ÷ Σbase − 1) × 100:+.1f}%) |

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
