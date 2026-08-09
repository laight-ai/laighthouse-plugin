---
name: daily-summary
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 Executive 데일리 보고서 생성 스킬. "임원용 데일리 보고서", "executive daily" 요청 시 사용.
  `daily-detailed`를 임원이 딥다이브 없이 훑어보도록 더 간결하게 재구성한 데일리 보고서. 대상 브랜드는 브리즘 하나뿐이다.
metadata:
  version: "1.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 성과 보고서**로 렌더링하는 스킬. **대상 브랜드는
브리즘(airbridge 기반) 하나뿐이다.** 이 스킬은 **Executive 데일리 보고서**(`daily-detailed`를 임원이 딥다이브 없이 훑어보도록 더 간결하게 재구성한 데일리 보고서) 전용이며,
다른 종류의 브리즘 보고서는 각각 별도 스킬로 나뉘어 있다 — `mtd-detailed`/`mtd-summary`/`daily-detailed`/`daily-summary`/`monthly-detailed`/`monthly-summary`/`creative-detailed`/`creative-summary`. 이 스킬 안에서
다른 보고서 종류를 선택하는 개념은 없다 — 호출되면 항상 Executive 데일리 보고서를 렌더링한다.

모든 MCP 호출에 `brand_name: "breezm"`을 넘기고, naver 전용 도구는 일절 쓰지 않는다. generic
도구(`get_ad_performance_daily_table`/`get_ad_performance_monthly_table`)와
`get_target_progress_v2`만 쓰며, 보고서의 모든 "매출"은 **Airbridge 매출**
(`media="airbridge"` 응답의 `airbridge_revenue`)이다. 광고 채널은 airbridge 응답의 `channel`
값이 `Google Ads`/`Meta Ads`/`Naver Ads`인 행으로 고정 정의한다 — 첫 airbridge 응답에서 실제
`channel` 값들을 확인하고, 이 상수와 다르면 조용히 0을 반환하지 말고 보고서에 불일치를 명시한다.
⚠️ **어떤 호출에도 `campaign-type` 파라미터를 넣지 않는다** — 넣으면 airbridge 행이 조용히
누락된다.

`weekly` 보고서나 브리즘 외 다른 브랜드(naver 기반 브랜드, Google/Meta 기반 브랜드)는 이
플러그인이 지원하지 않는다. 사용자가 다른 종류의 보고서나 weekly 보고서를 요청하면, 알맞은
스킬(`mtd-detailed`/`mtd-summary`/`daily-detailed`/`daily-summary`/`monthly-detailed`/`monthly-summary`/`creative-detailed`/`creative-summary` 중 하나)을 안내하거나 아직 지원하지 않는다고 알린다.

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
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 Executive 데일리 보고서 |
| brand_name | MCP 호출용 브랜드명 — **항상 `breezm`**(`get_brand_list` 응답과 정확히 일치하는 값). 사람이 브랜드를 부를 때 쓰는 "브리즘"과는 다른 값이니 혼동하지 않는다 (아래 경고 참고) | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

> ⚠️ **"브리즘"과 `brand_name`을 혼동하지 않는다.** "브리즘"은 사람이 대화·보고서 제목에서
> 브랜드를 부르는 **표시명**일 뿐이다. 어떤 MCP 도구를 호출하든 실제 파라미터에 넣는
> `brand_name` 값은 **반드시 정확히 `"breezm"`**(영문 소문자, `get_brand_list` 응답 기준)
> 이어야 한다 — `"브리즘"`을 그대로 넣으면 `Unknown brand '브리즘'` 에러로 호출 자체가
> 실패한다. 사용자가 "브리즘", "breezm", "브리즘(breezm)" 등 어떤 표현으로 브랜드를 지칭하든
> **전부 같은 브랜드를 가리키는 것으로 인식**하고, 실제 도구 호출 시에는 항상 `"breezm"`으로
> 정규화해서 넣는다. 보고서 제목·완료 메시지 등 사람이 읽는 텍스트에는 계속 "브리즘"을 쓴다.

이 보고서의 섹션 구성은 고정되어 있으며, 사용자가 섹션을 골라 지정하는 개념이 없다 — 아래
표에 있는 파일을 항상 전부 렌더링한다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `daily-summary`로 고정되어 있다.
2. target/achievement 수치를 호출한다 — `mcp__laighthouse__get_target_progress_v2`를
   `{ "brand_name": "breezm", "month": "YYYY-MM", "media": "...", "as_of_date": "target_date" }`로
   **google/meta/naver 세 번**(`media`만 바꿔) 호출한다
   (`daily-summary-section-1-target-achievement.md` 참고). 세 매체 모두
   `"No {media} budget/target available for {month}."` 메시지가 돌아오거나 `cost`/`revenue`
   행의 `target`이 0이면(브리즘은 현재 `revenue` 목표가 세 매체 다 0이다) 해당 목표 필드는
   N/A로 표시하고, 대체 값은 `get_ad_performance_daily_table`이 아니라
   **`get_ad_performance_monthly_table`(`start_month`=`end_month`=당월,
   `day_offset`=target_date.day)**로 가져온다 — 날짜별 행을 직접 합산하는 것보다 훨씬 빠르다
   (섹션 파일의 대체 규칙 참고). 매출 실적(`기간 매출`/`광고 매출`)은 목표 유무와 무관하게
   **항상** 이 방식(`media="airbridge"`, `group_by:"media"`, `day_offset`)으로 가져온다 —
   `get_target_progress_v2`의 `revenue` 행 `actual`은 naver에서 0을 반환하는 경우가 있어
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
4. **section-2가 Executive Summary다.** `executive_summary` 텍스트는 `df_dify` MCP를 호출하지
   않고, AI가 다른 섹션 응답을 재사용해 직접 작성한다. 어떤 섹션 응답을 근거로 쓰는지,
   프로모션/이벤트 정보를 위해 `mcp__laighthouse__list_promotions`를 추가로 호출하는지 등
   세부 규칙은 `daily-summary-section-2-executive-summary.md`에 적힌 대로 따른다.
5. 아래 표의 파일을 **순서대로 전부** import해 HTML을 조합한다.
6. 이 스킬 폴더의 `assets/chart.umd.min.js` 파일을 읽어 그 내용 전체를 `{CHART_JS_INLINE}` 자리에
   그대로 삽입한다 (CDN `<script src>` 절대 사용 금지 — 아래 보고서 골격의 경고 참고).
7. 아래 **보고서 골격**에 섹션들을 삽입해 렌더링한다. 완성된 HTML은 아래 **두 곳에 동시에** 낸다 —
   하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Claude Code(Artifact)에서 실행 중이면 Artifact 도구로 게시(위 스켈레톤과
     같은 파일을 갱신). `mcp__visualize__show_widget`이 있는 호스트에서는 그걸 쓴다.
   - **파일로 저장**: 동일한 최종 HTML을 `~/Downloads/laighthouse-reports/브리즘_daily-summary_
     {기준_일자}.html` 경로에 그대로 저장한다 (디렉터리가 없으면 새로 만든다). 파일명 예:
     `브리즘_daily-summary_2026-05-15.html`.
8. 렌더링 후 사용자에게 보내는 완료 메시지는 아래 **완료 메시지 형식**을 그대로 따른다 — 매번 다른
   문구로 즉석 요약하지 않는다. 저장된 파일 경로를 완료 메시지 마지막 줄에 덧붙인다.

---

## 병렬 호출 지침 (성능 최적화)

> ⚡ 이 스킬은 `render-report-docx`처럼 서브에이전트를 띄우지 않는다 — 오케스트레이터(본 대화)가
> MCP를 직접 호출한다. 대신 **서로 결과에 의존하지 않는 MCP 호출은 반드시 한 메시지 안에서
> 동시에(병렬 tool call로) 발사한다.** 하나씩 순차 호출하면 호출마다 브랜드 권한 확인 왕복이
> 누적되어 보고서 생성이 불필요하게 느려진다 — "2단계 먼저, 3단계 나중"이라는 실행 순서상의
> 서술은 데이터 의존성이 아니라 설명 편의상 나눈 순서일 뿐이다.

- **2단계**의 `get_target_progress_v2` 3회 호출(media=google/meta/naver)은 서로 독립적이다 — 3개를
  한 메시지 안에서 동시에 발사한다. 세 응답이 모두 도착한 뒤에만 "모든 매체 target이 0/N/A인지"를
  판단해 `get_ad_performance_monthly_table` 대체 호출 여부를 정한다 — 이 대체 호출은 3개 응답에
  의존하는 유일한 조건부 호출이라 앞의 3개와 동시에 낼 수 없다.
- **3단계**에서 section-2/3/4/5가 필요로 하는 나머지 모든 호출(각 섹션 파일이 지정하는
  `get_ad_performance_daily_table`/`get_ad_performance_monthly_table`)과 `list_promotions`
  **1회**(아래 참고)는 서로 다른 섹션 간에도 결과 의존성이 없다 — 위 조건부 대체 호출을 제외한
  전부를 **한 메시지에서 동시에** 발사한다.
- 실제로는 2단계의 3개 호출과 3단계의 모든 호출도 서로 독립적이므로, 가능하면 2·3단계를 합쳐
  **한 메시지에서 최대한 많은 호출을 동시에** 낸다. 예외는 오직 "3개 target 응답을 보고서야 필요
  여부가 정해지는 월간 대체 호출" 하나뿐이다.
- ⚠️ **`list_promotions`는 보고서 전체에서 딱 1회만 호출한다.** section-2/3/4가 예전에는
  조금씩 다른 룩백 기간(7일/6일/6일 전)으로 각자 호출했으나, section-2의 **7일 룩백**
  (`start_date`=기준일 7일 전, `end_date`=target_date — 세 섹션 중 가장 넓은 범위)으로
  통일했다. section-3/4는 이제 이 응답을 그대로 재사용하며 별도 호출을 하지 않는다 (각
  섹션 파일의 "재사용" 절 참고) — 응답 한 번으로 세 섹션 모두 충당되므로 위 "동시 발사" 대상
  목록에도 `list_promotions`는 한 번만 포함시킨다.

> 🚫 **MCP 응답을 스크래치패드/임시 파일에 썼다가 다시 읽어오지 않는다.** 각 MCP 호출 결과는
> 이미 그 턴의 대화 컨텍스트 안에 있으므로, HTML을 조합할 때 그 값을 직접 참조해서 쓴다.
> 응답을 파일로 저장하고 나중에 다시 Read하는 왕복은 시간과 토큰만 소모할 뿐 아무 이득이
> 없다 — "데이터 가공용 임시 스크립트/노트북을 만들지 않는다"는 위 원칙과 같은 이유로, 중간
> 저장용 JSON/텍스트 파일도 만들지 않는다. 이 스킬이 실행 중 생성하는 파일은 최종 보고서
> HTML 하나뿐이다(위 실행 방식 절대 지침과 동일).

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (MCP 호출 성공·실패 여부, 섹션 개수, 데이터
출처 등 기술적 디테일은 언급하지 않는다):

```
브리즘 Executive 데일리 보고서({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 html 파일 경로}
```

- `{기준_일자}`: 사용자가 지정한 기준 일자 (예: 2026-05-15)
- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 한 가지만 골라 한 문장으로 (예: "Naver
  Ads ROAS가 5,036.7%로 가장 두드러졌습니다"). 여러 개 나열하지 않는다.
- `{저장된 html 파일 경로}`: 7단계에서 저장한 `.html` 파일의 전체 경로.

예시:
```
브리즘 Executive 데일리 보고서(2026-05-15) 생성 완료.
가장 인상적인 부분: Naver Ads ROAS가 5,036.7%로 세 매체 중 가장 두드러졌습니다.
— by LaightAI
📁 C:\Users\minhyeok\Downloads\laighthouse-reports\브리즘_daily-summary_2026-05-15.html
```

---

## 섹션 구성

**총 5개 섹션. 구성이 전부 확정됐다.**

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 목표 달성 현황 | `@import daily-summary-section-1-target-achievement.md` |
| 2 | Executive Summary | `@import daily-summary-section-2-executive-summary.md` |
| 3 | 최근 7일 성과 | `@import daily-summary-section-3-daily-performance-7days.md` |
| 4 | 일일 매출 현황 (최근 7일) | `@import daily-summary-section-4-daily-revenue-7days.md` |
| 5 | 매체별 성과 (D-1 vs D-0) | `@import daily-summary-section-5-channel-performance.md` |

section-3(최근 7일 성과)은 `daily-detailed`의 section-3과 **완전히 동일한 데이터·차트 로직**이다 —
광고비/매출/ROAS 혼합 차트(막대+라인), 프로모션 브래킷 오버레이(밴드 폭 보정 포함), tooltip
₩/% 표기까지 그대로다. **주의**: `daily-summary`는 section-3(최근 7일 성과, 상세 혼합
차트)과 section-4(일일 매출 현황, 간결한 매출 라인 차트)를 **둘 다** 갖고 있다 — `daily-detailed`처럼
하나만 쓰는 게 아니라 두 관점을 나란히 보여주는 구성이다.

section-1(목표 달성 현황)은 `mtd-detailed`/`daily-detailed`의 section-1과 **완전히 동일한 데이터·계산
로직**이다 — "월초~기준일" 당월 MTD 목표 대비 진행 상황이며, no-budget/부분 목표(cost만 있고
revenue는 N/A) 처리 규칙도 동일하다. 이 섹션은 아직 공유할 다른 섹션(예: mtd의 Channel별
예산 소진 현황)이 없어 자체적으로만 쓰인다.

section-2(Executive Summary)는 `daily-detailed`의 section-2(Executive Summary)와 목적은 비슷하지만
근거 데이터가 다르다 — `daily-detailed`의 section-2는 section-1/3/4/5(캠페인·광고그룹 단위 포함)를
재사용하는 반면, `daily-summary`의 section-2는 **section-4(일일 매출 현황, 오거닉/광고
매출 비중)와 section-5(매체별 성과, D-1 vs D-0)만** 재사용한다 — section-1은 있지만 시점이
"당월 MTD"라 "전일 대비" 분석과 맞지 않아 직접 재사용하지 않으며, 브리즘은 현재 매출 목표가
N/A라 목표 대비 평가 자체가 불가능하다. `list_promotions`를 이 섹션에서 별도로 1회 호출하되,
`mtd-summary`(30일 룩백)보다 짧은 **7일 룩백**을 쓴다 (하루 단위 보고서이므로). 분석 항목도
"전월 대비"가 아니라 **"전일 대비"**(D-1 vs D-0)로 전부 바뀌었다는 점에 유의한다 (자세한
내용은 `daily-summary-section-2-executive-summary.md` 참고).

section-4는 `daily-detailed`의 section-3(최근 7일 성과, 광고비/매출/ROAS 혼합 차트)보다 더 간결한 —
전체 매출/광고 매출 라인만 보여주는 — 버전이다(`mtd-detailed`의 월별 광고 성과 ↔ `mtd-summary`의
매출 추이 관계와 동일). `daily-detailed`의 section-4(캠페인 성과, D-1 vs D-0)와 달리, 이 섹션은 **기준일
을 포함한 최근 7일**(daily 섹션-3과 동일한 7일 윈도우, MTD 아님)을 다룬다. `get_target_progress_v2`
나 `day_offset`을 쓰지 않는다. 프로모션 오버레이는 `mtd-detailed-section-4-daily-revenue.md`와
동일한 브래킷 방식이되, **밴드 폭 보정을 쓰지 않는다** — 이 섹션은 daily 섹션-3(막대 차트)이
아니라 mtd 섹션-4(라인 차트)를 기반으로 하므로 `xScale.getPixelForValue(idx)`를 보정 없이
그대로 쓴다.

section-5는 `daily-detailed`의 section-4(캠페인 성과, D-1 vs D-0)와 비교 방식(D-1 vs D-0, 변화량 표기,
색상 규칙)은 같지만 **비교 단위가 캠페인이 아니라 매체**다 — Naver Ads/Google Ads/Meta Ads/
Organic/Others 5개 행 고정, 지표는 광고비/매출/예약 완료/ROAS 4개다. (`daily-detailed`의 section-4는
여기에 CTR·예약 완료 CPA까지 더한 6개 지표를 쓰지만, 이 섹션(executive-daily의
section-5)은 여전히 4개만 쓴다 — 매체 5개 고정 표라 CTR/예약 완료 CPA를 추가하지 않았다.) D-0
매출 내림차순 정렬이다. 이 섹션의 네 지표는 전부 "증가=긍정(빨강)"이라 `daily-detailed` section-4의
예약 완료 CPA(감소가 긍정)와 다르다는 점, 헤더가 "지표명(위, colspan=2) + 날짜(아래)" 구조로
section-4/daily 섹션들과 반대라는 점, 항목 수가 5개로 고정이라 페이지네이션/검색창이
없다는 점에 유의한다 (자세한 내용은
`daily-summary-section-5-channel-performance.md` 참고).

이 스킬의 섹션 파일은 전부 브리즘(airbridge 기반) 기준으로 작성되어 있고, 다른 스킬의 파일을 import하지 않는다.

---

## 공통 표기·렌더링 규칙

공통 표기 규칙: 비율/ROAS는 % 스케일로 소수점 1자리, 금액은 천 단위 콤마 원화. 분모가 0인
비율(ROAS/CPA/달성률 등)은 임의로 0을 넣지 말고 N/A로 표시한다. **차트 Y축이 원화 금액을
나타내는 경우 `₩` 접두어 + 천 단위 콤마로 표시한다**(예: `₩15,000,000`) — 만원/억원 등
축약 단위로 바꾸지 않는다 (표/카드의 금액 표기와 동일한 원칙).

**캠페인/광고그룹/광고 단위(행 수가 가변적인) 표에 검색창이나 페이지네이션을 넣을 때는
반드시 실제로 작동해야 한다** — "검색창·페이지 버튼은 장식만 달아두고 실제로는 첫 10개만
HTML에 박아넣는" 방식은 금지한다(`mtd-detailed-section-7`/`daily-detailed-section-4`/
`daily-detailed-section-5`/`monthly-detailed-section-5` 전부 이 원칙을 따른다). 이 보고서는 서버
없이 한 번에 생성되는 정적 HTML이므로, "버튼 클릭/검색어 입력 → 서버에 다시 물어본다"는
방식은 애초에 성립하지 않는다. **올바른 패턴**: 필터·정렬을 마친 전체 행을 각각 완성된
`<tr>...</tr>` HTML 문자열 + 검색용 텍스트(식별 필드들을 소문자로 이어붙인 문자열)로 만들어
JS 배열에 전부 담고, 검색 input의 `oninput`과 페이지 버튼의 `onclick`이 그 배열을 걸러/잘라
`tbody`를 다시 그리는 실제 로직을 갖게 한다(위 4개 파일의 Script 참고 — 재사용 가능한
템플릿이다). 매체 5개 고정 표(`executive-*`의 채널 비교 섹션 등 행 수가 고정된 표)는 검색/
페이지네이션 자체가 필요 없다.

**매체/캠페인/광고그룹/광고 등 식별자 이름은 report_type에 관계없이 절대 잘려서 표시되면
안 된다** — 이건 특정 파일에만 적용되는 규칙이 아니라 **모든 report_type에 공통으로
적용되는 원칙**이다. `-webkit-line-clamp`, `text-overflow:ellipsis` 등 "말줄임표로
자르는" 방식은 절대 쓰지 않는다 — `daily-detailed`/`monthly-detailed`에서 이미 확정된 "안 잘림" 원칙은
`creative-detailed-section-5` 등 다른 모든 report_type에도 동일하게 적용한다. 대신 다음 3가지
조합을 표준으로 쓴다:
1. 식별자 열에 **넉넉한 고정 너비**를 준다(대략 매체 90px, 캠페인 260px, 광고그룹/광고 각
   200px — 실제로 검증된 값이다. 이보다 좁게 잡지 않는다).
2. `white-space:normal; overflow-wrap:break-word;`로 하이픈·언더스코어·공백 등 자연스러운
   경계에서 줄바꿈한다. **`word-break:break-word`는 쓰지 않는다** — 아무 글자에서나 강제로
   끊어서(예: "u/p/p/e/r") 이름이 세로로 길게 쪼개지는 문제가 생길 수 있다.
3. `<table>`에 **`table-layout:fixed`**를 준다 — `auto`(기본값)에서는 `width`가 힌트에
   불과해서, `nowrap`인 지표 열들이 공간을 다 차지하고 식별 열만 계속 짜부라지는 문제가 생길 수 있다(이를 막기 위해 지표 열에도 명시적 `width`를 준다).

**"최대 두 줄"은 목표일 뿐 강제 규칙이 아니다** — 이름이 길어서 두 줄을 넘어가면 억지로
줄이지 말고 3줄 이상으로 자연스럽게 넘치도록 둔다. "잘리지 않는 것"이 "줄 수를 맞추는 것"
보다 항상 우선한다. 새 report_type이나 새 섹션을 만들 때 캠페인/광고그룹/광고 같은 식별자
열이 있으면, 이 원칙을 처음부터 적용한다 — 나중에 문제가 발견되고서야 고치지 않는다.

**"지표명(위, colspan=2) + 날짜/월(아래)" 2행 헤더 구조를 쓸 때는 반드시 상하 대칭 패딩을
준다** — `mtd-detailed-section-7`을 제외한 `daily-detailed`/`monthly-detailed`의 section-4/5, `daily-summary`/
`monthly-summary`/`mtd-summary`의 매체 비교 섹션 전부에서 지표명 헤더("광고비" 등)가
아래로 치우쳐 보일 수 있다. 지표명 행에 `padding-bottom:2px`만 주고 위쪽은 기본 패딩(더
큼)을 쓰는 식으로 **상하 패딩을 비대칭으로 두면**, 지표명 행과 그 아래 날짜/월 표기 행을
시각적으로 더 가깝게 붙이려는 의도와 달리 셀 높이에 남는 여유 공간이 없으면
`vertical-align:middle`을 줘도 비대칭 패딩을 상쇄하지 못해 텍스트가 한쪽으로 치우쳐 보인다. **올바른 패턴**: 지표명 행과
날짜/월 표기 행 모두 `padding-top:8px; padding-bottom:8px;`처럼 상하를 동일하게 주고,
`vertical-align:middle`도 명시적으로 추가한다(대칭 패딩만으로 이미 중앙에 오지만, 명시해서
의도를 분명히 한다). 두 행을 시각적으로 더 가깝게 붙이고 싶어도 비대칭 패딩으로 붙이지
않는다 — "정확한 상하 중앙 정렬"이 "두 행 사이 간격을 좁히는 것"보다 항상 우선한다. 새로
이런 2행 헤더 구조를 만들 때는 처음부터 대칭 패딩으로 시작한다.

**지표 열(D-1/D-0, M-1/M0 등 값+변화량이 함께 들어가는 열)도 너무 좁게 고정폭을 주면 표가
겹쳐 보인다** — `table-layout:fixed`를 쓸 때 지표 열 폭을 90px로 줬다가, "₩8,984,291" +
"(▲ +5.4%)" 같은 실제 값이 그보다 넓어서 `white-space:nowrap` 텍스트가 옆 셀로 흘러넘쳐
글자가 서로 포개져 보일 수 있다(겹쳐서 읽기 어려워짐). **지표 열 폭은 최소 150px로 잡는다**
— 90px, 115px 둘 다 검증 결과 부족했다.

⚠️ **`table-layout:fixed`를 쓰는 `<table>`에는 `width:auto`도 반드시 같이 명시한다.**
SKILL.md 공통 스타일시트에 `table { width: 100%; ... }`가
전역으로 적용되는데, 개별 `<table>`에서 `width`를 따로 지정하지 않으면 이 100%가 그대로
상속된다. **`table-layout:fixed`와 `width:100%`를 함께 쓰면, 지정한 각 열의 픽셀 값이
절대값이 아니라 "100%를 나눠 갖는 비율"로 취급된다** — 그래서 지표 열 폭을 90px→115px→
150px로 계속 늘려도 카드 폭(100%)에 맞춰 매번 다시 비율로 쪼그라들어서 실제로는 하나도
넓어지지 않고, 표가 계속 겹쳐 보이는 문제가 반복될 수 있다. `width:auto`를 명시하면 테이블이 선언한 열 폭들의 **합만큼 실제로
넓어지고**, 카드보다 넓어진 부분은 `overflow-x:auto` 컨테이너가 가로 스크롤로 처리한다 —
이게 원래 의도한 동작이다. `table-layout:fixed`를 쓰는 표를 새로 만들 때는 `width:auto`를
처음부터 같이 명시한다 — 폭이 안 넓어지는 게 확인되고서야 나중에 추가하지 않는다.
`table-layout:fixed`를 안 쓴 표(예: 원래 `daily-detailed-section-4`)도 지표 열 개수가
많으면(6개 지표×2 = 12열 이상) 브라우저가 임의로 열을 압축하다 같은 증상이 날 수 있으므로,
지표 열이 많은 표는 처음부터 `table-layout:fixed`+명시적 폭+`width:auto`를 함께 준다.

**프로모션 브래킷 오버레이의 `start_idx`/`end_idx`는 "labels 배열에서 해당하는 인덱스를
찾는다"처럼 애매하게 지시하지 않는다** — `daily-detailed-section-3`/`daily-summary-
section-3`/`daily-summary-section-4`/`mtd-detailed-section-4-daily-revenue`
4개 파일에서 이렇게 모호하게만 적어두면, 실제 생성 시 프로모션 기간이 차트의 날짜 범위와
안 맞게(예: 7일 전체를 덮어야 할 프로모션이 중간 며칠만 덮은 것처럼) 그려질 수 있다.
**`labels` 배열은 항상 연속된 달력 날짜**이므로, 인덱스는
"찾기"가 아니라 **날짜 차이를 직접 계산**해서 구해야 한다:
```
raw_start_idx = (date_begin − labels[0]의 날짜).일수차
raw_end_idx   = (date_end   − labels[0]의 날짜).일수차
start_idx = max(0, raw_start_idx)
end_idx   = min(labels.length-1, raw_end_idx)
```
`raw_end_idx < 0`이거나 `raw_start_idx > labels.length-1`이면 그 프로모션은 차트 범위와
전혀 안 겹치므로 제외한다. Script 쪽에도 `Math.max(0, Math.min(n-1, ...))`로 한 번 더
방어적으로 clamp해서, 데이터 가공 단계가 실수로 clamp를 빼먹어도 브래킷이 차트 밖으로
삐져나가지 않게 한다. 새로 프로모션 오버레이가 있는 차트를 만들 때는 이 명시적 공식을
처음부터 쓴다.

---

## 보고서 골격 (Scaffold)

각 섹션 HTML을 `{SECTIONS}` 자리에 순서대로 삽입한다.

> ℹ️ **헤더의 `{기간}` 표기 규칙**: 날짜 범위가 아니라 **기준일 하나만 표기**한다 —
> `{YYYY}년 {M}월 {D}일 기준` (예: `2026년 7월 25일 기준`). "보고서 기준일:"처럼 라벨
> 자체를 바꾸지 않는다 — 라벨은 항상 "보고서 기간:"으로 고정하고, 그 뒤에 오는 내용만
> 위 형식(단일 날짜 + "기준")으로 채운다.

> ⚠️ **Chart.js는 CDN `<script src>`로 절대 불러오지 않는다.** Artifact(claude.ai 아티팩트)의 CSP는
> 외부 호스트로 나가는 스크립트 요청을 전부 차단하므로, `<script src="https://cdn.jsdelivr.net/...">`
> 로 로드하면 스크립트 자체가 실행되지 않아 모든 차트가 빈 캔버스로 남는다.
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
- 섹션을 임의로 생략하지 않는다 — 이 스킬은 5개 섹션 전부 항상 렌더링한다.
