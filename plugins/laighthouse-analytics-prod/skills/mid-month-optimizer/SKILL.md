---
name: mid-month-optimizer
description: >
  월중(mid-month) 예산 최적화 플로우 가이드. "월중 예산 최적화", "이번 달 남은 예산 조정",
  "mid-month 예산", "주간 예산 조정안" 요청 시 사용. laighthouse MCP 툴
  optimize_mid_month_budget의 질문·승인 플로우와, 월 예산 유무에 따른 시나리오별
  조정안 표 렌더링 형식을 정의한다.
metadata:
  version: "1.3.0"
---

## 역할

`optimize_mid_month_budget` MCP 툴의 호출 플로우를 진행하고, 결과를 **월 예산 유무로
분기한 표**로 렌더링하는 스킬.

**조정 폭과 매체별 최종 주간 예산 금액은 전부 툴이 사용자 답변으로 산출한다.** 이 스킬이
하는 일은 세 가지뿐이다:

1. 툴이 돌려주는 **질문을 사용자에게 문구 그대로 중계하고, 답변을 툴 인자로 되돌려주기**
2. 매체별 **rationale(판단 근거) 작성**
3. 툴이 돌려준 금액을 **표로 렌더링하기**

고를 수 있는 조정 레벨이나 배수는 없다. 조정 규칙(어떤 답변이 폭을 어떻게 바꾸는지)은
툴 내부에만 있고, 툴이 요약(`message`)에 산출 내역을 적어 돌려준다 — 그 내역을 그대로
전달하면 되고, 규칙을 추측해 설명하지 않는다.

## 데이터 처리 원칙 (절대 지침)

> 🚫 MCP 응답 값을 의심·재집계·보정하지 않는다. 이 스킬에서 허용되는 계산은 아래
> **허용 계산식** 6개뿐이다. 주간 예산 금액과 증감 폭은 툴이 산출하므로 직접 계산하거나
> 조정하지 않는다.

**허용 계산식** (이 스킬에 명시된 표기 변환):
1. **월 잔여예산** = `monthly_budget − month_to_date_cost`
2. **잔여 기간 편성 합계** = `주간 조정안 × remaining_weeks` (매체별·총계 동일)
3. **일평균 환산** = `주간 금액 ÷ 7` (Scenario 2 전용)
4. **증감률 Δ%** = (조정안 ÷ base_value − 1) × 100
5. **일당 예산 (기존 → 변경)** = base_value ÷ 7 → 조정안 ÷ 7, 괄호에 주간과 동일한 Δ% 표기
6. **잔여 예산** = 매체별 월 예산(budget_goal/target) − 집행된 예산(spent/actual); 합계 행은 monthly_budget − month_to_date_cost

## 사용자에게 물어야 하는 질문은 둘뿐이다

툴이 필요할 때 정확한 문구로 돌려준다 — **직접 작문하지 말고 그대로 중계한다.**

- **① 효율 전망 (1차 호출)**: 이달 남은 기간 중 광고 효율에 변동을 줄 만한 이벤트·프로모션·
  명절 등의 변수가 있는지. 답변에서 두 가지를 읽어낸다 — (a) 효율이 **크게 개선 / 크게 악화 /
  없음·모호** 중 어느 쪽인지, (b) 특정 매체에만 해당하는지.
- **② 매체별 사유 (2차 호출, 해당 매체가 있을 때만)**: 툴이 근거를 보고 확인이 필요하다고
  판단한 매체에 대해, 상대적으로 높은 효율에도 증액/감액하지 않은 이유가 있었는지.
  **매체마다 한 건씩** 돌아오며, 사유 유무가 조정 폭을 바꾼다.

두 질문 모두 **사용자에게 실제로 물어야 한다.** 예고만 하고 넘어가거나, 답을 추측해
채우거나, 질문을 다시 작문하는 것은 금지다.

## 플로우

1. **1차 호출**: `optimize_mid_month_budget(brand_name=...)` — `decisions` 없이.
   - `stage="needs_user_input"`이면 `questions`의 **① 효율 전망** 질문을 문구 그대로 물은 뒤,
     답변을 인자로 담아 재호출한다:
     - `efficiency_outlook` — `improve`(크게 개선) / `worsen`(크게 악화) / `none`(없음·모호)
     - `unlisted_promotion_note` — 사용자 답변 **원문**(없으면 '없음')
     - `outlook_media` — 사용자가 특정 매체만 지목한 경우 그 매체명 목록
       (`budget_reference.groups[].media`와 정확히 일치). **전체이거나 언급이 없으면 생략한다**
       (생략 = 전체 매체).
   - elicitation 대화상자가 뜬 환경에서는 답변이 `context.efficiency_outlook` /
     `context.outlook_media` / `context.unlisted_promotion_note`로 돌아온다 — **2차 호출에
     그 값을 그대로 다시 전달한다.**
   - 증액 여부와 예산 소진 여부는 묻지 않으며 `can_increase_budget=false`(월 총액 고정) /
     `must_exhaust_budget=true`(예산 소진)가 기본 적용된다 — 사용자가 대화에서 명시적으로
     다르게 요구한 경우에만 해당 인자를 명시 전달해 오버라이드한다.
   - `stage="context"`가 나올 때까지 반복.
2. **decisions 작성**: `budget_reference.groups[].media`마다 항목 하나씩,
   `decisions=[{"media": ..., "rationale": ...}]` 형태로 **모든 media를 빠짐없이** 담는다.
   - `rationale`에는 그 매체를 왜 그렇게 판단했는지(근거의 방향, 판정, 제약 등)를 적는다.
     근거는 그룹의 `avg_cost_change_rate_pct`·`candidate_weekly_budget`, 판정
     (`classification`), 사용자의 전망 답변, 기본 정책값이다.
   - `final_weekly_budget`은 넣지 않는다 — 넣어도 무시된다. **금액이나 증감 폭을 직접
     계산해 넣으려 하지 않는다.**
3. **2차 호출 (저장 없음)**: `decisions=[...]` + 1차에서 받은 답변 인자
   (`efficiency_outlook`, `unlisted_promotion_note`, 있었다면 `outlook_media`,
   오버라이드한 정책 인자)로 호출한다 — `approved`는 넣지 않는다.
   - **매체별 사유 질문(②)이 돌아오는 경우**: `stage="needs_user_input"`으로 게이트 대상
     매체마다 질문 한 건씩(`questions[].arguments`가
     `decisions[<매체>].over_change_reason`) 돌아온다. 각 질문을 **문구 그대로** 사용자에게
     보여주고 답을 받은 뒤, 그 답을 해당 매체의 `decisions` 항목에 `over_change_reason`으로
     담아 재호출한다.
     - 사유가 있다는 답이면 **답변 원문**을, 사유가 없다는 답이면 **빈 문자열(`""`)**을 넣는다.
     - **사유를 대신 추측해 적지 않는다.** 사유 유무가 조정 폭을 바꾼다.
     - elicitation 대화상자가 뜬 환경에서는 받은 사유가 `collected`에 담겨 돌아온다 —
       재호출 시 각 `decisions` 항목의 `over_change_reason`에 **그대로 다시 넣는다.**
     - 이 질문 자체가 큰 폭 변경에 대한 확인이다. 별도의 확인 인자는 없다.
   - 사유가 모두 모이면 `stage="needs_user_approval"`과 최종안 요약(`message` — 매체별
     기존 → 최종 금액과 산출 내역, 주간 합계, 월 전망)이 돌아온다. 아직 아무것도 저장되지
     않았다. 그대로 4단계로 간다.
   - 게이트에 걸릴지 미리 따져 조건부로 호출하지 말고 항상 이 호출을 거친다.
4. **표 렌더링**: 3단계에서 받은 최종안 요약(`message`)의 **매체별 최종 금액을 그대로**
   써서 아래 시나리오 판정에 따라 표를 사용자에게 보여준다. 금액을 직접 계산하거나
   재조정하지 않는다. 저장 여부는 아직 묻지 않은 상태다.
   - `message`에 **`[경고]` 또는 `[참고]` 라인이 있으면 표와 함께 그대로 전달한다** —
     빠뜨리거나 요약해서 흐리지 않는다. 이것은 저장을 막는 오류가 아니라 사용자가 알고
     결정해야 하는 정보다(아래 **산출 규칙** 참고).
5. **승인 후 저장**: 표와 요약을 사용자에게 보여주고 채팅에서 명시적 동의를 받은 뒤에만
   같은 인자에 `approved=true`를 더해 다시 호출해 저장한다(거절이면 `approved=false`;
   사유를 받았다면 `over_change_reason`도 계속 함께 보낸다). 저장 대화상자는 뜨지 않는다 —
   동의는 채팅에서 받는다. **표를 보여주고 동의받기 전에는 절대 `approved=true`를
   설정하지 않는다.**

## 산출 규칙

- **금액과 증감 폭은 툴의 몫이다**: 이 스킬은 질문 중계와 rationale, 표 렌더링만 한다.
  조정 폭이 만족스럽지 않아 보여도 임의로 다시 만들지 말고, 근거가 부족하다면 사용자에게
  다시 물어 답변을 갱신한 뒤 재호출한다. 근거의 증액/감액 방향은 어떤 답변에도 뒤집히지
  않으므로, 방향을 바꾸려고 답변을 손대는 것은 금지다.
- **증액 불가 = 월 총액 고정 (기본값)**: `can_increase_budget`는 기본 false다 — 이번 달 총
  예산을 늘릴 수 없다는 뜻이지, 개별 매체 증액 금지가 아니다. 총액 한도 내에서 한 매체를
  늘리고 다른 매체를 줄이는 재배분은 허용된다.
- **월 전망 경고는 차단이 아니라 전달 대상이다**: 월 전망이 월 예산을 넘거나(총액 고정
  정책), 예산 소진이 필요한데 크게 밑돌면 툴이 요약에 `[경고]`/`[참고]` 라인을 붙여
  돌려준다 — **오류가 아니며 저장도 막히지 않는다.** 그 라인을 표와 함께 사용자에게 그대로
  보여주고, 이대로 진행할지 확인을 받는다. 경고를 피하려고 조정안을 임의로 줄이거나
  숨기지 않는다.
- **네이버 브랜드검색(`NAVER:BRS`)**: 다른 매체와 마찬가지로 `decisions`에 포함하고
  `rationale`에 '유지'라고 적는다. 금액은 툴이 근거와 답변으로 정한다.
- 변경하지 않을 매체도 `decisions`에 rationale '유지'를 담아 **전부** 포함한다.

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

요약(`message`)에 `[경고]`/`[참고]` 라인이 있으면 이 줄 바로 아래에 그대로 덧붙인다.

## Scenario 2 — 월 예산이 없는 경우

잔여예산 컬럼 없이 **일평균 기준**으로 렌더링한다 (허용 계산식 3):

| 매체 | 기존 일평균 (base_value ÷ 7) | 조정 일평균 (조정안 ÷ 7) | Δ |
|---|---:|---:|---:|
| {media} | {base_value ÷ 7} | {final_weekly_budget ÷ 7} | {(조정÷기존 − 1) × 100:+.1f}% |
| **합계** | {Σbase ÷ 7} | {Σfinal ÷ 7} | {…:+.1f}% |

`monthly_budget`이 없으므로 월 잔여예산·월 전망 문장은 쓰지 않는다.

기존 일평균이 0이면 Δ는 계산하지 않고 '-'로 표기한다.
