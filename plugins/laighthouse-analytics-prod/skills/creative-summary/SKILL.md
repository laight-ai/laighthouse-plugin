---
name: creative-summary
description: >
  브랜드 비종속 Executive 소재 보고서 생성 스킬. "임원용 소재 보고서", "executive creative report" 요청 시 사용.
  `creative-detailed`를 임원이 딥다이브 없이 훑어보도록 재구성한 소재 분석 보고서. 사용자가 말한 브랜드의
  매체·지표를 실행 시작에 디스커버리하고, 소재(개별 광고) 데이터가 있는 매체 하나를 골라 분석한다.
  `creative-detailed`/`creative-summary`는 다른 스킬들과 **레이아웃이 상당히
  다르다** — 톤앤매너(색상·카드 스타일·폰트)는 동일하게 유지한다.
metadata:
  version: "2.1.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 Executive 소재 보고서**(HTML)로 렌더링한다. 다른
종류의 보고서는 각각 별도 스킬이다 (`mtd-detailed`/`mtd-summary`/`daily-detailed`/
`daily-summary`/`monthly-detailed`/`monthly-summary`/`creative-detailed`). 이 스킬은 호출되면
항상 Executive 소재 보고서를 렌더링한다 — weekly는 지원하지 않는다(요청받으면 알맞은 스킬을
안내하거나 미지원임을 알린다).

**브랜드 비종속**: 사용자가 말한 브랜드명을 모든 MCP 호출의 `brand_name`과 제목·파일명에 그대로
쓴다. 매체 목록과 지표 키(`metric_names` → 역할별 `metric_keys`)는 실행 시작의 **디스커버리
호출**로 알아낸다 — 절차·역할 해석 규칙은 `shared/references/generic-report-pattern.md`가 단일
소스다. 이 파일과 섹션 파일에서 "cost/impression/click/revenue 키"라 하면 그 맵의 값을 뜻한다.
소재(ad) 단위 행에도 매출이 지표로 함께 들어온다(별도 조인 불필요).

**단일 매체 분석**: 소재 보고서는 매체 하나를 대상으로 한다(매체마다 소재 체계가 달라 섞지
않는다). 대상 매체(`chosen_media`)는 아래 **매체 선택** 규칙으로 실행마다 정하고, 모든 소재
단위 호출에 `filters: {"media": ["<chosen_media>"]}`를 건다. 매체명을 스킬 파일에 리터럴로
두지 않는다.

이 스킬이 쓰는 도구는 `get_ad_performance`/`get_ad_creative_info`뿐이다 —
`get_target_progress_v2`, `day_offset`은 쓰지 않는다.

공통 호출 규칙 (`get_ad_performance`):
- ℹ️ 응답은 **JSON 봉투**다: `{"source": "elt", "tenant": "<brand>", "time_grain": "day"|"month"|
  "total", "dimensions": [...], "metrics": [...], "row_count": N, "rows": [...]}`. 행의 차원
  키는 영문(`date`/`media`/`source`/`campaign_name`/`ad_group_name`/`ad_id`/`ad_name` 등),
  **지표 키는 테넌트별**이다. **응답의 `metrics` 목록이 유효한 지표 키의 유일한 진실이다** —
  키를 추측하지 않고, 디스커버리 응답에서 역할별 `metric_keys`를 한 번 정해 그 키만 쓴다.
- ⚠️ 비율 지표(ROAS/CTR류)는 요청한 grain 기준으로 서버가 이미 % 값으로 계산해 준다 —
  ×100 불필요. **행별 비율 값을 합산해 상위 기간 비율을 만들지 않는다**(날짜별 합산은
  `creative_daily_series.py`가 원자 지표 합으로 계산한다).
- ⚠️ `group_by`는 **차원명 문자열 리스트**다 — 소재 단위 호출은 전부
  `["campaign_name","ad_group_name","ad_name"]`만 쓴다.
- ⚠️ 소재 단위 호출에서 **매체 필터를 절대 생략하지 않는다** — 생략 시 전 매체 소재 행이 섞여
  응답이 폭증하고(마크다운 시절 실측 76만+자) 정확도 사고로 이어진 실제 사례가 있다. 항상
  `filters: {"media": ["<chosen_media>"]}`를 명시한다. 예전의 `media: "<값>"` 파라미터는
  서버에서 제거됐다 — 넣어도 조용히 무시되어 전 매체 행이 온다.

## 매체 선택 (실행당 1회, 디스커버리 직후)

1. **디스커버리 호출** (`generic-report-pattern.md` 2절의 변형 — `source`를 함께 받는다):
   ```json
   { "brand_name": "<brand>", "start_date": "기준일 6일 전", "end_date": "target_date",
     "time_grain": "total", "group_by": ["media", "source"], "metrics": [] }
   ```
   - 응답 `rows`는 (media, source) 쌍당 한 행. `media_list` = `media`가 `null`이 아닌 값들
     (응답 문자열 그대로, 중복 제거·순서 유지), `sources_of[media]` = 그 매체 행들의 `source`
     값 목록(매체 하나가 소스 여럿에 대응할 수 있다), `metric_names` = 봉투 `metrics`.
   - `metric_names`로 역할별 `metric_keys`(cost/impression/click/revenue; conversion은 이
     스킬에서 쓰지 않는다)를 정한다 — 3절 규칙, 미해결이면 한 번에 질문.
   - 브랜드에 `media` 차원이 없어 호출이 실패하면 `group_by: ["source"]`로 재호출하고,
     `source` 값을 `media_list`로, 이후 필터 키도 `"source"`로, `sources_of[m] = [m]`으로 쓴다.
2. **사용자가 매체를 지정했으면** 그 값을 `media_list`에서 정확 일치로 찾아 `chosen_media`로
   쓴다(대소문자만 다른 경우는 `media_list`의 표기로 맞춘다). 없으면 `media_list`를 보여주며
   한 번 되묻는다.
3. **지정하지 않았으면 소재 데이터 유무를 확인한다**: `media_list`의 각 매체에 대해
   `get_ad_performance`(`time_grain:"total"`, `group_by:["ad_name"]`, `metrics:[]`,
   `filters:{"media":[m]}`, 같은 7일)를 **한 배치**로 발사하고, `rows`가 비어있지 않은 매체만
   후보로 남긴다.
   - 후보가 정확히 1개 → 그 매체가 `chosen_media`(질문 없음).
   - 후보가 2개 이상 → 후보 목록을 보여주며 어느 매체를 분석할지 **한 번** 묻는다.
   - 후보가 0개 → 소재 단위 데이터가 있는 매체가 없다고 알리고 종료한다(보고서 생성 안 함).
4. `get_ad_creative_info`의 `source`는 `sources_of[chosen_media]`에서 귀속/분석 전용 소스
   (`airbridge`, `google_analytics_4`, `ga4`)를 제외한 값이다 — 제외 후 남은 소스마다 1회씩
   호출한다(제외 후 0개면 원래 `sources_of[chosen_media]` 전체로 호출한다). 서버가 그 `source`
   값을 거절하면(지원 소스 아님) 썸네일은 `null`로 두고 진행한다(오류 아님).

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
>   section-4/5(상위 5개 소재 exact-match 일별 시리즈)의 파싱·계산 전부. 응답이
>   `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트 — 이
>   플러그인의 PostToolUse 훅이 대용량 응답을 파일로 저장한 것) `json_files`에 경로만,
>   원본 JSON 봉투가 그대로 오면 `json`에 문자열 통째로 넘긴다(혼용 가능). 따옴표 있는 heredoc(`<<'PYEOF'`)으로
>   stdin에 파이프하고, 출력은 `> /tmp/creative_series.json`처럼 빌더가 읽을 파일로 바로
>   저장한다. 스텁이 가리키는 캡처 파일을 Read로 열어 내용을 컨텍스트로 가져오지 않는다(경로만
>   넘긴다). 응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽는 2단계도 금지다.
>   `metric_keys`(디스커버리에서 정한 역할 맵)를 함께 넘긴다.
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션 1~5
>   마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의 호출로**
>   완성한다. 모델은 소량 값 JSON만 heredoc으로 넘긴다 — 섹션별 HTML 조각 파일을 만들거나
>   chart.js를 타이핑하는 방식은 금지된 과거 패턴이다. 입력 스키마는 스크립트 상단 docstring
>   참고.
> - 시리즈 스크립트 실행과 빌더 실행은 **한 번의 Bash 호출 안에 이어서** 담을 수 있다
>   (`creative_daily_series > f && build_report`) — 왕복을 늘리지 않는다.
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다.
> - section-1의 랭킹(ROAS/CTR 1·2위)과 section-4의 상위 5개 선정은 total 응답(소재당
>   1행, 이미 합산됨)의 단순 정렬이라 스크립트가 필요 없다 — 모델이 직접 정렬한다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 (`{브랜드명} Executive 소재 보고서`) | acme Executive 소재 보고서 |
| brand_name | 사용자가 말한 브랜드명 그대로 | acme |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |
| 매체 | 선택 — 사용자가 지정한 분석 대상 매체(없으면 매체 선택 규칙으로 정한다) | Kakao |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `creative-summary` 고정.
2. **디스커버리 + 매체 선택** (위 **매체 선택** 절): 디스커버리 1회 → `media_list`/
   `sources_of`/`metric_keys` → (필요 시 소재 유무 확인 배치 1회) → `chosen_media` 확정.
3. **소재 데이터 배치 (한 메시지에 동시 발사, 총 2회)** — 소재 데이터는 두 갈래다:
   - **3-a. section-1용 (7일 합산, 랭킹)**: `get_ad_performance` ×1
     (`time_grain:"total"`, `filters:{"media":["<chosen_media>"]}`,
     `group_by:["campaign_name","ad_group_name","ad_name"]`, 기준일 6일 전 ~ target_date).
     구간 전체가 소재당 1행으로 이미 합산돼 있고 매출도 같은 행에 있어 정렬만 하면 랭킹이
     나온다. `rows`가 비어있으면 이 매체에 소재 단위 데이터가 없다는 뜻 — 사용자에게 알리고
     `media_list`에서 다른 매체를 고르게 한다(스켈레톤은 게시하되 임의로 채우지 않는다).
   - **3-b. section-3/4/5용 (일별 추이)**: `get_ad_performance` ×1
     (`time_grain:"day"`, 같은 `filters`, 같은 `group_by`, 같은 7일). 날짜별 행(`date` 키)이
     필요해서 total로 대체할 수 없다. **이 응답을 section-3/4/5가 전부 공유한다** — 섹션별로
     다시 호출하지 않는다. 대용량 응답이라 캡처 훅 스텁으로 도착하는 것이 정상이다.
4. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 3단계 응답 수신 즉시, 다음 단계 전에
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 9단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 툴호출 예산이 바닥나면 사용자는 아무것도 못
   본다 — 자매 스킬의 실제 사고 사례가 있는 필수 단계다.
5. **section-1 랭킹 + 상위 5개 선정**: 3-a 응답에서 ROAS/CTR 1·2위와 cost 키 상위 5개
   소재(표시 이름 포함)를 정한다(각 섹션 파일의 선정 규칙). 선정된 유니크 최대 4개 소재
   각각에 대해 `get_ad_creative_info`(`source:"<sources_of[chosen_media] 값>"`,
   `name_query:"<ad_name>"`)를 호출해 `image_url`을 받는다(⚠️ IP 화이트리스트 뒤라 허용되지
   않은 네트워크에서는 이미지가 안 뜰 수 있다 — onerror 폴백은 템플릿이 처리). **이 스킬의
   MCP 데이터 호출은 디스커버리(+확인 배치) + 3단계 2회 + 이 최대 4회×소스 수로 끝난다.**
6. **시리즈 계산**: `assets/creative_daily_series.py`를 3-b 응답(스텁 경로 또는 원본)과
   `top5_keys`, `metric_keys`로 1회 실행해 `> /tmp/creative_series.json`으로 저장한다 —
   section-3(overall)과 section-4/5(top5)가 이 한 파일을 공유한다 (section-3 파일의 호출 절
   참고).
7. **section-2 Executive Summary 작성** — 신규 MCP 호출 없이 다른 섹션 데이터만 재사용해 AI가
   직접 작성 (`creative-summary-section-2-executive-summary.md`의 규칙, `df_dify` 호출 금지).
8. **최종 빌드**: `assets/build_report.py`에 값 JSON을 heredoc으로 넘겨 최종 HTML을 생성한다.
   출력 경로(`out`)는 `~/Downloads/laighthouse-reports/{브랜드명}_creative-summary_{기준_일자}.html`
   (디렉터리는 빌더가 만든다).
9. 완성된 HTML을 **두 곳에 동시에** 낸다 — 하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Artifact(또는 `mcp__visualize__show_widget`)로 게시 — 4단계 스켈레톤과
     같은 대상을 갱신.
   - **파일 저장**: 8단계에서 빌더가 이미 위 경로에 저장했다 — 별도 재저장 불필요.
10. 완료 메시지는 아래 **완료 메시지 형식** 그대로 (즉석 요약 금지).

> ℹ️ 이 호스트의 Bash 기본 셸은 `sh`(dash)일 수 있다 — 프로세스 치환(`<(...)`) 같은 bash 전용
> 문법은 `bash -c '...'`로 감싸거나 쓰지 않는다.

---

## 병렬 호출 지침 (성능 최적화)

> ⚡ 서브에이전트 없이 오케스트레이터(본 대화)가 MCP를 직접 호출한다. **서로 의존성 없는 MCP
> 호출은 한 메시지 안에서 동시에(병렬 tool call로) 발사한다.** 배치의 실제 효과는 "턴 오버헤드
> 제거"다(네트워크 동시 실행 보장은 아님 — 실측 daily-summary 참고). 진짜 속도는 (a) 호출 총
> 개수 고정(디스커버리 1회 + 소재 데이터 2회 + creative_info 최대 4회, section-3/4/5의 day
> 응답 공유), (b) 캡처 훅(대용량 응답의 파일 우회), (c) asset 스크립트(재타이핑·손계산
> 제거)에서 나온다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
{브랜드명} Executive 소재 보고서({기준_일자}, {chosen_media}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
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
- **데이터 흐름 요약**: 3-a(total ×1) → section-1 랭킹 + section-4의 상위 5개 선정.
  3-b(day ×1) → `creative_daily_series.py` 1회 → section-3(overall)/4(top5 CTR)/
  5(top5 ROAS) 공유. section-2는 신규 호출 없이 재사용만.
- 섹션 데이터가 준비 안 되면 해당 `s*` 키를 빌더 입력에서 뺀다 → "데이터 준비 중" 카드로
  렌더링된다. 섹션을 임의로 생략하는 개념은 없다 — 항상 5개 전부.
