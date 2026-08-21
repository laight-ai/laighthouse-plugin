---
name: creative-detailed
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 소재 보고서 생성 스킬. "소재 보고서", "소재 분석 보고서", "creative report" 요청 시 사용.
  소재(개별 광고 크리에이티브) 단위로 ROAS/CTR을 분석하는 보고서 — 캠페인/매체 실적 중심이
  아니라 최우수 소재 카드·소재별 라인차트 등으로 구성된다. 현재는 메타(Meta Ads)만 대상으로
  한다. 대상 브랜드는 브리즘 하나뿐이다.
metadata:
  version: "2.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.
> **목표 소요 시간은 3분이다.**


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 소재 성과 보고서**(HTML)로 렌더링한다. **대상
브랜드는 브리즘(airbridge 기반) 하나뿐이고, 매체는 메타(Meta Ads)만 대상이다** —
google/naver는 다루지 않는다. 다른 종류의 브리즘 보고서는 각각 별도 스킬이다
(`mtd-detailed`/`mtd-summary`/`daily-detailed`/`daily-summary`/`monthly-detailed`/
`monthly-summary`/`creative-summary`). 이 스킬은 호출되면 항상 소재 보고서를 렌더링한다 —
weekly나 다른 브랜드는 지원하지 않는다(요청받으면 알맞은 스킬을 안내하거나 미지원임을 알린다).

모든 MCP 호출에 `brand_name: "breezm"`을 넘긴다 — "브리즘"은 사람용 표시명일 뿐이고, 도구
파라미터에는 **반드시 정확히 `"breezm"`**(영문 소문자)을 넣는다 (`"브리즘"`을 넣으면
`Unknown brand` 에러). 사람이 읽는 텍스트(제목·완료 메시지)에는 계속 "브리즘"을 쓴다.

generic 도구(`get_ad_performance`)와 `get_ad_creative_info`만 쓴다 —
`get_target_progress_v2`, `list_promotions`, `day_offset`은 쓰지 않는다. 보고서의 모든
"매출"은 **Airbridge 귀속 매출**로, `get_ad_performance` 응답 행의 지표 `매출_AB`다(예약은
`예약완료_AB`) — 소재(ad) 단위 행에도 매출/예약이 지표로 함께 들어온다(별도 조인 불필요).

공통 호출 규칙 (`get_ad_performance`):
- ℹ️ 응답은 **JSON 봉투**다: `{"source": "elt", "tenant": "breezm", "time_grain": "day"|"month"|
  "total", "dimensions": [...], "metrics": [...], "row_count": N, "rows": [...]}`. 행의 차원
  키는 영문(`date`/`media`/`campaign_name`/`ad_group_name`/`ad_id`/`ad_name` 등), **지표 키는
  테넌트별**이다 — 브리즘은 한국어 지표명 `광고비`/`노출`/`클릭`/`매출_AB`/`예약완료_AB`와
  서버 계산 비율 지표 `ROAS_AB`/`CPM`/`CTR`/`CVR`/`CPA`/`CPA_AB`를 쓴다. **응답의 `metrics`
  목록이 유효한 지표 키의 유일한 진실이다** — 키를 추측하지 않는다.
- ⚠️ 비율 지표(`ROAS_AB`/`CTR`)는 요청한 grain 기준으로 서버가 이미 % 값으로 계산해 준다 —
  ×100 불필요. **행별 비율 값을 합산해 상위 기간 비율을 만들지 않는다**(날짜별 합산이
  필요하면 원자 지표 합으로 다시 계산 — `creative_daily_series.py`가 그렇게 한다).
- ⚠️ `group_by`는 **차원명 문자열 리스트**다 — 이 스킬의 데이터 호출은 전부
  `["campaign_name","ad_group_name","ad_name"]`(소재 단위)다.
- ⚠️ 소재 단위 호출에서 **`media`를 생략하지 않는다** — 생략 시 응답이 수 배로 커져 근사치
  사고의 직접 원인이 됐다(마크다운 시절 실측 76만 자+). 이 스킬은 항상 `media="Meta"`다.

### time_grain 사용 구분 (이 스킬의 핵심 배선)

- **`time_grain:"total"`** — 소재당 **7일 전체를 서버가 이미 합산한 한 행**을 반환. "7일 누적
  값"만 필요한 **section-1/5**가 쓴다(1회). 응답이 소재 개수만큼으로 작고, 비율 지표
  (`CTR`/`ROAS_AB`)도 7일 합산 기준으로 이미 계산돼 있다.
- **`time_grain:"day"`** — 날짜별 원본 행(`date` 키). **일별 트렌드 차트**가 필요한
  **section-3/4**만 쓴다(1회). total 응답은 날짜 차원이 이미 합쳐져 있어 이 용도로 쓸 수 없다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답은 이미 정제가 끝난 최종 데이터다 — 그대로 쓰고, 값을 의심·보정·재계산·추정하지
> 않는다.** 예외는 각 섹션 파일에 명시된 표기 변환뿐이다(CTR/ROAS ×100 판정, section-4의
> 0-채움 등). 데이터가 비거나 갭이 있어도 채우거나 추정하지 않는다.
>
> 🚫 **응답이 크다고 느껴져도 선택지는 정확히 둘뿐이다**: (1) 원본을 가공 없이 전부 처리
> (즉석 Bash exact-match 포함)하거나, (2) 정말 처리 불가능하면 그 섹션을 "데이터 준비 중"으로
> 표시한다(빌더 입력에서 해당 `s*` 키를 빼면 된다). **다른 섹션·다른 날짜 값의 재사용, 비슷해
> 보이는 숫자 생성, 부분 훑기 후 추정은 — 그 대체 숫자가 진짜 쿼리 결과라도 — 전부 금지다.**
> 이미 정상적으로 받은 응답은 그 세분화 단위 그대로 쓴다("받았지만 크다"며 다른 것으로 바꾸는
> 경우는 존재하지 않는다). 응답을 못 받았을 때만 (2)로 간다.

## 실행 방식 절대 지침

> 이 스킬의 렌더링은 전부 **미리 검증된 asset 스크립트**가 한다 — 모델이 실행 중
> `.py`/`.js` 스크립트 파일을 새로 만들거나, HTML을 직접 타이핑하거나, 섹션 조각 파일
> (`section3.html`, `meta.tsv` 등)을 만들었다 다시 읽는 것은 전부 금지다.
>
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션
>   1~5 마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의
>   호출로** 완성한다. section-5의 CTR/CPA/ROAS 계산·포맷·정렬·`<tr>` 생성과 section-1의
>   썸네일 카드 HTML도 빌더가 만든다. 모델은 소량 값 JSON만 따옴표 있는 heredoc
>   (`<<'PYEOF'`)으로 stdin에 넘긴다 — 입력 스키마는 스크립트 상단 docstring 참고.
> - **total 응답(section-1/5)은 이미 작다(소재당 한 행) — 받은 그 자리에서 바로
>   정렬 결과를 낸다.** Bash도 스크립트도 스크래치 파일(`meta.tsv` 등)도
>   쓰지 않고, 각 행을 자연어로 하나씩 서술하지도 않는다 — 실제 실행(2026-07-08)에서 이
>   작은 응답을 3중 중복 처리(자연어 서술 → 파일 재입력 → heredoc 스크립트)해 수 분을
>   소모한 사고가 있었다. "응답이 이미 작으면 바로 결과"가 규칙이다.
> - **day grain 응답(section-3/4)은 5개 키 × 7일 exact-match만 남는 bounded 작업**이다
>   (소재 선정은 range 응답 정렬로 이미 끝남). 응답이
>   `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트 — 이
>   플러그인의 PostToolUse 훅이 대용량 응답을 파일로 저장한 것) 그 파일을 입력으로 즉석 Bash
>   1회(`grep/awk ... <경로>`)로 5개 키 행만 추출한다 — 스텁이 가리키는 파일을 Read로 통째로
>   열거나 원본을 재타이핑하지 않는다. 원본이 그대로 오면 컨텍스트에서 바로 걸러낸다.
>   exact-match는 필수 절차이며 **전부 정확하게** 수행한다 — 일부만 훑고 추정하는 것은
>   금지("정확한 계산 없는 순위/합계는 넣지 말고 차라리 데이터 준비 중").
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다. 이 스킬이 만드는 파일은 빌더가 저장하는 최종 보고서
>   HTML(과 s5 rows를 파일로 넘길 때의 rows JSON 1개)뿐이다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 소재 보고서 |
| brand_name | 항상 `breezm` | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다. 보고서 헤더는 기준일
하나만 표기하지만(빌더가 처리), 데이터는 기준일 포함 최근 7일이다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `creative-detailed` 고정.
2. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 어떤 MCP 호출보다도 먼저(이 스킬은
   먼저 도착하는 요약 호출이 없어 정적 값만으로 바로 만들 수 있다)
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 8단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 예산이 바닥나면 사용자는 아무것도 못 본다 —
   실제 사고 사례가 있는 필수 단계다.
3. **데이터 배치 (한 메시지에 동시 발사, 총 2회)**: `get_ad_performance` ×1
   (`time_grain:"total"`, `media:"Meta"` — section-1/5용) + `get_ad_performance` ×1
   (`time_grain:"day"`, `media:"Meta"` — section-3/4용). 둘 다
   `group_by:["campaign_name","ad_group_name","ad_name"]`, 기준일 6일 전 ~ target_date.
   각 섹션 파일의 호출 명세를 그대로 따른다. (day 호출은 total 응답에 의존하지 않는다 —
   "5개 키로 거른다"는 가공 시점에만 필요하다.)
4. **계산**: total 응답 정렬 → section-1 랭킹과 section-5 rows(매출/예약이 행에 이미 있어
   조인 불필요), `광고비` 내림차순 → 상위 5개 소재 키·표시 이름, day 응답에서 5개 키
   exact-match → section-3 CTR 시리즈(`null` 규칙)와 section-4 ROAS 시리즈(0-채움 규칙).
   섹션 데이터가 준비되는 대로 골격의 placeholder를 교체·재게시해도 된다.
5. **`get_ad_creative_info` (순차 의존, 최대 4회)**: 4단계에서 확정된 ROAS/CTR 1·2위 소재
   (유니크 최대 4개) 각각에 대해 `{ "brand_name": "breezm", "source": "meta_ads",
   "name_query": "<ad_name>" }`로 호출 → 응답 `items[]`에서 이름이 정확히 일치하는 항목의
   `image_url` (section-1 참고. 3단계 배치와 함께 낼 수 없다 — 랭킹이 먼저 필요.
   ⚠️ `image_url`은 IP 화이트리스트 뒤에 있어 허용되지 않은 네트워크에서는 이미지가 안 뜰 수
   있다 — 렌더링 실패 시 onerror 폴백은 템플릿이 처리한다).
6. **section-2 Executive Summary 작성** — 신규 MCP 호출 없이 다른 섹션 결과만 재사용해 AI가
   직접 작성 (`creative-detailed-section-2-executive-summary.md`의 규칙).
7. **최종 빌드**: `assets/build_report.py`에 값 JSON을 heredoc으로 넘겨 최종 HTML을 생성한다.
   출력 경로(`out`)는 `~/Downloads/laighthouse-reports/브리즘_creative-detailed_{기준_일자}.html`
   (디렉터리는 빌더가 만든다).
8. 완성된 HTML을 **두 곳에 동시에** 낸다 — 하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Artifact(또는 `mcp__visualize__show_widget`)로 게시 — 2단계 스켈레톤과
     같은 대상을 갱신.
   - **파일 저장**: 7단계에서 빌더가 이미 위 경로에 저장했다 — 별도 재저장 불필요.
9. 완료 메시지는 아래 **완료 메시지 형식** 그대로 (즉석 요약 금지).

> ℹ️ 이 호스트의 Bash 기본 셸은 `sh`(dash)일 수 있다 — 프로세스 치환(`<(...)`) 같은 bash 전용
> 문법은 `bash -c '...'`로 감싸거나 쓰지 않는다.

---

## 병렬 호출 지침 (성능 최적화)

> ⚡ 서브에이전트 없이 오케스트레이터(본 대화)가 MCP를 직접 호출한다. **서로 의존성 없는 MCP
> 호출은 한 메시지 안에서 동시에(병렬 tool call로) 발사한다.** 이 스킬에서 배치 대상은 3단계의
> 두 호출뿐이고, `get_ad_creative_info`는 랭킹 확정 후에만 가능한 순차 의존이다 — 없는
> 병렬성을 부풀리지 않는다. 배치의 실제 효과는 "턴 오버헤드 제거"다(네트워크 동시 실행 보장
> 아님). 진짜 속도는 (a) 호출 공유(section-5가 total 응답을, section-4가 day
> 응답을 재사용 — 신규 호출 0), (b) 캡처 훅(대용량 day 응답의 파일 우회), (c) asset
> 스크립트(재타이핑·손계산·HTML 타이핑 제거)에서 나온다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
브리즘 소재 보고서({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 html 파일 경로}
```

- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 하나만 (여러 개 나열 금지).

---

## 섹션 구성

**총 5개 섹션, 구성 고정.** 각 파일은 MCP 호출 명세와 빌더 입력(`s1`~`s5`) 매핑 규칙을 담는다
— HTML/Script는 전부 `assets/report-template.html`에 있다.

| 순서 | 섹션 | 파일 | 빌더 키 |
|-----|------|------|--------|
| 1 | 최우수 소재 (ROAS / CTR, 최근 7일) | `creative-detailed-section-1-top-creatives.md` | `s1` |
| 2 | Executive Summary | `creative-detailed-section-2-executive-summary.md` | `s2` |
| 3 | 최근 7일 일별 CTR (광고비 상위 5개 소재) | `creative-detailed-section-3-daily-CTR.md` | `s3` |
| 4 | 최근 7일 일별 ROAS (광고비 상위 5개 소재) | `creative-detailed-section-4-daily-ROAS.md` | `s4` |
| 5 | 최근 7일 소재 단위 누적 성과 | `creative-detailed-section-5-daily-creative-performance.md` | `s5` |

- ⚠️ 파일명 표기 주의 — section-3/4/5의 "daily"는 "매일 갱신되는 보고서"라는 맥락일 뿐이고,
  section-5의 데이터는 날짜별이 아니라 7일 누적값이다(section-3/4만 실제 시계열).
  `CTR`/`ROAS` 대소문자도 정확히.
- section-1/5는 같은 total 응답 공유(랭킹 카드 vs 전체 표), section-3/4는 같은 day 응답과
  5개 소재 키·색상·범례 순서를 공유한다(빌더가 `s3`의 `names`/`labels`를 `s4`에도 주입).
  section-2만 신규 호출 없이 전부 재사용. **이 섹션은 프로모션을 언급하지 않는다**
  (`list_promotions` 호출 없음 — 다른 report_type의 section-2들과 다른 점).
- 섹션 데이터가 준비 안 되면 해당 `s*` 키를 빌더 입력에서 뺀다 → "데이터 준비 중" 카드로
  렌더링된다. 섹션을 임의로 생략하는 개념은 없다 — 항상 5개 전부.
