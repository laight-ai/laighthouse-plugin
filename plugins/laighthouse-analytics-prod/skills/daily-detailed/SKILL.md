---
name: daily-detailed
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 데일리 보고서 생성 스킬. "데일리 보고서", "일간 보고서", "daily 보고서" 요청 시 사용.
  최근 7일 등 짧은 기간 단위로 매일 확인하는 실무자용 일자별 성과 보고서. 대상 브랜드는 브리즘 하나뿐이다.
metadata:
  version: "2.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 데일리 성과 보고서**(HTML)로 렌더링한다. **대상
브랜드는 브리즘(airbridge 기반) 하나뿐이다.** 다른 종류의 브리즘 보고서는 각각 별도 스킬이다
(`mtd-detailed`/`mtd-summary`/`daily-summary`/`monthly-detailed`/`monthly-summary`/
`creative-detailed`/`creative-summary`). 이 스킬은 호출되면 항상 데일리 보고서를 렌더링한다 —
weekly나 다른 브랜드는 지원하지 않는다(요청받으면 알맞은 스킬을 안내하거나 미지원임을 알린다).

모든 MCP 호출에 `brand_name: "breezm"`을 넘긴다 — "브리즘"은 사람용 표시명일 뿐이고, 도구
파라미터에는 **반드시 정확히 `"breezm"`**(영문 소문자)을 넣는다 (`"브리즘"`을 넣으면
`Unknown brand` 에러). 사람이 읽는 텍스트(제목·완료 메시지)에는 계속 "브리즘"을 쓴다.

generic 도구(`get_ad_performance`)와 `get_target_progress_v2`, `list_promotions`만 쓴다.
보고서의 모든 "매출"은 **Airbridge 귀속 매출**로, `get_ad_performance` 응답 행의 지표
`매출_AB`다(예약은 `예약완료_AB`). 매체 구분은 행의 `media` 차원 값(`Google`/`Meta`/`Naver`)
으로 한다 — 예전의 airbridge/`channel` 행 개념은 ELT 이관으로 사라졌고, 매출/예약이 각 행에
지표로 함께 들어온다(별도 조인 불필요).

공통 호출 규칙 (`get_ad_performance`):
- ℹ️ 응답은 **JSON 봉투**다: `{"source": "elt", "tenant": "breezm", "time_grain": "day"|"month"|
  "total", "dimensions": [...], "metrics": [...], "row_count": N, "rows": [...]}`. 행의 차원
  키는 영문(`date`(day grain)/`month`(month grain, "YYYY-MM")/`media`/`campaign_id`/
  `campaign_name`/`ad_group_id`/`ad_group_name`/`ad_id`/`ad_name` 등), **지표 키는 테넌트별**
  이다 — 브리즘은 한국어 지표명 `광고비`(비용)/`노출`/`클릭`/`매출_AB`/`예약완료_AB`와 서버
  계산 비율 지표 `ROAS_AB`/`CPM`/`CTR`/`CVR`/`CPA`/`CPA_AB`를 쓴다. **응답의 `metrics` 목록이
  유효한 지표 키의 유일한 진실이다** — 키를 추측하지 않는다.
- ⚠️ 비율 지표(`ROAS_AB`/`CTR` 등)는 요청한 grain 기준으로 서버가 이미 % 값으로 계산해 준다 —
  ×100 불필요. **행별 비율 값을 합산해 상위 기간/상위 그룹 비율을 만들지 않는다**(필요하면
  원자 지표 합으로 다시 계산).
- ⚠️ `group_by`는 **차원명 문자열 리스트**다 (예: `["media"]`,
  `["media","campaign_id","campaign_name"]`) — 예전의 문자열 enum(`total`/`campaign` 등)이
  아니다. 생략하면 총계만 온다(day/month grain이면 `date`/`month` 키 포함). `metrics` 생략 시
  테넌트 전체 지표가 온다.
- `media` 필터 값은 `"Google"`/`"Meta"`/`"Naver"` (대소문자 변형·한국어 표기는 서버가 흡수).
- ⚠️ `get_target_progress_v2`의 ROAS류 수치는 비율값(0.87)이므로 ×100 해서 %로 쓴다 —
  이 도구 응답만 여전히 markdown 표다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답은 이미 정제가 끝난 최종 데이터다 — 그대로 스크립트에 넘기고, 값을 의심·보정·
> 재계산·추정하지 않는다.** 예외는 각 섹션 파일에 명시된 표기 변환뿐이다(ROAS ×100 등).
> 데이터가 비거나 갭이 있어도 채우거나 추정하지 않는다.
>
> 🚫 **응답이 크다고 느껴져도 선택지는 정확히 둘뿐이다**: (1) 원본을 가공 없이 전부 asset
> 스크립트에 넘기거나, (2) 정말 처리 불가능하면 그 섹션을 "데이터 준비 중"으로 표시한다
> (빌더 입력에서 해당 `s*` 키를 빼면 된다). **다른 섹션·다른 날짜 값의 재사용, 비슷해 보이는
> 숫자 생성, 부분 전사 후 추정은 — 그 대체 숫자가 진짜 쿼리 결과라도 — 전부 금지다.** 이미
> 정상적으로 받은 응답은 그 세분화 단위 그대로 쓴다("받았지만 크다"며 다른 것으로 바꾸는
> 경우는 존재하지 않는다). 응답을 못 받았을 때만 (2)로 간다.

## 실행 방식 절대 지침

> 이 스킬의 계산·렌더링은 전부 **미리 검증된 asset 스크립트**가 한다 — 모델이 실행 중
> `.py`/`.js` 스크립트 파일을 새로 만들거나, HTML을 직접 타이핑하거나, 캠페인/광고 행을
> 프로즈로 손계산하는 것은 전부 금지다.
>
> - **`assets/dxd_table_rows.py`** — section-4/5의 조인·파생지표·변화율·필터·정렬·`<tr>` 생성.
>   응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트 —
>   이 플러그인의 PostToolUse 훅이 대용량 응답을 파일로 저장한 것) `json_files`에 경로만,
>   원본 JSON 봉투가 그대로 오면 `json`에 문자열 통째로 넘긴다(혼용 가능). 따옴표 있는
>   heredoc(`<<'PYEOF'`)으로 stdin에 파이프하고, 출력은 `> /tmp/s4_rows.json`처럼 빌더가 읽을
>   파일로 바로 저장한다. 스텁이 가리키는 캡처 파일을 Read로 열어 내용을 컨텍스트로 가져오지
>   않는다(경로만 넘긴다).
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션 1~5
>   마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의 호출로**
>   완성한다. 모델은 소량 값 JSON만 heredoc으로 넘긴다 — 섹션별 HTML 조각 파일(part1.html 등)을
>   만들거나 chart.js를 타이핑하는 방식은 금지된 과거 패턴이다. 입력 스키마는 스크립트 상단
>   docstring 참고.
> - dxd 실행과 빌더 실행은 **한 번의 Bash 호출 안에 이어서** 담을 수 있다
>   (`dxd s4 > f1 && dxd s5 > f2 && build_report`) — 왕복을 늘리지 않는다.
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 데일리 보고서 |
| brand_name | 항상 `breezm` | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`, D-0) | 2026-08-10 |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `daily-detailed` 고정.
2. **1차 배치 (한 메시지에 동시 발사)**: `get_target_progress_v2` ×3(google/meta/naver) +
   `get_ad_performance` ×1(당월 1일~target_date, `time_grain:"month"`, `group_by:["media"]`,
   media 생략) — section-1용 (`daily-detailed-section-1-target-achievement.md` 참고).
3. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 2단계 응답 수신 즉시, 다음 단계 전에
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 8단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 툴호출 예산이 바닥나면 사용자는 아무것도 못
   본다 — 실제 사고 사례가 있는 필수 단계다.
4. **2차 배치 (한 메시지에 동시 발사)**: section-3(`time_grain:"day"`, 7일, `group_by` 생략
   1회 + `list_promotions` 1회), section-4(`time_grain:"day"`, 이틀,
   `group_by:["media","campaign_id","campaign_name"]`, media 생략 1회),
   section-5(`time_grain:"day"`, 이틀, `group_by:["media","campaign_name","ad_group_name",
   "ad_name"]`, media=Google/Meta/Naver 각각 3회). 각 섹션 파일의 호출 명세를 그대로 따른다.
5. **계산**: section-1 값 판정(섹션 파일의 계산 규칙), section-3 배열 3개 산출,
   section-4/5는 `dxd_table_rows.py` 실행(`> /tmp/s4_rows.json`, `> /tmp/s5_rows.json`).
6. **section-2 Executive Summary 작성** — 신규 MCP 호출 없이 다른 섹션 응답만 재사용해 AI가
   직접 작성 (`daily-detailed-section-2-executive-summary.md`의 규칙).
7. **최종 빌드**: `assets/build_report.py`에 값 JSON을 heredoc으로 넘겨 최종 HTML을 생성한다.
   출력 경로(`out`)는 `~/Downloads/laighthouse-reports/브리즘_daily-detailed_{기준_일자}.html`
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
> 개수 축소(section-1/3/4의 media 생략 통합 — section-5만 고카디널리티라 매체별 유지), (b)
> 캡처 훅(대용량 응답의 파일 우회), (c) asset 스크립트(재타이핑·손계산 제거)에서 나온다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
브리즘 데일리 보고서({기준_일자}) 생성 완료.
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
| 1 | 목표 달성 현황 (당월 MTD) | `daily-detailed-section-1-target-achievement.md` | `s1` |
| 2 | Executive Summary | `daily-detailed-section-2-executive-summary.md` | `s2` |
| 3 | 최근 7일 성과 (차트) | `daily-detailed-section-3-daily-performance-7days.md` | `s3` |
| 4 | 캠페인 성과 (D-1 vs D-0) | `daily-detailed-section-4-campaign-performance.md` | `s4` |
| 5 | 광고그룹 및 광고 성과 (D-1 vs D-0) | `daily-detailed-section-5-ad-performance.md` | `s5` |

- section-1은 당월 MTD 기준(월 단위 예산), section-3은 7일, section-4/5는 D-1~D0 이틀 —
  기간·group_by가 서로 달라 응답을 섹션 간 공유하지 않는다 (section-2만 신규 호출 없이 재사용).
- 섹션 데이터가 준비 안 되면 해당 `s*` 키를 빌더 입력에서 뺀다 → "데이터 준비 중" 카드로
  렌더링된다. 섹션을 임의로 생략하는 개념은 없다 — 항상 5개 전부.
