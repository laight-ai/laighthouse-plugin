---
name: mid-month-optimizer
description: >
  월중(mid-month) 예산 최적화 플로우 가이드. "월중 예산 최적화", "이번 달 남은 예산 조정",
  "mid-month 예산", "주간 예산 조정안" 요청 시 사용. laighthouse MCP 툴
  optimize_mid_month_budget을 2회 호출하는 플로우와, 월 예산 유무에 따른 시나리오별
  조정안 표 렌더링 형식을 정의한다.
metadata:
  version: "1.2.1"
---

## 역할

`optimize_mid_month_budget` MCP 툴의 호출 플로우를 진행하고, 결과를 **월 예산 유무로
분기한 표**로 렌더링하는 스킬. 판단 근거는 툴이 돌려주는 `budget_reference.groups[]`의
**평균 변화율(`avg_cost_change_rate_pct`)과 단일 후보액(`candidate_weekly_budget`)**,
툴이 함께 주는 **조정 레벨 목록(`adjustment_levels`)**, 그리고 사용자 답변뿐이다.
매체별 **최종 주간 예산 금액은 툴이 계산해서 돌려준다** — 이 스킬은 금액을 만들지 않고,
매체마다 조정 레벨 하나를 고를 뿐이다.

## 데이터 처리 원칙 (절대 지침)

> 🚫 MCP 응답 값을 의심·재집계·보정하지 않는다. 이 스킬에서 허용되는 계산은 아래
> **허용 계산식** 6개뿐이다. 주간 예산 금액은 툴이 산출하므로 직접 계산하지 않는다 —
> 이 스킬이 정하는 것은 매체별 **조정 레벨 하나**뿐이다.

**허용 계산식** (이 스킬에 명시된 표기 변환):
1. **월 잔여예산** = `monthly_budget − month_to_date_cost`
2. **잔여 기간 편성 합계** = `주간 조정안 × remaining_weeks` (매체별·총계 동일)
3. **일평균 환산** = `주간 금액 ÷ 7` (Scenario 2 전용)
4. **증감률 Δ%** = (조정안 ÷ base_value − 1) × 100
5. **일당 예산 (기존 → 변경)** = base_value ÷ 7 → 조정안 ÷ 7, 괄호에 주간과 동일한 Δ% 표기
6. **잔여 예산** = 매체별 월 예산(budget_goal/target) − 집행된 예산(spent/actual); 합계 행은 monthly_budget − month_to_date_cost

## 플로우

1. **1차 호출**: `optimize_mid_month_budget(brand_name=...)` — `decisions` 없이.
   - 툴이 묻는 질문은 `unlisted_promotion_note`(미기입 프로모션·이벤트) 하나뿐이다.
     `stage="needs_user_input"`이면 `questions`의 질문을 사용자에게 그대로 물은 뒤,
     답변을 `unlisted_promotion_note` 인자에 담아 재호출한다.
   - 증액 여부와 예산 소진 여부는 더 이상 묻지 않으며
     `can_increase_budget=false`(월 총액 고정) / `must_exhaust_budget=true`(예산 소진)가
     기본 적용된다 — 사용자가 대화에서 명시적으로 다르게 요구한 경우에만 해당 인자를
     명시 전달해 오버라이드한다.
   - `stage="context"`가 나올 때까지 반복.
2. **조정 레벨 선택**: 매체마다 `context.adjustment_levels` 목록에서 레벨 **하나**를 골라
   `decisions=[{"media": ..., "adjustment_level": ..., "rationale": ...}]` 형태로 전달한다
   (`final_weekly_budget`은 넣지 않는다 — 넣어도 무시된다). 판단 근거는 그룹의
   `avg_cost_change_rate_pct`·`candidate_weekly_budget`, 판정(`classification`), 사용자의
   프로모션 답변, 그리고 기본 정책값(증액 불가·예산 소진 — 오버라이드했다면 그 값)이다.
   각 레벨이 무슨 뜻인지는 목록의 `description`에 적혀 있으니 그 설명만 읽고 고른다.
   목록에 없는 레벨을 기억이나 추측으로 만들어 쓰지 않는다. 아래 **산출 규칙**을 반드시
   지킨다.
3. **2차 호출 (저장 없음)**: `decisions=[...]` + `unlisted_promotion_note`(오버라이드한
   인자가 있으면 그것도 함께)로 호출한다 — `approved`/`over_change_confirmed`는 넣지
   않는다. 증감폭 판정은 **툴이 산출한 금액**으로 서버가 하므로, 게이트에 걸릴지를 미리
   따져 조건부로 호출하지 말고 항상 이 호출을 거친다.
   - 게이트에 걸리지 않으면 `stage="needs_user_approval"`과 최종안 요약(`message` —
     매체별 기존 → 최종 금액, 주간 합계, 월 전망)이 돌아온다. 아직 아무것도 저장되지
     않았다. 그대로 4단계로 간다.
   - **20% 초과 증액 게이트**: 서버 산출 금액이 기존(base_value) 대비 20%를 넘는 증액인
     매체가 있으면 아래 확인 절차가 먼저 돌아온다.
   - 서버 질문에는 초과 매체별 증액폭과 **decisions에 적은 판단 근거(rationale)**,
     그리고 반영되지 않은 히스토리(프로모션·재고·계약·정책 변경)가 있는지 묻는 문장이
     포함된다.
   - elicitation 가능한 클라이언트에서는 확인 대화상자가 직접 뜨고, 사용자가 확인하면
     `stage="over_change_confirmed"`로 돌아온다 — 아직 아무것도 저장되지 않았다.
   - 불가 환경에서는 `stage="needs_user_input"`으로 돌아온다 — `questions[0].question`
     (서버가 작성한 초과 증액 목록 질문)을 **문구 그대로** 사용자에게 보여주고 답을
     기다린다. 스스로 질문을 다시 작문하거나 예고만 하고 넘어가는 것은 금지다.
     중계할 때 자신의 판단 근거가 질문에 포함되어 있으므로 별도로 재작성하지 않는다.
   - **히스토리 분기**: 사용자가 반영되지 않은 히스토리를 제공하면(대화 답변이든,
     elicitation 다이얼로그의 `history_note`든 — 후자는 `stage="aborted"` 메시지에
     노트가 담겨 돌아온다) 절대 `over_change_confirmed`를 설정하지 말고, 그 히스토리를
     반영해 2단계(조정 레벨 선택)부터 다시 고른 뒤 진행한다. 이때의
     `stage="aborted"`는 중단이 아니라 재선택 신호다.
   - 판단 근거에 동의하고 히스토리가 없을 때만 같은 인자에 `over_change_confirmed=true`를
     더해 다시 호출한다 — 그러면 `stage="needs_user_approval"`과 최종안 요약이 돌아온다.
     거절하면 `over_change_confirmed=false`로 호출하거나 해당 매체의 레벨을 더 보수적으로
     다시 골라 2단계부터 진행한다.
4. **표 렌더링**: 3단계에서 받은 최종안 요약(`message`)의 **매체별 최종 금액을 그대로**
   써서 아래 시나리오 판정에 따라 표를 사용자에게 보여준다. 금액을 직접 계산하거나
   재조정하지 않는다. 저장 여부는 아직 묻지 않은 상태다.
5. **승인 후 저장**: 표와 요약을 사용자에게 보여주고 채팅에서 명시적 동의를 받은 뒤에만
   같은 인자에 `approved=true`를 더해 다시 호출해 저장한다(거절이면 `approved=false`;
   게이트를 거쳤다면 `over_change_confirmed=true`도 계속 함께 보낸다). 저장 대화상자는
   뜨지 않는다 — 동의는 채팅에서 받는다. **표를 보여주고 동의받기 전에는 절대
   `approved=true`를 설정하지 않는다.**

## 산출 규칙

- **증액 불가 = 월 총액 고정 (기본값)**: can_increase_budget는 기본 false다 — 이번 달 총 예산을 늘릴 수 없다는 뜻이지, 개별 매체 증액 금지가 아니다. 총액 한도 내에서 한 매체를 늘리고 다른 매체를 줄이는 재배분은 허용되며, 그룹의 후보액이 양수(증액)여도 재배분 범위에서는 선택할 수 있다. 성과 하락 근거가 없는 매체는 가장 보수적인 레벨이 기본값이다. 이 경우 주간 합계의 상한은 (monthly_budget − month_to_date_cost) ÷ remaining_weeks다 — 월 전망이 월 예산을 넘으면 서버가 오류로 거부하며, 그때는 같은 방향에서 더 보수적인 레벨로 다시 골라 호출한다.
- **방향은 근거가 정하고, 레벨은 폭만 정한다**: 총액 상한 등 제약에 걸리면 방향이 다른 근거로 갈아타지 말고, 같은 방향에서 더 보수적인 레벨을 골라 다시 호출한다. rationale에는 어떤 근거로 그 레벨을 골랐는지(그리고 제약 때문에 더 보수적으로 골랐다면 그 사실을) 적는다. 레벨은 금액이 아니라 근거의 변화율에 적용되므로 **증액 근거가 감액으로 뒤집히는 일은 어떤 레벨을 골라도 일어나지 않는다 — 툴이 구조적으로 막는다.** 그래도 근거와 반대 방향을 노리고 레벨을 고르는 것은 금지다.
- **네이버 브랜드검색(`NAVER:BRS`)은 조정 대상이 아니다** — 목록에서 가장 보수적인 레벨을
  골라 rationale에 '유지'라고 적는다.
- **20%를 초과하는 증액은 증액 매체가 있을 때만 서버가 확인을 요구한다** — 이 확인은 위 플로우 3단계의 2차 호출에서 서버 게이트에 맡긴다 — LLM이 질문을 대필하지 말고 서버가 돌려준 질문 문구를 그대로 중계한다 (질문에 자신의 판단 근거(rationale)와 히스토리 질문이 이미 포함되어 있으므로 별도로 재작성하지 않는다). 2차 호출에서 어떤 매체든
  서버 산출 금액이 base_value 대비 20%를 넘는 증액이면 툴이 확인 elicitation을 띄우거나,
  elicitation 불가 환경에서는 `stage="needs_user_input"`으로 `over_change_confirmed`
  질문을 돌려준다. 그 경우 초과 매체 목록(+Δ% + 판단 근거)을 사용자에게 그대로 보여주고,
  사용자가 판단 근거에 동의하고 반영되지 않은 히스토리가 없을 때만 같은 인자에
  `over_change_confirmed=true`를 더해 재호출한다
  (거절 시 `over_change_confirmed=false`). 사용자가 히스토리를 제공하면
  `over_change_confirmed`를 설정하지 말고 그 히스토리를 반영해 레벨을 다시 고른다 —
  이때 서버가 돌려주는 `stage="aborted"`는 중단이 아니라 재선택 신호다.
  **사용자에게 보여주고 동의받기 전에는
  절대 true로 설정하지 않는다.** 감액은 게이트 대상이 아니며 폭 제한도 없다 — 확인을 피하려고 더 보수적인 레벨로 낮춰 맞추지 말고, 근거가 가리키는 대로 레벨을 고른다.
- 변경하지 않을 매체도 `decisions`에 레벨과 rationale '유지'를 담아 **전부** 포함한다.

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
