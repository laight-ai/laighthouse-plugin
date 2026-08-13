---
name: creative-summary
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 Executive 소재 보고서 생성 스킬. "임원용 소재 보고서", "executive creative report" 요청 시 사용.
  `creative-detailed`를 임원이 딥다이브 없이 훑어보도록 재구성한 소재 분석 보고서. 대상 브랜드는 브리즘 하나뿐이다. `creative-detailed`/`creative-summary`는 다른 스킬들과 **레이아웃이 상당히
  다르다** — 톤앤매너(색상·카드 스타일·폰트)는 동일하게 유지한다.
metadata:
  version: "2.0.1"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 Executive 소재 보고서**(HTML)로 렌더링한다. **대상
브랜드는 브리즘(airbridge 기반) 하나뿐이고, 소재 데이터는 메타(Meta Ads)만 대상이다.** 다른
종류의 브리즘 보고서는 각각 별도 스킬이다 (`mtd-detailed`/`mtd-summary`/`daily-detailed`/
`daily-summary`/`monthly-detailed`/`monthly-summary`/`creative-detailed`). 이 스킬은 호출되면
항상 Executive 소재 보고서를 렌더링한다 — weekly나 다른 브랜드는 지원하지 않는다(요청받으면
알맞은 스킬을 안내하거나 미지원임을 알린다).

모든 MCP 호출에 `brand_name: "breezm"`을 넘긴다 — "브리즘"은 사람용 표시명일 뿐이고, 도구
파라미터에는 **반드시 정확히 `"breezm"`**(영문 소문자)을 넣는다 (`"브리즘"`을 넣으면
`Unknown brand` 에러). 사람이 읽는 텍스트(제목·완료 메시지)에는 계속 "브리즘"을 쓴다.

이 스킬이 쓰는 도구는 `get_ad_performance_range_table`/`get_ad_performance_daily_table`/
`get_ad_creative_info`뿐이다 — naver 전용 도구, `get_target_progress_v2`, `day_offset`은 쓰지
않는다. 보고서의 모든 "매출"은 **Airbridge 매출**(`media="airbridge"` 응답의
`airbridge_revenue`)이다.

공통 호출 규칙:
- ⚠️ **어떤 호출에도 `campaign-type` 파라미터를 넣지 않는다** — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 **문자열 enum**(`total`/`media`/`campaign`/`ad-set`/`ad`)이다 — boolean 금지.
  이 스킬은 전부 `"ad"`만 쓴다.
- ⚠️ `group_by:"ad"` 호출에서 **`media`를 절대 생략하지 않는다** — 생략 시 응답이 실측 76만+자로
  폭증해(단일 `media="meta"`도 13만자대) 정확도 사고로 이어진 실제 사례가 있다(`CLAUDE.md` 참고).
  `media="meta"`/`media="airbridge"` 각각 명시해서 호출한다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답은 이미 정제가 끝난 최종 데이터다 — 그대로 스크립트에 넘기고, 값을 의심·보정·
> 재계산·추정하지 않는다.** 예외는 각 섹션 파일에 명시된 표기 변환뿐이다.
> 데이터가 비거나 갭이 있어도 채우거나 추정하지 않는다.
>
> 🚫 **응답이 크다고 느껴져도 선택지는 정확히 둘뿐이다**: (1) 원본을 가공 없이 전부 asset
> 스크립트에 넘기거나, (2) 정말 처리 불가능하면 그 섹션을 "데이터 준비 중"으로 표시한다
> (빌더 입력에서 해당 `s*` 키를 빼면 된다). **다른 섹션·다른 날짜 값의 재사용, 비슷해 보이는
> 숫자 생성, 부분 전사 후 추정("이 정도만 훑어보고 나머지는 추정")은 — 그 대체 숫자가 진짜
> 쿼리 결과라도 — 전부 금지다.** 이미 정상적으로 받은 응답은 그 세분화 단위 그대로 쓴다
> ("받았지만 크다"며 다른 것으로 바꾸는 경우는 존재하지 않는다). 응답을 못 받았을 때만 (2)로
> 간다. 정확한 계산 없는 순위·합계·TOP-N을 보고서에 넣는 것보다 "데이터 준비 중"이 항상 낫다.

## 실행 방식 절대 지침

> 이 스킬의 계산·렌더링은 전부 **미리 검증된 asset 스크립트**가 한다 — 모델이 실행 중
> `.py`/`.js` 스크립트 파일을 새로 만들거나, HTML을 직접 타이핑하거나, 소재별 합산·조인을
> 프로즈로 손계산하는 것은 전부 금지다.
>
> - **`assets/creative_daily_series.py`** — section-3(전체 소재 날짜별 합산 CTR/ROAS)과
>   section-4/5(상위 5개 소재 exact-match 일별 시리즈)의 파싱·조인·계산 전부. 응답이
>   `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트 — 이
>   플러그인의 PostToolUse 훅이 대용량 응답을 파일로 저장한 것) `meta_markdown_files`/
>   `airbridge_markdown_files`에 경로만, 원본 마크다운이 그대로 오면 `meta_markdown`/
>   `airbridge_markdown`에 문자열 통째로 넘긴다(혼용 가능). 따옴표 있는 heredoc(`<<'PYEOF'`)으로
>   stdin에 파이프하고, 출력은 `> /tmp/creative_series.json`처럼 빌더가 읽을 파일로 바로
>   저장한다. 스텁이 가리키는 캡처 파일을 Read로 열어 내용을 컨텍스트로 가져오지 않는다(경로만
>   넘긴다). 응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽는 2단계도 금지다.
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션 1~5
>   마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의 호출로**
>   완성한다. 모델은 소량 값 JSON만 heredoc으로 넘긴다 — 섹션별 HTML 조각 파일을 만들거나
>   chart.js를 타이핑하는 방식은 금지된 과거 패턴이다. 입력 스키마는 스크립트 상단 docstring
>   참고.
> - 시리즈 스크립트 실행과 빌더 실행은 **한 번의 Bash 호출 안에 이어서** 담을 수 있다
>   (`creative_daily_series > f && build_report`) — 왕복을 늘리지 않는다.
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다.
> - section-1의 랭킹(ROAS/CTR 1·2위)과 section-4의 상위 5개 선정은 range_table 응답(소재당
>   1행, 이미 합산됨)의 단순 정렬이라 스크립트가 필요 없다 — 모델이 직접 정렬한다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 Executive 소재 보고서 |
| brand_name | 항상 `breezm` | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `creative-summary` 고정.
2. **1차 배치 (한 메시지에 동시 발사, 총 4회)** — 소재 데이터는 두 갈래다:
   - **2-a. section-1용 (7일 합산, 랭킹)**: `get_ad_performance_range_table` ×2
     (`media="meta"`/`media="airbridge"`, `group_by:"ad"`, 기준일 6일 전 ~ target_date).
     구간 전체가 소재당 1행으로 이미 합산돼 있어 정렬만 하면 랭킹이 나온다.
   - **2-b. section-3/4/5용 (일별 추이)**: `get_ad_performance_daily_table` ×2
     (`media="meta"`/`media="airbridge"`, `group_by:"ad"`, 같은 7일). 날짜별 행이 필요해서
     range_table로 대체할 수 없다. **이 2회 응답을 section-3/4/5가 전부 공유한다** — 섹션별로
     다시 호출하지 않는다. 대용량 응답이라 캡처 훅 스텁으로 도착하는 것이 정상이다.
3. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 2단계 응답 수신 즉시, 다음 단계 전에
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 8단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 툴호출 예산이 바닥나면 사용자는 아무것도 못
   본다 — 자매 스킬의 실제 사고 사례가 있는 필수 단계다.
4. **section-1 랭킹 + 상위 5개 선정**: 2-a 응답에서 ROAS/CTR 1·2위와 광고비 상위 5개 소재
   (표시 이름 포함)를 정한다(각 섹션 파일의 조인·선정 규칙). 선정된 최대 4개 소재의
   `platform_account_id`/`creative_id`로 `get_ad_creative_info` ×1을 호출해 썸네일 URL을
   받는다. **이 스킬의 MCP 데이터 호출은 2단계 4회 + 이 1회, 총 5회로 끝난다.**
5. **시리즈 계산**: `assets/creative_daily_series.py`를 2-b 응답(스텁 경로 또는 원본)과
   `top5_keys`로 1회 실행해 `> /tmp/creative_series.json`으로 저장한다 — section-3(overall)과
   section-4/5(top5)가 이 한 파일을 공유한다 (section-3 파일의 호출 절 참고).
6. **section-2 Executive Summary 작성** — 신규 MCP 호출 없이 다른 섹션 데이터만 재사용해 AI가
   직접 작성 (`creative-summary-section-2-executive-summary.md`의 규칙, `df_dify` 호출 금지).
7. **최종 빌드**: `assets/build_report.py`에 값 JSON을 heredoc으로 넘겨 최종 HTML을 생성한다.
   출력 경로(`out`)는 `~/Downloads/laighthouse-reports/브리즘_creative-summary_{기준_일자}.html`
   (디렉터리는 빌더가 만든다).
8. 완성된 HTML을 **두 곳에 동시에** 낸다 — 하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Artifact(또는 `mcp__visualize__show_widget`)로 게시 — 3단계 스켈레톤과
     같은 대상을 갱신.
   - **파일 저장**: 7단계에서 빌더가 이미 위 경로에 저장했다 — 별도 재저장 불필요.
9. 완료 메시지는 아래 **완료 메시지 형식** 그대로 (즉석 요약 금지).

> ℹ️ 이 호스트의 Bash 기본 셸은 `sh`(dash)일 수 있다 — 프로세스 치환(`<(...)`) 같은 bash 전용
> 문법은 `bash -c '...'`로 감싸거나 쓰지 않는다.

---

## 병렬 호출 지침 (성능 최적화)

> ⚡ 서브에이전트 없이 오케스트레이터(본 대화)가 MCP를 직접 호출한다. **서로 의존성 없는 MCP
> 호출은 한 메시지 안에서 동시에(병렬 tool call로) 발사한다.** 배치의 실제 효과는 "턴 오버헤드
> 제거"다(네트워크 동시 실행 보장은 아님 — 실측 daily-summary 참고). 진짜 속도는 (a) 호출 총
> 개수 고정(소재 데이터 4회 + creative_info 1회 = 5회, section-3/4/5의 daily 응답 공유), (b)
> 캡처 훅(대용량 응답의 파일 우회), (c) asset 스크립트(재타이핑·손계산 제거)에서 나온다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
브리즘 Executive 소재 보고서({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 html 파일 경로}
```

- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 하나만 (여러 개 나열 금지).

---

## 섹션 구성

**총 5개 섹션, 구성 고정.** 각 파일은 MCP 호출/재사용 명세와 빌더 입력(`s1`~`s5`) 매핑 규칙을
담는다 — HTML/Script는 전부 `assets/report-template.html`에 있다.

| 순서 | 섹션 | 파일 | 빌더 키 |
|-----|------|------|--------|
| 1 | 최우수 소재 (ROAS / CTR, 최근 7일) | `creative-summary-section-1-top-creatives.md` | `s1` |
| 2 | Executive Summary | `creative-summary-section-2-executive-summary.md` | `s2` |
| 3 | 최근 7일 전체 소재 CTR 및 ROAS | `creative-summary-section-3-daily-creative-total-performance.md` | `s3` |
| 4 | 최근 7일 일별 CTR (광고비 상위 5개 소재) | `creative-summary-section-4-daily-CTR.md` | `s4` |
| 5 | 최근 7일 일별 ROAS (광고비 상위 5개 소재) | `creative-summary-section-5-daily-ROAS.md` | `s5` |

- section-1/4/5는 `creative-detailed`의 section-1/3/4와 동일 내용이다(4/5는 번호만 하나씩
  밀림). section-3은 이 스킬 고유의 신규 섹션, section-2는 임원용 불릿 카드 골격(점 색상
  구분)을 쓴다. `creative-detailed`의 소재 전체 나열 표에 대응하는 섹션은 없다.
- **데이터 흐름 요약**: 2-a(range_table ×2) → section-1 랭킹 + section-4의 상위 5개 선정.
  2-b(daily_table ×2) → `creative_daily_series.py` 1회 → section-3(overall)/4(top5 CTR)/
  5(top5 ROAS) 공유. section-2는 신규 호출 없이 재사용만.
- 섹션 데이터가 준비 안 되면 해당 `s*` 키를 빌더 입력에서 뺀다 → "데이터 준비 중" 카드로
  렌더링된다. 섹션을 임의로 생략하는 개념은 없다 — 항상 5개 전부.
