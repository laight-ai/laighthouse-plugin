---
name: creative-detailed
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 소재 보고서 생성 스킬. "소재 보고서", "소재 분석 보고서", "creative report" 요청 시 사용.
  소재(개별 광고 크리에이티브) 단위로 ROAS/CTR을 분석하는 보고서 — 캠페인/매체 실적 중심이 아니라 최우수 소재 카드·소재별 라인차트 등으로 구성된다. 현재는 메타(Meta Ads)만 대상으로 한다. 대상 브랜드는 브리즘 하나뿐이다. `creative-detailed`/`creative-summary`는 다른 스킬들과 **레이아웃이 상당히
  다르다** — 톤앤매너(색상·카드 스타일·폰트)는 동일하게 유지한다.
metadata:
  version: "1.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 성과 보고서**로 렌더링하는 스킬. **대상 브랜드는
브리즘(airbridge 기반) 하나뿐이다.** 이 스킬은 **소재 보고서**(소재(개별 광고 크리에이티브) 단위로 ROAS/CTR을 분석하는 보고서 — 캠페인/매체 실적 중심이 아니라 최우수 소재 카드·소재별 라인차트 등으로 구성된다. 현재는 메타(Meta Ads)만 대상으로 한다) 전용이며,
다른 종류의 브리즘 보고서는 각각 별도 스킬로 나뉘어 있다 — `mtd-detailed`/`mtd-summary`/`daily-detailed`/`daily-summary`/`monthly-detailed`/`monthly-summary`/`creative-detailed`/`creative-summary`. 이 스킬 안에서
다른 보고서 종류를 선택하는 개념은 없다 — 호출되면 항상 소재 보고서를 렌더링한다.

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
> ⏱ **긴 대기 없이 스켈레톤을 먼저 보여준다.** 2단계(소재 데이터 호출) 응답을 받는 즉시,
> 나머지 섹션은 전부 "데이터 준비 중" placeholder(§ 데이터 부족 시 규칙과 동일한 마크업)로 채운
> 전체 골격을 1차로 Artifact에 게시한다. 이후 3단계에서 각 섹션 데이터가 준비되는 대로 같은
> Artifact 파일을 갱신(재게시)해 placeholder를 실제 값으로 교체한다 — 사용자가 빈 화면을 오래
> 기다리지 않도록 먼저 뼈대를 보여주고 채워나간다.

## 입력 파라미터

사용자 프롬프트에서 아래 항목을 파싱한다:

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 소재 보고서 |
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

1. 파라미터를 파싱한다. report_type은 `creative-detailed`로 고정되어 있다.
2. 소재 데이터를 호출한다 — `get_ad_performance_daily_table`을 **`media` 파라미터를 생략하고**
   `group_by:"ad"`로 **단 한 번만**(기준일 6일 전 ~ target_date, 7일 범위) 호출한다. `media`를
   생략하면 등록된 모든 매체(google/meta/naver/airbridge 등)의 행이 한 응답에 함께 온다 — 이
   응답에서 `media`가 정확히 `"meta"`인 행과 `"airbridge"`인 행만 걸러 쓴다(그 외 매체 행은
   이 스킬이 쓰지 않으므로 무시한다). **이 호출 1회를 section-1/3/4/5가 전부 공유해서
   재사용한다** — 매체별로 나눠 여러 번 부르지 않는다(예전에는 section별로 최대 4번까지
   나눠 불렀다). meta 행과 airbridge 행을 `campaign_name`+`asset_group`+`ad_name` 세 필드로
   조인해서 소재별 노출/클릭/광고비(메타 쪽)와 매출/예약 완료(airbridge 쪽)를 구한다 —
   Airbridge가 소재(ad) 단위까지 매출/예약을 정상적으로 귀속한다(`creative-detailed-section-1-top-creatives.md`
   참고). 소재 이미지는 `get_ad_creative_info`(메타 행의 `creative_id`/`platform_account_id`를
   그대로 전달)로 가져온 `thumbnail_image_url`을 쓴다 — 이 호출은 위 소재 데이터 호출 결과로
   ROAS/CTR 랭킹이 정해진 뒤에만 나갈 수 있으므로 순차적으로 의존한다(병렬 배치 대상 아님).
   **메타(Meta Ads)만 대상**이며, `get_target_progress_v2`나 `day_offset`은 쓰지 않는다.
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
   세부 규칙은 `creative-detailed-section-2-executive-summary.md`에 적힌 대로 따른다.
5. 아래 표의 파일을 **순서대로 전부** import해 HTML을 조합한다.
6. ⚠️ **`chart.umd.min.js`(약 208KB)를 절대 자신의 응답 텍스트로 다시 타이핑(재생성)하지
   않는다** — 이 파일을 Read해서 그 내용을 자기 출력(tool call 인자, 응답 텍스트)에 그대로
   복사해 넣으면, 그 208KB(대략 5만 토큰)를 전부 출력 토큰으로 새로 생성해야 하므로 리포트
   1건당 수십 초~수 분이 그냥 여기서 소모된다. 대신 아래 두 경로로 나눠 처리한다 — **어느
   쪽이든 모델이 chart.js 바이트를 직접 다시 쓰는 일은 없어야 한다**:
   - **파일로 저장하는 사본** (7단계의 "파일로 저장" 출력): 먼저
     `~/Downloads/laighthouse-reports/chart.umd.min.js`가 **이미 존재하는지 확인**한다. **이미
     있으면 이 단계를 완전히 건너뛴다** — 아무 도구도 쓰지 않는다. **없을 때만** 그 경로에
     `assets/chart.umd.min.js`를 생성한다 — 전용 "파일 복사" 도구가 있으면 그걸로 바이트
     그대로 복사하고, 그런 도구가 없고 일반 "파일 쓰기" 도구(내용을 문자열 인자로 받는
     것)만 있다면 그걸로라도 써서 만든다. 이 비용은 해당 출력 폴더에 리포트가 생성되는 전체
     기간 통틀어 "생애 첫 리포트 1회"에만 발생한다 — 파일이 일단 존재하면 이후 모든
     `creative-detailed`(뿐 아니라 Chart.js를 쓰는 다른 report_type도 같은 자산을 공유할 수
     있다) 리포트는 존재 확인만 하고 곧장 건너뛴다. 파일이 준비되면(새로 만들었든 이미
     있었든), 저장할 리포트 HTML의 `<head>`에는 `<script src="chart.umd.min.js"></script>`처럼
     **같은 폴더를 가리키는 상대 경로 `<script src>`**를 쓴다 — `file://`로 연 로컬 HTML이
     같은 폴더의 로컬 `.js` 파일을 상대 경로로 불러오는 것은 CDN 요청이 아니라 정상적으로
     동작한다(classic `<script src>`는 ES 모듈/`fetch`와 달리 `file://`에서 CORS 제약이 없다).
   - **채팅 내부 표시 사본** (Artifact 등 CSP로 상대/외부 스크립트 로드가 막힌 호스트): 이
     경우에만 어쩔 수 없이 인라인이 필요하다 — 이때도 모델이 직접 텍스트로 옮기지 말고, 파일
     복사·치환(diff 적용, cp, 템플릿 치환 등 텍스트 재생성이 아닌 도구)이 가능하면 그 방식을
     우선 쓴다. 그런 도구가 전혀 없는 호스트에서만 최후 수단으로 `{CHART_JS_INLINE}` 치환을
     쓴다.
7. 아래 **보고서 골격**에 섹션들을 삽입해 렌더링한다. 완성된 HTML은 아래 **두 곳에 동시에** 낸다 —
   하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Claude Code(Artifact)에서 실행 중이면 Artifact 도구로 게시(위 스켈레톤과
     같은 파일을 갱신). `mcp__visualize__show_widget`이 있는 호스트에서는 그걸 쓴다. 이 경로는
     위 6단계의 "채팅 내부 표시 사본"(인라인) 규칙을 따른다.
   - **파일로 저장**: 동일한 최종 HTML을 `~/Downloads/laighthouse-reports/브리즘_creative-detailed_
     {기준_일자}.html` 경로에 그대로 저장한다 (디렉터리가 없으면 새로 만든다). 파일명 예:
     `브리즘_creative-detailed_2026-05-15.html`. 이 경로는 위 6단계의 "파일로 저장하는 사본"
     (상대 경로 `<script src>`) 규칙을 따른다.
8. 렌더링 후 사용자에게 보내는 완료 메시지는 아래 **완료 메시지 형식**을 그대로 따른다 — 매번 다른
   문구로 즉석 요약하지 않는다. 저장된 파일 경로를 완료 메시지 마지막 줄에 덧붙인다.

---

## 병렬 호출 지침 (성능 최적화)

> ⚡ 이 스킬은 서브에이전트를 띄우지 않는다 — 오케스트레이터(본 대화)가 MCP를 직접 호출한다.
> **서로 결과에 의존하지 않는 MCP 호출은 한 메시지 안에서 동시에(병렬 tool call로) 발사한다.**
> 단, `daily-summary`(동일 플러그인, `daily-summary/CLAUDE.md` 참고)에서 실측으로 확인된 바
> 있듯 배치해도 MCP 호출 자체가 네트워크 레벨에서 진짜 동시 실행되는 것은 아니다 — 배치의
> 실제 효과는 "턴 오버헤드 제거"이지 "네트워크 동시 실행"이 아니며, 진짜 속도 개선은 **호출
> 총 개수를 줄이는 것**에서 나온다(위 2단계의 `media` 생략 통합이 그 예다).
>
> ⚠️ **이 스킬은 애초에 배치할 독립 호출이 거의 없다.** 데이터 호출이 2단계의 소재 데이터
> 호출(`get_ad_performance_daily_table`, `media` 생략 1회) 하나뿐이고, `get_ad_creative_info`는
> 그 응답으로 정해진 ROAS/CTR 랭킹 소재의 `creative_id`/`platform_account_id`가 있어야 부를 수
> 있으므로 **순차적으로 의존**한다 — 둘을 한 메시지에 동시에 낼 수 없다. 3단계의 나머지 섹션
> 호출도 이 스킬에는 존재하지 않는다(section-3/4/5는 모두 2단계 응답을 재사용하며 신규 호출이
> 없다). 억지로 "병렬 배치"를 적용할 대상 자체가 없다는 점을 명시한다 — 없는 병렬성을 있는
> 것처럼 서술하지 않는다.

> 🚫 **MCP 응답을 스크래치패드/임시 파일에 썼다가 다시 읽어오지 않는다.** 각 MCP 호출 결과는
> 이미 그 턴의 대화 컨텍스트 안에 있으므로, HTML을 조합할 때 그 값을 직접 참조해서 쓴다.
> 응답을 파일로 저장하고 나중에 다시 Read하는 왕복은 시간과 토큰만 소모할 뿐 아무 이득이
> 없다 — "데이터 가공용 임시 스크립트/노트북을 만들지 않는다"는 위 실행 방식 절대 지침과
> 같은 이유로, 중간 저장용 JSON/텍스트 파일도 만들지 않는다. 이 스킬이 실행 중 생성하는
> 파일은 최종 보고서 HTML과(6단계 조건에 해당할 때만) `chart.umd.min.js` 자산 사본뿐이다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (MCP 호출 성공·실패 여부, 섹션 개수, 데이터
출처 등 기술적 디테일은 언급하지 않는다):

```
브리즘 소재 보고서({기준_일자}) 생성 완료.
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
브리즘 소재 보고서(2026-05-15) 생성 완료.
가장 인상적인 부분: Naver Ads ROAS가 5,036.7%로 세 매체 중 가장 두드러졌습니다.
— by LaightAI
📁 C:\Users\minhyeok\Downloads\laighthouse-reports\브리즘_creative-detailed_2026-05-15.html
```

---

## 섹션 구성

**총 5개 섹션. 구성이 전부 확정됐다.**

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 최우수 소재 (ROAS / CTR, 최근 7일 기준) | `@import creative-detailed-section-1-top-creatives.md` |
| 2 | Executive Summary | `@import creative-detailed-section-2-executive-summary.md` |
| 3 | 최근 7일 일별 CTR (광고비 상위 5개 소재) | `@import creative-detailed-section-3-daily-CTR.md` |
| 4 | 최근 7일 일별 ROAS (광고비 상위 5개 소재) | `@import creative-detailed-section-4-daily-ROAS.md` |
| 5 | 최근 7일 소재 단위 누적 성과 | `@import creative-detailed-section-5-daily-creative-performance.md` |

⚠️ **파일명 표기에 유의한다** — section-3/4/5는 파일명에 `daily-detailed`가 들어있지만(`daily-CTR`,
`daily-ROAS`, `daily-creative-performance`), 이는 "매일 갱신되는 보고서"라는 맥락일 뿐
**section-5 자체의 데이터는 날짜별이 아니라 7일 누적값**이다(section-3/4만 실제로 날짜별
시계열이다). 대소문자도 정확히 지킨다(`CTR`/`ROAS`는 대문자).

section-1은 소재별(캠페인+광고그룹+광고 3단계 조합) 7일 합산 ROAS/CTR을 계산해 1·2위를 뽑는
카드다 — 날짜별 비교(D-1 vs D0 등)가 아니라 **7일 전체를 하나로 합친 누적 값** 기준이라는
점이 다른 report_type의 비교형 섹션들과 다르다.

section-2(Executive Summary)는 `mtd-detailed`/`daily-detailed`/`monthly-detailed`와 같은 **실무자용 HTML 골격**
(`<ul><li>`, `⚠` 항목만 주황색 — `executive-*` 계열의 점-색상 카드 아님)을 쓴다. **신규 MCP
호출이 전혀 없다** — section-5(소재 단위 특이사항)와 section-3/4(광고비 상위 5개 소재의
일별 CTR/ROAS 추이)만 재사용한다. 분석 항목은 ① 소재 특이사항(지표 간 역상관 주목) →
② 성과 추이 분석(상승/하락 추세, 통계적 설명 없이 서술) 순이며, **항목 2는 section-3/4가
다루는 "광고비 상위 5개 소재"로만 한정된다**(section-5의 다른 소재는 일별 데이터가 없어
추이 분석 대상이 될 수 없음). **다른 report_type의 section-2들과 달리 이 섹션은
`list_promotions`를 호출하지 않고 프로모션을 전혀 언급하지 않는다** — 소재 단위 분석이라
캠페인/매체 차원의 프로모션과 결이 다르기 때문이다.

section-3(일별 CTR)과 section-4(일별 ROAS)는 **같은 "광고비 상위 5개 소재"(7일 합산 기준)를
공유**한다 — section-3이 소재 선정을 담당하고, section-4는 그 선정 결과를 재사용한다. 매체
(meta)/airbridge 데이터 자체는 둘 다 새로 호출하지 않고, section-1이 받아둔 `media` 생략 1회
호출의 공유 응답에서 각자 필요한 행(meta 행은 section-3, airbridge 행은 section-4)만 꺼내
쓴다. 두 차트는 색상·범례 순서가 정확히 일치해야 한다(같은 소재 = 같은 색). 날짜별로 데이터가
없는 지점은 0이 아니라 `null`로 두어 차트에서 끊긴 구간으로 표시한다(`spanGaps:false`) —
추정해서 이어 그리지 않는다.

section-5(소재 단위 누적 성과 표)는 **section-1이 이미 받아둔 `media` 생략 1회 호출의 공유
응답(meta 행 + airbridge 행, `group_by:"ad"`, 최근 7일)을 그대로 재사용**한다 — 새 MCP
호출이 없다. section-1은 그 데이터에서 랭킹 1·2위만 뽑아 카드로 보여줬지만, section-5는
**모든 소재를 전부** 표로 나열한다는 점이 다르다(같은 원본 데이터의 다른 가공). 지표는
노출/클릭/CTR/광고비/매출/예약 완료/예약 완료 CPA/ROAS 8개, 7일 합산 광고비 내림차순
정렬이며, 다른 report_type의 캠페인/광고그룹 단위 표들과 동일하게 검색+페이지네이션이
실제로 작동해야 한다.

**현재까지 합의된 공통 규칙** (다른 섹션에도 적용될 전제들):
- **메타(Meta Ads)만 대상**이다 — google/naver는 다루지 않는다.
- 데이터 기간은 **기준일을 포함한 최근 7일**(daily 섹션-3과 동일한 7일 윈도우)이다. 보고서
  헤더의 `{기간}`은 이 7일 범위가 아니라 **기준일 하나만** 표기한다(`daily-detailed`와 동일한 단일
  일자 형식) — 헤더 표기와 실제 데이터 기간이 다르다는 점에 유의한다.
- 보고서 제목은 항상 "소재 보고서"로 고정한다.
- 소재별 매출/ROAS는 `get_ad_performance_daily_table`을 `media` 생략, `group_by:"ad"`로
  **1회만** 호출한 응답에서 `media`가 `"meta"`인 행과 `"airbridge"`인 행을
  `campaign_name`+`asset_group`+`ad_name` 세 필드로 조인해서 구한다 — Airbridge가 소재(ad)
  단위까지 매출/예약을 정상적으로 귀속한다는 것을 실제 API 호출로 확인했다(2026-08-03).
  매체 쪽 행에 이미 `creative_id`/`platform_account_id`가 포함되어 있다. 이 응답 1개를
  section-1/3/4/5가 전부 공유한다(예전에는 section마다 최대 4번까지 나눠 호출했다).
- 소재 이미지는 `get_ad_creative_info`(meta 파라미터에 위 `creative_id`/`platform_account_id`
  를 그대로 전달)로 받은 `thumbnail_image_url`을 `<img src="{url}"
  onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">` +
  바로 뒤에 `style="display:none;"`로 숨겨둔 "소재 미리보기 →" 링크(`<a href="{url}"
  target="_blank">`)를 짝으로 둔다. 이미지 로드 성공 시 이미지가, 실패 시(클로드 렌더링
  환경처럼 매체사가 접근을 차단하는 경우) 자동으로 링크가 보인다. `thumbnail_image_data_url`
  (base64)은 쓰지 않는다 — 다운로드 후 열람 시 사용자 네트워크가 항상 연결되어 있다고
  가정하므로 파일에 이미지를 인라인으로 심을 필요가 없다.
- 검색/페이지네이션이 있는 표(예: 소재 단위 누적 성과 표)는 다른 report_type과 동일하게
  **실제로 작동해야 한다**(아래 "공통 표기·렌더링 규칙"의 캠페인/광고그룹/광고 단위 표 원칙 참고) —
  전체 행을 JS 배열에 담고 클라이언트에서 검색·페이지 전환을 처리한다.

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
> 위 형식(단일 날짜 + "기준")으로 채운다. 보고서 헤더에는 기준일 하나만 표기하지만,
> **섹션 내부의 차트/표 데이터는 그 기준일까지의 최근 7일**을 다룬다는 점에 유의한다 —
> 헤더 표기와 실제 데이터 기간이 다르다.

> ⚠️ **Chart.js는 `https://cdn...` 같은 외부 CDN `<script src>`로는 절대 불러오지 않는다.**
> Artifact(claude.ai 아티팩트)의 CSP는 외부 호스트로 나가는 스크립트 요청을 전부 차단하므로,
> `<script src="https://cdn.jsdelivr.net/...">`로 로드하면 스크립트 자체가 실행되지 않아 모든
> 차트가 빈 캔버스로 남는다. 이 스킬 폴더의 `assets/chart.umd.min.js`(Chart.js v4 UMD 빌드,
> MIT license, 오프라인 자산)를 쓰되, **어느 경로를 쓰든 모델이 그 208KB를 직접 응답 텍스트로
> 재생성하지 않는다** (위 6단계 참고):
> - 로컬 파일로 저장하는 경우 → `assets/chart.umd.min.js`를 저장 폴더에 파일 그대로 복사해두고
>   `<script src="chart.umd.min.js"></script>`(같은 폴더 상대 경로)를 쓴다.
> - CSP 때문에 인라인이 꼭 필요한 Artifact 등에서만 → 텍스트 재생성이 아닌 도구(파일 복사/치환)로
>   `{CHART_JS_INLINE}` 자리를 채운다. 그런 도구가 전혀 없을 때만 최후 수단으로 모델이 직접
>   붙여넣는다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<!-- 로컬 파일 저장본: <script src="chart.umd.min.js"></script>
     CSP로 상대 경로 로드가 막힌 호스트(Artifact 등)에서만 아래처럼 인라인:
<script>
{CHART_JS_INLINE}
</script>
-->
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
