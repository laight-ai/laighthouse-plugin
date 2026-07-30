---
name: render-report
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 보고서 생성 스킬. "보고서로 만들어줘", "레포트 형식으로 보여줘", "MTD 보고서",
  "Executive MTD 보고서", "임원용 MTD 보고서", "executive mtd", "라이트하우스 보고서",
  "성과 분석 보고서" 요청 시 사용. 지원하는 report_type은 `mtd`/`executive-mtd`/`daily` 세
  가지이며, monthly/weekly는 지원하지 않는다. 대상 브랜드는 브리즘 하나뿐이다.
metadata:
  version: "1.0.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 데이터를 받아 **라이트하우스 스타일 성과 보고서**로 렌더링하는 오케스트레이터. **대상
브랜드는 브리즘(airbridge 기반) 하나뿐이다.** 지원하는 `report_type`은
`mtd`/`executive-mtd`/`daily` 세 가지이며, 각각 완전히 독립된 폴더(`sections/mtd-type-b/`,
`sections/executive-mtd-type-b/`, `sections/daily-type-b/`)에서 자기 완결적으로 섹션을
가져온다 — 폴더 간 import는 없다.

| report_type | 목적 | 폴더 |
|---|---|---|
| `mtd` | 신규: airbridge 기반 브랜드(브리즘) — Google/Meta/Naver 광고 성과를 Airbridge에 기록된 매출과 엮어 보여주는 상세 MTD 보고서 (7개 섹션) | `sections/mtd-type-b/` |
| `executive-mtd` | 신규: 브리즘 (airbridge 기반, 임원 보고용) — 위 `mtd`를 임원이 딥다이브 없이 훑어볼 수 있도록 5개 섹션으로 재구성한 보고서 | `sections/executive-mtd-type-b/` |
| `daily` | 신규: 브리즘 (airbridge 기반, 실무자용 데일리 보고서) — 최근 7일 등 짧은 기간 단위로 매일 확인하는 일자별 성과 보고서 | `sections/daily-type-b/` |

세 report_type 모두 `brand_name`은 항상 `"breezm"`이고, naver 전용 도구를 일절 쓰지 않는다.
generic 도구(`get_ad_performance_daily_table`/`get_ad_performance_monthly_table`)와
`get_target_progress_v2`만 쓰며, 보고서의 모든 "매출"은 **Airbridge 매출**
(`media="airbridge"` 응답의 `airbridge_revenue`)이다. 광고 채널은 airbridge 응답의 `channel`
값이 `Google Ads`/`Meta Ads`/`Naver Ads`인 행으로 고정 정의한다 — 첫 airbridge 응답에서 실제
`channel` 값들을 확인하고, 이 상수와 다르면 조용히 0을 반환하지 말고 보고서에 불일치를 명시한다.
⚠️ **어떤 호출에도 `campaign-type` 파라미터를 넣지 않는다** — 넣으면 airbridge 행이 조용히
누락된다.

`executive-mtd`는 `mtd`와 같은 부분월(MTD) 데이터를 다루지만, 임원이 딥다이브 없이 훑어볼 수
있도록 목표 달성 현황 / Executive Summary / 월별 광고 성과 / 매출 추이 / Channel별 성과 비교,
5개 섹션으로 구성한 변형이다. 사용자가 "임원용 MTD", "executive mtd", "임원 보고서" 등을
요청하면 이 report_type을 쓴다. `mtd`/`executive-mtd` **둘 다 Executive Summary 섹션이
있다** — 각 report_type의 section-2 파일(`mtd-type-b-section-2-executive-summary.md`,
`executive-mtd-type-b-section-2-executive-summary.md`)이며, 서로 다른 파일이라 곁들이는
섹션 구성이 다르면 내용도 다를 수 있다. `df_dify` MCP는 어느 쪽도 호출하지 않고, AI가 같은
report_type의 다른 섹션 응답을 재사용해 직접 작성한다 (각 섹션 파일 참고) — 다만
프로모션/이벤트 정보만은 다른 섹션이 가져오지 않으므로 `list_promotions`를 Executive Summary
섹션에서 별도로 1회 호출한다 (해당 섹션 파일에 상세 규칙이 있으면 그것을 따른다).

`daily`는 실무자가 매일 확인하는 짧은 기간(예: 최근 7일, 또는 D-1 vs D-0 이틀) 단위 보고서다.
다만 목표 달성 현황(section-1)은 `mtd`와 동일하게 "월초부터 기준일까지"(당월 MTD)를 다룬다 —
예산이 월 단위이므로 짧은 보고서에서도 이 지표는 그대로 유효하다. section-3(최근 7일 성과)과
section-4/5(캠페인·광고그룹/광고 성과, D-1 vs D-0)는 `mtd`/`executive-mtd`와 달리 **기준일을
포함한 고정 일수 구간**(각각 7일, 이틀)을 다룬다. section-2(Executive Summary)는 `df_dify`를
호출하지 않고 다른 daily 섹션(1/3/4/5) 응답을 재사용해 AI가 직접 작성하며, "월초~기준일"
페이싱이 아니라 **D-1 vs D-0 하루 단위 변화**와 캠페인/광고그룹 특이사항 중심으로 쓴다 — `mtd`
의 Executive Summary와 분석 항목 구성이 다르다 (`daily-type-b-section-2-executive-summary.md`
참고). 현재 확정된 섹션은 section-1~5 다섯 개 전부다. 사용자가 "데일리 보고서", "일간
보고서", "daily 보고서" 등을 요청하면 이 report_type을 쓴다.

`monthly`/`weekly`는 이 스킬의 범위 밖이다 — 브리즘 외 다른 브랜드(naver 기반 브랜드,
Google/Meta 기반 브랜드)는 현재 이 플러그인에서 지원하지 않는다. 사용자가 monthly/weekly
보고서를 요청하면, 아직 지원하지 않는다고 알리고 mtd/executive-mtd/daily 중 무엇을 원하는지
확인한다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답 데이터는 이미 정제·가공이 끝난 최종 데이터다. 생각하지 말고 그대로 렌더링만 한다.**
> - 결측치 보정, 이상치 제거, 재집계, 재계산, 정렬·필터링, 반올림/포맷 변경, "이 값이 이상한 것
>   같다" 식의 임의 판단 — **전부 금지**. MCP가 준 값을 의심하거나 검증하지 않는다.
> - 예외는 오직 각 섹션 파일에 **명시적으로 적힌 표기 변환뿐**이다 (예: ROAS 소수 → % 변환,
>   목표 미존재 시 실적 대체 소스). 그 외에는 어떤 가공도 스스로 판단해서 추가하지 않는다.
> - 데이터가 비어있거나 갭이 있어도 채우거나 추정하지 않는다 — "데이터 부족 시" 규칙을 그대로
>   따른다.
> - 이 지침은 다른 모든 지시보다 우선한다. MCP → 값 → 화면, 이 사이에 어떤 사고/판단 단계도
>   끼워넣지 않는다.

## 실행 방식 절대 지침

> 🚫 **이 스킬을 실행하는 동안 `.py`/`.js`/`.ipynb` 등 별도 스크립트·노트북 파일을 절대 생성하지
> 않는다.** MCP 도구는 직접 호출하고, 그 결과를 곧바로 HTML 문자열 조합에 사용한다. 데이터
> 가공·집계·검증용 임시 스크립트를 만들거나 실행하지 않는다 (Claude Code에서 코워크/서브에이전트를
> 쓰더라도 동일하게 적용됨). 이 스킬이 만드는 파일은 오직 최종 보고서 HTML 하나뿐이다.
>
> ⏱ **긴 대기 없이 스켈레톤을 먼저 보여준다.** 2단계(target/achievement 호출) 응답을 받는 즉시,
> 나머지 섹션은 전부 "데이터 준비 중" placeholder(§ 데이터 부족 시 규칙과 동일한 마크업)로 채운
> 전체 골격을 1차로 Artifact에 게시한다. 이후 3단계에서 각 섹션 데이터가 준비되는 대로 같은
> Artifact 파일을 갱신(재게시)해 placeholder를 실제 값으로 교체한다 — 사용자가 빈 화면을 오래
> 기다리지 않도록 먼저 뼈대를 보여주고 채워나간다.

## 입력 파라미터

사용자 프롬프트에서 아래 항목을 파싱한다:

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| report_type | `mtd`, `executive-mtd`, 또는 `daily` | mtd |
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 MTD 보고서 |
| brand_name | MCP 호출용 브랜드명 — **항상 `breezm`**(`get_brand_list` 응답과 정확히 일치하는 값). 사람이 브랜드를 부를 때 쓰는 "브리즘"과는 다른 값이니 혼동하지 않는다 (아래 경고 참고) | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

> ⚠️ **"브리즘"과 `brand_name`을 혼동하지 않는다.** "브리즘"은 사람이 대화·보고서 제목에서
> 브랜드를 부르는 **표시명**일 뿐이다. 어떤 MCP 도구를 호출하든 실제 파라미터에 넣는
> `brand_name` 값은 **반드시 정확히 `"breezm"`**(영문 소문자, `get_brand_list` 응답 기준)
> 이어야 한다 — `"브리즘"`을 그대로 넣으면 `Unknown brand '브리즘'` 에러로 호출 자체가
> 실패한다. 사용자가 "브리즘", "breezm", "브리즘(breezm)" 등 어떤 표현으로 브랜드를 지칭하든
> **전부 같은 브랜드를 가리키는 것으로 인식**하고, 실제 도구 호출 시에는 항상 `"breezm"`으로
> 정규화해서 넣는다. 보고서 제목·완료 메시지 등 사람이 읽는 텍스트에는 계속 "브리즘"을 쓴다.

`mtd`/`executive-mtd` 모두 **섹션 구성은 report_type이 전부 결정**하며 사용자가 섹션을 골라
지정하는 개념이 없다 — 아래 표에 있는 파일을 항상 전부 렌더링한다.

---

## 실행 순서

1. 파라미터를 파싱하고 report_type을 확정한다 (`mtd`/`executive-mtd`/`daily`만 유효).
2. target/achievement 수치를 호출한다 — `mcp__laighthouse__get_target_progress_v2`를
   `{ "brand_name": "breezm", "month": "YYYY-MM", "media": "...", "as_of_date": "target_date" }`로
   **google/meta/naver 세 번**(`media`만 바꿔) 호출한다 — `mtd`/`executive-mtd` 공통 규칙이다
   (`sections/mtd-type-b/mtd-type-b-section-1-target-achievement.md` 참고). 세 매체 모두
   `"No {media} budget/target available for {month}."` 메시지가 돌아오거나 `cost`/`revenue`
   행의 `target`이 0이면(브리즘은 현재 `revenue` 목표가 세 매체 다 0이다) 해당 목표 필드는
   N/A로 표시하고, 대체 값은 `get_ad_performance_daily_table`이 아니라
   **`get_ad_performance_monthly_table`(`start_month`=`end_month`=당월,
   `day_offset`=target_date.day)**로 가져온다 — 날짜별 행을 직접 합산하는 것보다 훨씬 빠르다
   (섹션 파일의 대체 규칙 참고). 매출 실적(`기간 매출`/`광고 매출`)은 목표 유무와 무관하게
   **항상** 이 방식(`media="airbridge"`, `group_by:"media"`, `day_offset`)으로 가져온다 —
   `get_target_progress_v2`의 `revenue` 행 `actual`은 naver에서 0을 반환하는 버그가 확인되어
   매출 실적으로 절대 쓰지 않는다.
   ⚠️ ROAS 관련 수치(`target_roas`/`actual_roas`)는 비율값(예: 0.87, 5.06)으로 반환되므로
   반드시 × 100 후 표시한다 (0.87 → 87%, 5.06 → 506%).
3. 나머지 `mcp__laighthouse__*` generic 도구를 호출해 각 섹션 수치 데이터를 가져온다 (각 섹션
   파일에 명시된 정확한 tool명 참고).
   - **generic 도구**(`get_ad_performance_daily_table`/`get_ad_performance_monthly_table`)만
     쓴다 — naver 전용 도구는 브리즘에 적용되지 않으므로 절대 쓰지 않는다.
   - ⚠️ 이 계열 도구의 `group_by`는 **문자열 enum**(`total`/`media`/`campaign`/`ad-set`/`ad`)이다
     — `true`/`false` boolean으로 절대 보내지 않는다. 각 섹션 파일에 적힌 값(대부분 `"total"`)을
     문자열 그대로 그 섹션에서만 쓴다.
   - ⚠️ **어떤 호출에도 `campaign-type` 파라미터를 넣지 않는다** — 넣으면 airbridge 행이 조용히
     누락된다.
4. **`mtd`/`executive-mtd` 둘 다 section-2가 Executive Summary다.** `executive_summary`
   텍스트는 `df_dify` MCP를 호출하지 않고, AI가 같은 report_type의 다른 섹션 응답을 재사용해
   직접 작성한다. 어떤 섹션 응답을 근거로 쓰는지, 프로모션/이벤트 정보를 위해
   `mcp__laighthouse__list_promotions`를 추가로 호출하는지 등 세부 규칙은 report_type별
   section-2 파일에 각각 적혀 있으므로 **그 파일에 적힌 대로** 따른다
   (`sections/mtd-type-b/mtd-type-b-section-2-executive-summary.md`,
   `sections/executive-mtd-type-b/executive-mtd-type-b-section-2-executive-summary.md`).
   두 파일은 서로 다른 섹션 구성(예: `mtd`는 일일 매출 현황·Campaign 분석이 있고 `executive-mtd`
   는 매출 추이·Channel별 성과 비교가 있음)을 참고하므로 내용이 같지 않을 수 있다.
5. report_type에 대응하는 아래 표의 파일을 **순서대로 전부** import해 HTML을 조합한다.
6. 이 스킬 폴더의 `assets/chart.umd.min.js` 파일을 읽어 그 내용 전체를 `{CHART_JS_INLINE}` 자리에
   그대로 삽입한다 (CDN `<script src>` 절대 사용 금지 — 아래 보고서 골격의 경고 참고).
7. 아래 **보고서 골격**에 섹션들을 삽입해 렌더링한다. 완성된 HTML은 아래 **두 곳에 동시에** 낸다 —
   하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Claude Code(Artifact)에서 실행 중이면 Artifact 도구로 게시(위 스켈레톤과
     같은 파일을 갱신). `mcp__visualize__show_widget`이 있는 호스트에서는 그걸 쓴다.
   - **파일로 저장**: 동일한 최종 HTML을 `~/Downloads/laighthouse-reports/브리즘_{report_type}_
     {기준_일자}.html` 경로에 그대로 저장한다 (디렉터리가 없으면 새로 만든다). 파일명 예:
     `브리즘_mtd_2026-05-15.html`.
8. 렌더링 후 사용자에게 보내는 완료 메시지는 아래 **완료 메시지 형식**을 그대로 따른다 — 매번 다른
   문구로 즉석 요약하지 않는다. 저장된 파일 경로를 완료 메시지 마지막 줄에 덧붙인다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (MCP 호출 성공·실패 여부, 섹션 개수, 데이터
출처 등 기술적 디테일은 언급하지 않는다):

```
브리즘 {report_type 한글명}({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 html 파일 경로}
```

- `{report_type 한글명}`: `mtd` → "MTD 보고서", `executive-mtd` → "Executive MTD 보고서",
  `daily` → "데일리 보고서"
- `{기준_일자}`: 사용자가 지정한 기준 일자 (예: 2026-05-15)
- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 한 가지만 골라 한 문장으로 (예: "Naver
  Ads ROAS가 5,036.7%로 가장 두드러졌습니다"). 여러 개 나열하지 않는다.
- `{저장된 html 파일 경로}`: 7단계에서 저장한 `.html` 파일의 전체 경로.

예시:
```
브리즘 MTD 보고서(2026-05-15) 생성 완료.
가장 인상적인 부분: Naver Ads ROAS가 5,036.7%로 세 매체 중 가장 두드러졌습니다.
— by LaightAI
📁 C:\Users\minhyeok\Downloads\laighthouse-reports\브리즘_mtd_2026-05-15.html
```

---

## 섹션 Import 목록

### report_type: `mtd` (브리즘 전용, airbridge 기반, 항상 포함)

**총 7개 섹션.** 모든 MCP 호출에 `brand_name: "breezm"`을 넘기고, 보고서의 모든 "매출"은
Airbridge 매출(`airbridge_revenue`)이다. 광고 채널 상수(`Google Ads`/`Meta Ads`/`Naver Ads`),
첫 airbridge 응답 검증 규칙, `campaign-type` 금지 규칙은 위 「역할」의 설명을 따른다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 목표 달성 현황 | `@import sections/mtd-type-b/mtd-type-b-section-1-target-achievement.md` |
| 2 | Executive Summary | `@import sections/mtd-type-b/mtd-type-b-section-2-executive-summary.md` |
| 3 | 월별 광고 성과 | `@import sections/mtd-type-b/mtd-type-b-section-3-monthly-ad-performance.md` |
| 4 | 일일 매출 현황 | `@import sections/mtd-type-b/mtd-type-b-section-4-daily-revenue.md` |
| 5 | Campaign 분석 | `@import sections/mtd-type-b/mtd-type-b-section-5-campaign-analysis.md` |
| 6 | Channel별 예산 소진 현황 | `@import sections/mtd-type-b/mtd-type-b-section-6-channel-budget.md` |
| 7 | Campaign별 성과 | `@import sections/mtd-type-b/mtd-type-b-section-7-campaign-performance.md` |

`mtd`에는 **`매출 추이`나 `Channel별 성과 비교`(전월 vs 당월) 섹션이 없다** — 그 둘은
`executive-mtd` 전용 섹션이다. 대신 `mtd`는 일일 매출 현황(4번)과 Campaign 분석(5번)을 쓴다.

공통 표기 규칙: 비율/ROAS는 % 스케일로 소수점 1자리, 금액은 천 단위 콤마 원화. 분모가 0인
비율(ROAS/CPA/달성률 등)은 임의로 0을 넣지 말고 N/A로 표시한다. **차트 Y축이 원화 금액을
나타내는 경우 `₩` 접두어 + 천 단위 콤마로 표시한다**(예: `₩15,000,000`) — 만원/억원 등
축약 단위로 바꾸지 않는다 (표/카드의 금액 표기와 동일한 원칙).

`sections/mtd-type-b/` 폴더의 파일은 전부 브리즘(airbridge 기반) 기준으로 작성되어 있고, 다른
폴더를 import하지 않는다.

### report_type: `executive-mtd` (브리즘 전용, airbridge 기반, 임원 보고용, 항상 포함)

**총 5개 섹션.** `mtd`와 동일한 airbridge 기반 데이터를 쓰되, 임원이 훑어볼 수 있도록 핵심
섹션만 남긴 구성이다. `mtd`(7개 섹션)의 일일 매출 현황/Campaign 분석/Channel별 예산 소진
현황/Campaign별 성과 섹션은 여기에 없다. 반대로 매출 추이(6개월 라인 차트)와 Channel별 성과
비교(전월 vs 당월)는 `executive-mtd`에만 있고 `mtd`에는 없다 — 서로 완전히 겹치는 섹션이
아니다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 목표 달성 현황 | `@import sections/executive-mtd-type-b/executive-mtd-type-b-section-1-target-achievement.md` |
| 2 | Executive Summary | `@import sections/executive-mtd-type-b/executive-mtd-type-b-section-2-executive-summary.md` |
| 3 | 월별 광고 성과 | `@import sections/executive-mtd-type-b/executive-mtd-type-b-section-3-monthly-ad-performance.md` |
| 4 | 매출 추이 (6개월) | `@import sections/executive-mtd-type-b/executive-mtd-type-b-section-4-revenue-trend.md` |
| 5 | Channel별 성과 비교 (전월 vs 당월) | `@import sections/executive-mtd-type-b/executive-mtd-type-b-section-5-channel-comparison.md` |

파일명의 섹션 번호(1~5)가 이제 렌더링 순서(1→5)와 정확히 일치한다.

공통 표기 규칙은 `mtd`와 동일하다. 다만 변화율(광고 매출 변화율/ROAS 변화율)은 부호 포함
표기, **음수는 파란색, 양수는 빨간색**으로 표시한다 — 아래 「보고서 골격」의 공통 유틸
`changeColor`(양수 초록/음수 빨강)를 쓰지 않고, 이 섹션 파일에 명시된 대로 색상을 직접
지정한다 (`executive-mtd-type-b-section-5-channel-comparison.md` 참고). Executive Summary
섹션(2번)의 불릿 앞 점(●) 색상 규칙은 별도다 — 해당 섹션 파일의 `{DOT_COLOR}` 규칙을 따른다.

`sections/executive-mtd-type-b/` 폴더의 파일은 전부 브리즘(airbridge 기반) 기준으로 작성되어
있고, 다른 폴더를 import하지 않는다.

### report_type: `daily` (브리즘 전용, airbridge 기반, 실무자용 데일리 보고서, 항상 포함) ⭐ 신규

**총 5개 섹션. 구성이 전부 확정됐다.**

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 목표 달성 현황 | `@import sections/daily-type-b/daily-type-b-section-1-target-achievement.md` |
| 2 | Executive Summary | `@import sections/daily-type-b/daily-type-b-section-2-executive-summary.md` |
| 3 | 최근 7일 성과 | `@import sections/daily-type-b/daily-type-b-section-3-daily-performance-7days.md` |
| 4 | 캠페인 성과 (D-1 vs D-0) | `@import sections/daily-type-b/daily-type-b-section-4-campaign-performance.md` |
| 5 | 광고그룹 및 광고 성과 (D-1 vs D-0) | `@import sections/daily-type-b/daily-type-b-section-5-ad-performance.md` |

section-1(목표 달성 현황)은 `mtd-type-b-section-1-target-achievement.md`와 **완전히 동일한
데이터·계산 로직**을 쓴다 — "월초~기준일" 당월 MTD 목표 대비 진행 상황이다 (예산이 월 단위로
설정되므로, 데일리 보고서에서도 이 지표는 그대로 유효하다). section-3(최근 7일 성과)·
section-4(캠페인 성과)·section-5(광고그룹 및 광고 성과)는 `mtd`/`executive-mtd`의
"월초~기준일" 범위가 아니라 각각 **기준일을 포함한 고정 구간**(section-3은 7일, section-4/5는
D-1~D-0 딱 이틀)을 다룬다 — 다른 report_type과 기간 정의 자체가 다르다는 점에 유의한다.
section-3은 매체별 일자별 광고비(`get_ad_performance_daily_table`, `group_by:"total"`)와
airbridge 채널별 일자별 매출(같은 도구, `group_by:"media"`)을, section-4는 같은 도구를
`group_by:"campaign"`으로, section-5는 google/meta/naver는 `group_by:"ad"`(캠페인/광고그룹/
광고 3단계가 한 응답에 다 들어있음)로, airbridge는 `group_by:"campaign"`으로 호출한다 —
전부 section-1과 달리 `get_target_progress_v2`나 `day_offset`을 쓰지 않는다(고정 일수
구간이라 MTD 컷오프 개념이 없다). section-3의 프로모션 오버레이는
`mtd-type-b-section-4-daily-revenue.md`와 같은 브래킷 방식이며, 카테고리 축 밴드 폭 보정
(좌우 경계를 정확히 날짜 영역에 맞추는 것)까지 동일하게 적용한다. section-3의 Legend는
광고비/매출은 박스, ROAS는 라인 마커 순서(광고비 → 매출 → ROAS)로 고정한다. section-4/5는
캠페인(또는 광고그룹/광고)별로 D-1/D-0 값을 절대 합산하지 않고 날짜별로 각각 유지하며, D-0
값 아래에 D-1 대비 변화량(광고비/예약 CPA는 %, CTR/ROAS는 %p)을 **괄호로 감싸서** 표시한다 —
색상 규칙은 두 파일이 동일하다(양수=빨강/음수=파랑 조합이 지표별로 다르다는 점에 유의:
예약 CPA는 감소가 빨강이다). **두 파일 모두 D-0 광고비가 ₩10,000 이하인 행은 표에서 제외**
한다(조용히 제외 — 각주로만 안내). **section-5는 Airbridge가 캠페인보다 아래(광고그룹/광고) 단위로
매출을 귀속하지 않으므로, 같은 캠페인 아래 모든 광고그룹/광고 행이 그 캠페인의 매출/예약
완료/CPA/ROAS를 동일하게 공유한다** — section-4와 달리 이 부분은 진짜 캠페인별 매출이 아니라
상위 캠페인 값을 재사용한 것임에 유의한다. **section-2(Executive Summary)는 새 MCP 호출이
전혀 없다** — section-1/3/4/5 응답만 재사용해 AI가 직접 작성한다. `mtd`의 Executive
Summary와 달리 페이싱/매체별 특이사항 항목이 없고, 대신 ROAS는 목표가 없으면(현재 기본 상태)
**D-1 vs D-0**로 비교하며(mtd는 전월 동기 비교), 캠페인/광고그룹 특이사항 항목은 section-4/5의
D-1 vs D-0 변화량이 큰 캠페인·광고그룹 2~4개를 골라 원인 가설과 해결 방향까지 붙여 서술한다
(자세한 내용은 `daily-type-b-section-2-executive-summary.md` 참고).

`sections/daily-type-b/` 폴더의 파일도 다른 폴더를 import하지 않는다.

---

## 보고서 골격 (Scaffold)

각 섹션 HTML을 `{SECTIONS}` 자리에 순서대로 삽입한다.

> ⚠️ **Chart.js는 CDN `<script src>`로 절대 불러오지 않는다.** Artifact(claude.ai 아티팩트)의 CSP는
> 외부 호스트로 나가는 스크립트 요청을 전부 차단하므로, `<script src="https://cdn.jsdelivr.net/...">`
> 로 로드하면 스크립트 자체가 실행되지 않아 모든 차트가 빈 캔버스로 남는다 (실제로 발생했던 버그).
> 대신 이 스킬 폴더의 `assets/chart.umd.min.js`(Chart.js v4 UMD 빌드, MIT license, 오프라인 자산)를
> 읽어서 **그 파일 내용 전체를 `<script>...</script>` 태그 안에 그대로 붙여넣는다** (src 속성 없이,
> 인라인 텍스트로). `{CHART_JS_INLINE}` 자리표시자가 그 자리다 — 절대 CDN URL로 되돌리지 않는다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<script>
{CHART_JS_INLINE}
</script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
         background: #f8fafc; color: #1e293b; padding: 24px; }
  .report-wrap { max-width: 960px; margin: 0 auto; }
  .card { background: white; border: 1px solid #e2e8f0; border-radius: 12px;
          padding: 20px; margin-bottom: 16px; }
  .section-title { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #f1f5f9; color: #475569; font-weight: 600; padding: 8px 12px;
       text-align: left; border-bottom: 1px solid #e2e8f0; }
  td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; color: #374151; }
  @media print {
    body { background: white; padding: 0; }
    button { display: none !important; }
    .card { box-shadow: none; border: 1px solid #e2e8f0; break-inside: avoid; }
    canvas { max-width: 100%; }
    @page { margin: 15mm; size: A4; }
  }
</style>
</head>
<body>
<div class="report-wrap" id="report-content">

  <!-- 헤더: 항상 포함 -->
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
    <div>
      <h1 style="font-size:20px; font-weight:700;">{보고서_제목}</h1>
      <span style="font-size:13px; color:#64748b; margin-top:4px; display:block;">보고서 기간: {기간}</span>
    </div>
    <div style="display:flex; gap:8px;">
      <!-- PDF 저장 -->
      <button onclick="downloadReport()"
        style="padding:8px 14px; background:#3b82f6; border:none; border-radius:8px; font-size:13px; color:white; cursor:pointer; display:flex; align-items:center; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
        PDF 저장
      </button>
    </div>
  </div>

  <!-- 섹션 HTML 삽입 위치 -->
  {SECTIONS}

  <!-- 푸터: 항상 포함 -->
  <div style="text-align:center; font-size:12px; color:#94a3b8; padding:16px 0;">
    Engineered by Laighthouse AI
  </div>

</div>

<script>
/* ── 공통 유틸 ── */
function changeColor(v){ return v>0?'#16a34a':v<0?'#dc2626':'#6b7280'; }
function changeLabel(v,s='%'){ return v>0?`▲ +${v.toFixed(1)}${s}`:v<0?`▼ ${v.toFixed(1)}${s}`:'-'; }
function fmtUSD(v){ return '$'+Number(v).toLocaleString(); }

/* ── 버튼 핸들러 ── */

/* ── PDF 저장 (차트 렌더링 완료 후 인쇄) ── */
function downloadReport(){
  // Chart.js 캔버스를 정적 이미지로 교체 후 인쇄 → 원복
  const canvases = document.querySelectorAll('canvas');
  const replacements = [];

  canvases.forEach(canvas => {
    const img = document.createElement('img');
    img.src = canvas.toDataURL('image/png');
    img.style.width = canvas.style.width || canvas.offsetWidth + 'px';
    img.style.height = canvas.style.height || canvas.offsetHeight + 'px';
    img.style.maxWidth = '100%';
    canvas.parentNode.insertBefore(img, canvas);
    canvas.style.display = 'none';
    replacements.push({ canvas, img });
  });

  setTimeout(() => {
    window.print();
    // 인쇄 대화상자 닫힌 후 원복
    setTimeout(() => {
      replacements.forEach(({ canvas, img }) => {
        canvas.style.display = '';
        img.remove();
      });
    }, 1000);
  }, 300);
}

/* ── 각 섹션 차트 초기화 스크립트 삽입 위치 ── */
{SECTION_SCRIPTS}
</script>
</body></html>
```

---

## 데이터 부족 시

- 해당 섹션은 `<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>` 로 대체
- 섹션을 임의로 생략하지 않는다 — `mtd`는 7개, `executive-mtd`는 5개, `daily`는 5개 전부
  항상 렌더링한다.