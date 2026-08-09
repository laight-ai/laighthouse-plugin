# Breezm Executive Daily Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
데일리 보고서에서도 이 카드는 **당월 MTD 목표 대비 진행 상황**을 그대로 보여준다 (`mtd`와
동일한 데이터·계산 로직 — 예산이 일 단위가 아니라 월 단위로 설정되므로, 짧은 기간 보고서에서도
"이번 달 전체 진행 상황"은 여전히 매일 확인할 가치가 있는 지표다). 모든 "매출"은 Airbridge
매출(`airbridge_revenue`), 광고 채널은 airbridge 응답 `channel` ∈ {`Google Ads`, `Meta Ads`,
`Naver Ads`} 행이다 (SKILL.md 공통 규칙 참고).

---

## MCP 도구 호출: `get_target_progress_v2` × 3 (media만 바꿔 반복)

```json
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "google", "as_of_date": "target_date" }
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "meta", "as_of_date": "target_date" }
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. 해당 매체 예산(media_mix)이
> 전혀 없으면 예외 대신 `"No {media} budget/target available for {month}."` 메시지 한 줄이
> 반환된다 — 오류로 취급하지 않는다. **표를 반환하더라도 `cost`/`revenue`는 서로 독립적으로
> 목표가 있을 수도 없을 수도 있다** — 실제로 브리즘은 현재 세 매체 모두 `cost`(예산) 목표는
> 등록돼 있지만 `revenue`(매출) 목표는 `target: 0`으로 비어 있는 상태다. 이 두 경우를 구분하지
> 않고 "표를 반환했으니 다 유효하다"고 가정하면 안 된다 (아래 계산 규칙 참고).

이 세 응답은 이 섹션에서만 쓴다 — `executive-daily` 보고서에는 아직 이 응답을 공유할 다른
섹션(예: `mtd`의 Channel별 예산 소진 현황 같은)이 정의되어 있지 않다. 나중에 그런 섹션이
추가되면 재사용하도록 갱신한다.

## ⚠️ 매출(실적)은 항상 Airbridge에서만 가져온다 — `get_target_progress_v2`의 revenue actual 금지

**절대 규칙**: `기간 매출`(실적)은 목표 유무와 무관하게 **항상**
`get_ad_performance_monthly_table`(`start_month`=당월, `end_month`=당월,
`day_offset`=target_date.day, `group_by: "media"`, **`media` 파라미터는 생략**) 1회 호출로
가져온다. `media`를 생략하면 이 도구는 등록된 모든 매체(google/meta/naver/airbridge 등)를 한
응답에 함께 반환한다 — 이 호출 하나로 아래 세 가지를 전부 충당한다:
1. 이 섹션(매출 실적) — airbridge 행 중 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의
   `airbridge_revenue` 합.
2. 아래 「계산 규칙」의 **no-budget fallback 소진액** — google/meta/naver 행(매체당 이미 합산된
   한 줄)의 `cost`.
3. (fallback이 필요 없는 매체라도 이 호출 자체는 항상 나가므로 추가 판단 없이 매번 이 응답을
   그대로 캐시해두고 필요한 값만 골라 쓴다.)

응답에는 `media`가 `google`/`meta`/`naver`/`airbridge` 외의 값(예: `ga4`)인 행도 섞여 올 수
있다 — 이 섹션이 쓰지 않는 행이므로 무시한다. `get_target_progress_v2` 응답의 `revenue` 행
`actual` 값은 **매출 실적으로 절대 쓰지 않는다** — google/meta도 이 값이 Airbridge와 일치한다는
보장이 없으므로 셋 다 예외 없이 Airbridge를 원천으로 쓴다.

```json
{ "brand_name": "breezm", "start_month": "당월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "media", "day_offset": "target_date.day" }
```

⚠️ 이 호출은 **목표 유무를 판단하기 전에, `get_target_progress_v2` 3회 호출과 같은 배치(한
메시지)에서 동시에** 발사한다 — 예전에는 "목표가 없는 매체가 있으면 그때 가서 fallback을
추가 호출"하는 조건부 2차 라운드였지만, 이제는 이 호출 하나가 매출 실적과 fallback 소진액
후보를 항상 함께 가져오므로 조건 분기를 기다릴 필요가 없다 (SKILL.md 「병렬 호출 지침」 참고).

## 계산 규칙 (매체별로 cost/revenue를 독립적으로 판단)

각 매체(google/meta/naver) 응답을 아래처럼 개별 판단한다:

- **완전히 no-budget 메시지**(`"No {media} budget/target available..."`)인 매체 → `목표 예산`
  N/A, `소진액`은 위에서 이미 받아둔 `get_ad_performance_monthly_table`(media 생략) 응답 중
  해당 매체 행의 `cost`를 그대로 쓴다 — 추가 호출이 필요 없다.
  (no-budget이 아닌 매체는 이 값을 쓸 필요 없다 — 아래처럼 `get_target_progress_v2`의
  cost actual을 그대로 쓴다.)
- **표를 반환**하는 매체 → `cost` 행 `target`이 0보다 크면 `목표 예산` = target, `소진액` =
  actual을 그대로 쓴다. `target`이 0이거나 없으면(현재 관측된 바 없음) 위 no-budget과 동일하게
  N/A + 위 공유 응답의 해당 매체 `cost`로 처리한다.
- `revenue` 행은 **cost와 별개로** 판단한다: `target`이 0보다 크면 `목표 매출` = target을 그대로
  쓴다. `target`이 0이면(현재 브리즘의 기본 상태) `목표 매출` N/A로 표시하고, 그 매체는 목표
  매출 합산·매출 달성률·목표 ROAS 계산에서 제외한다. (`revenue` 행 `actual`은 위 규칙대로 어떤
  경우에도 쓰지 않는다.)

집계(세 매체 합산):
- `목표 예산` = 목표 예산이 유효한 매체들의 target 합 (하나도 없으면 N/A)
- `소진액` = 세 매체 소진액(정상 값 또는 fallback) 전부 합
- `소진율` = 소진액 ÷ 목표 예산 × 100 (`목표 예산`이 N/A면 전체도 N/A) — 목표 없는 매체의
  소진액도 분자에는 포함되므로, 일부 매체만 목표가 있으면 소진율이 얼핏 왜곡돼 보일 수 있다
  (아래 고정 각주로 갈음한다 — 구체적으로 어떤 매체인지는 명시하지 않는다).
- `목표 매출` = 목표 매출이 유효한 매체들의 target 합 (하나도 없으면 N/A — 현재 브리즘 기본 상태)
- `기간 매출` = 위 "매출은 항상 Airbridge" 규칙으로 구한 세 매체 매출 합 (fallback 개념 없이
  항상 이 값)
- `매출 달성률` = 기간 매출 ÷ 목표 매출 × 100 (`목표 매출`이 N/A면 N/A)
- `목표 ROAS` = 목표 매출 ÷ 목표 예산 × 100 (둘 중 하나라도 N/A면 N/A)
- `실제 ROAS` = 기간 매출 ÷ 소진액 × 100 (소진액 0이면 N/A)
- 목표(예산 또는 매출)가 없는 매체가 하나라도 있으면 아래 HTML의 고정 각주
  (`{TARGET_ACHIEVEMENT_FOOTNOTE}`)를 표시한다 — 어떤 매체의 어떤 목표가 없는지는 나열하지
  않는다.

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.

---

## HTML

```html
<!-- BREEZM EXECUTIVE DAILY SECTION 1: 목표 달성 현황 (TARGET ACHIEVEMENT) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">목표 달성 현황 ({MM}월 1일~{MM}월 {DD}일)</div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 예산대비 소진율</div>
      <div style="font-size:28px; font-weight:700; color:#1e293b; margin-bottom:12px;">{소진율}</div>
      <div style="display:flex; justify-content:center; gap:16px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표 예산</div><div style="font-weight:600;">{목표_예산}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진액</div><div style="font-weight:600;">{소진액}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 목표 매출 대비 달성률</div>
      <div style="font-size:28px; font-weight:700; color:#1e293b; margin-bottom:12px;">{매출_달성률}</div>
      <div style="display:flex; justify-content:center; gap:16px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표 매출</div><div style="font-weight:600;">{목표_매출}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">기간 매출</div><div style="font-weight:600;">{기간_매출}</div></div>
      </div>
    </div>

    <div style="padding:20px; text-align:center; display:flex; flex-direction:column; justify-content:center; align-items:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">실제 ROAS</div>
      <div style="font-size:28px; font-weight:700; color:#1e293b; margin-bottom:10px;">{실제_ROAS}</div>
      <div style="font-size:12px; color:#94a3b8;">목표 ROAS</div>
      <div style="font-size:12px; font-weight:600; color:#64748b;">{목표_ROAS}</div>
    </div>

  </div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">{TARGET_ACHIEVEMENT_FOOTNOTE}</p>
</div>
```

## Script
없음 (정적 카드)

## 렌더링 규칙
- 카드 제목의 `{MM}`/`{DD}`는 데이터 기간에 맞춰 채운다 — 둘 다 `target_date` 기준이며, 시작은
  항상 당월 1일이므로 `{MM}월 1일~{MM}월 {DD}일` 형식에서 두 `{MM}`은 같은 값(당월)이고 `{DD}`는
  `target_date`의 일(day)이다 (예: 기준일이 7월 15일이면 "7월 1일~7월 15일").
- `{TARGET_ACHIEVEMENT_FOOTNOTE}`: 목표(예산 또는 매출)가 없는 매체가 하나라도 있을 때만
  다음 **고정 문구**를 그대로 쓴다 — 어떤 매체의 어떤 목표가 없는지 구체적으로 나열하지 않는다:
  `* 매체별 예산 및 목표 매출이 등록되지 않은 경우, 현황이 제대로 표시되지 않을 수 있습니다.`
  모든 매체에 예산·매출 목표가 다 있으면 이 각주 자체를 표시하지 않는다.
- 값 표기: 비율/ROAS는 % 소수점 1자리, 금액은 천 단위 콤마 원화. N/A인 값은 문자 그대로 `N/A`.
- 소진율/매출 달성률/실제 ROAS 큰 숫자는 색을 입히지 않는다 — 기본 텍스트 색상(`#1e293b`)으로
  통일해서 표시한다 (양수/음수 강조색은 이 카드에 쓰지 않는다).
- no-budget 메시지는 오류가 아니다 — "데이터 준비 중" 카드로 대체하지 않고 N/A 규칙대로 렌더링한다.
- airbridge 응답의 실제 `channel` 값이 상수(`Google Ads`/`Meta Ads`/`Naver Ads`)와 다르면 조용히
  0을 만들지 말고 카드 아래에 불일치를 명시한다.