---
name: monthly-detailed
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 월간 보고서 생성 스킬. "월간 보고서", "monthly 보고서" 요청 시 사용.
  실무자용 월간 보고서. 대상 브랜드는 브리즘 하나뿐이다.
metadata:
  version: "2.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 월간 성과 보고서**(HTML)로 렌더링한다. **대상
브랜드는 브리즘(airbridge 기반) 하나뿐이다.** 다른 종류의 브리즘 보고서는 각각 별도 스킬이다
(`mtd-detailed`/`mtd-summary`/`daily-detailed`/`daily-summary`/`monthly-summary`/
`creative-detailed`/`creative-summary`). 이 스킬은 호출되면 항상 월간 보고서를 렌더링한다 —
weekly나 다른 브랜드는 지원하지 않는다(요청받으면 알맞은 스킬을 안내하거나 미지원임을 알린다).

모든 MCP 호출에 `brand_name: "breezm"`을 넘긴다 — "브리즘"은 사람용 표시명일 뿐이고, 도구
파라미터에는 **반드시 정확히 `"breezm"`**(영문 소문자)을 넣는다 (`"브리즘"`을 넣으면
`Unknown brand` 에러). 사람이 읽는 텍스트(제목·완료 메시지)에는 계속 "브리즘"을 쓴다.

generic 도구(`get_ad_performance_daily_table`/`get_ad_performance_monthly_table`)와
`get_target_progress_v2`, `list_promotions`만 쓴다 — naver 전용 도구는 일절 쓰지 않는다.
보고서의 모든 "매출"은 **Airbridge 매출**(`media="airbridge"` 응답의 `airbridge_revenue`)이고,
광고 채널은 airbridge 응답 `channel` ∈ {`Google Ads`, `Meta Ads`, `Naver Ads`} 행으로 고정이다
— 첫 airbridge 응답에서 실제 `channel` 값을 확인하고, 다르면 조용히 0을 만들지 말고 보고서에
불일치를 명시한다.

공통 호출 규칙:
- ⚠️ **어떤 호출에도 `campaign-type` 파라미터를 넣지 않는다** — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 **문자열 enum**(`total`/`media`/`campaign`/`ad-set`/`ad`)이다 — boolean 금지.
- ⚠️ `get_target_progress_v2`의 ROAS류 수치는 비율값(0.87)이므로 ×100 해서 %로 쓴다.
- ⚠️ monthly_table 호출에는 항상 `day_offset: target_date.day`를 넣는다 — 범위 내 모든 월에
  균일하게 적용되어 "매달 기준일과 같은 일자까지"의 동일 기준 비교가 된다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답은 이미 정제가 끝난 최종 데이터다 — 그대로 스크립트에 넘기고, 값을 의심·보정·
> 재계산·추정하지 않는다.** 예외는 각 섹션 파일에 명시된 표기 변환뿐이다(ROAS ×100 등).
> 데이터가 비거나 갭이 있어도 채우거나 추정하지 않는다.
>
> 🚫 **응답이 크다고 느껴져도 선택지는 정확히 둘뿐이다**: (1) 원본을 가공 없이 전부 asset
> 스크립트에 넘기거나, (2) 정말 처리 불가능하면 그 섹션을 "데이터 준비 중"으로 표시한다
> (빌더 입력에서 해당 `s*` 키를 빼면 된다). **다른 섹션·다른 월 값의 재사용, 비슷해 보이는
> 숫자 생성, 부분 전사 후 추정은 — 그 대체 숫자가 진짜 쿼리 결과라도 — 전부 금지다.** 이미
> 정상적으로 받은 응답은 그 세분화 단위 그대로 쓴다("받았지만 크다"며 다른 것으로 바꾸는
> 경우는 존재하지 않는다). 응답을 못 받았을 때만 (2)로 간다.

## 실행 방식 절대 지침

> 이 스킬의 계산·렌더링은 전부 **미리 검증된 asset 스크립트**가 한다 — 모델이 실행 중
> `.py`/`.js` 스크립트 파일을 새로 만들거나, HTML을 직접 타이핑하거나, 캠페인/매체 행을
> 프로즈로 손계산하는 것은 전부 금지다.
>
> - **`assets/monthly_campaign_rows.py`** — section-5의 조인·파생지표·변화율·`(-)` 규칙·
>   ₩300,000 필터·정렬·`<tr>` 생성. 응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>`
>   스텁으로 오면(캡처 훅 동작 호스트) `markdown_files`에 경로만, 원본 마크다운이 그대로 오면
>   `markdown`에 문자열 통째로 넘긴다(혼용 가능). 따옴표 있는 heredoc(`<<'PYEOF'`)으로 stdin에
>   파이프하고, 출력은 `> /tmp/s5_rows.json`처럼 빌더가 읽을 파일로 바로 저장한다. 스텁이
>   가리키는 캡처 파일을 Read로 열어 내용을 컨텍스트로 가져오지 않는다(경로만 넘긴다).
>   응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽어 실행하는 2단계도 금지다.
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션 1~5
>   마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의 호출로**
>   완성한다. section-4의 파생지표(CTR/CPA/ROAS)·변화량·색상·정렬도 빌더가 계산한다 — 모델은
>   소량 값 JSON만 heredoc으로 넘긴다. 섹션별 HTML 조각 파일(section4.html 등)을 만들거나
>   chart.js를 타이핑하는 방식은 금지된 과거 패턴이다. 입력 스키마는 스크립트 상단 docstring 참고.
> - rows 스크립트 실행과 빌더 실행은 **한 번의 Bash 호출 안에 이어서** 담을 수 있다
>   (`monthly_campaign_rows > f1 && build_report`) — 왕복을 늘리지 않는다.
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 월간 보고서 |
| brand_name | 항상 `breezm` | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`, M0 기준일) | 2026-07-31 |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다. M0 = target_date가 속한
달, M-1 = 그 전달.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `monthly-detailed` 고정.
2. **1차 배치 (한 메시지에 동시 발사)**: `get_target_progress_v2` ×3(google/meta/naver) +
   `get_ad_performance_monthly_table` ×1(당월, `media` 생략) — section-1용
   (`monthly-detailed-section-1-target-achievement.md` 참고).
3. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 2단계 응답 수신 즉시, 다음 단계 전에
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 8단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 툴호출 예산이 바닥나면 사용자는 아무것도 못
   본다 — 자매 스킬의 실제 사고 사례가 있는 필수 단계다.
4. **2차 배치 (한 메시지에 동시 발사)**: section-3/4 공유 응답(`group_by:"media"`, 6개월,
   `media` 생략, `day_offset` 1회) + section-5(google/meta/naver/airbridge 각각
   `group_by:"campaign"`, 전월~당월, `day_offset`, 4회) + `list_promotions` 1회(당월 1일
   30일 전 ~ target_date). 각 섹션 파일의 호출 명세를 그대로 따른다.
5. **계산**: section-1 값 판정(섹션 파일의 계산 규칙), section-3 배열 3개 산출, section-4
   channels 매핑(원본 수치만 — 파생지표는 빌더가 계산), section-5는
   `monthly_campaign_rows.py` 실행(`> /tmp/s5_rows.json`).
6. **section-2 Executive Summary 작성** — `list_promotions` 외 신규 MCP 호출 없이 다른 섹션
   응답만 재사용해 AI가 직접 작성 (`monthly-detailed-section-2-executive-summary.md`의 규칙).
7. **최종 빌드**: `assets/build_report.py`에 값 JSON을 heredoc으로 넘겨 최종 HTML을 생성한다.
   출력 경로(`out`)는 `~/Downloads/laighthouse-reports/브리즘_monthly-detailed_{기준_일자}.html`
   (디렉터리는 빌더가 만든다).
8. 완성된 HTML을 **두 곳에 동시에** 낸다 — 하나만 하고 끝내지 않는다:
   - **채팅 내부 표시**: Artifact(또는 `mcp__visualize__show_widget`)로 게시 — 3단계 스켈레톤과
     같은 대상을 갱신. 둘 다 없는 호스트(Claude Desktop 채팅 등)에서는 이 사본을 만들지 않고
     저장 파일만 안내한다.
   - **파일 저장**: 7단계에서 빌더가 이미 위 경로에 저장했다 — 별도 재저장 불필요.
9. 완료 메시지는 아래 **완료 메시지 형식** 그대로 (즉석 요약 금지).

> ℹ️ 이 호스트의 Bash 기본 셸은 `sh`(dash)일 수 있다 — 프로세스 치환(`<(...)`) 같은 bash 전용
> 문법은 `bash -c '...'`로 감싸거나 쓰지 않는다.

---

## 병렬 호출 지침 (성능 최적화)

> ⚡ 서브에이전트 없이 오케스트레이터(본 대화)가 MCP를 직접 호출한다. **서로 의존성 없는 MCP
> 호출은 한 메시지 안에서 동시에(병렬 tool call로) 발사한다.** 배치의 실제 효과는 "턴 오버헤드
> 제거"다(네트워크 동시 실행 보장은 아님 — 실측 daily-summary 참고). 진짜 속도는 (a) 호출 총
> 개수 축소(section-1의 media 생략 통합, section-4의 호출 완전 제거·section-3 응답 재사용 —
> section-5만 campaign 단위 고카디널리티라 매체별 4회 유지), (b) 캡처 훅(대용량 응답의 파일
> 우회), (c) asset 스크립트(재타이핑·손계산 제거)에서 나온다. 데이터 호출은 총 10회
> (1차 배치 4회 + 2차 배치 6회)로 끝난다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
브리즘 월간 보고서({기준_일자}) 생성 완료.
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
| 1 | 목표 달성 현황 (당월) | `monthly-detailed-section-1-target-achievement.md` | `s1` |
| 2 | Executive Summary | `monthly-detailed-section-2-executive-summary.md` | `s2` |
| 3 | 월별 광고 성과 (최근 6개월, 차트) | `monthly-detailed-section-3-monthly-ad-performance.md` | `s3` |
| 4 | 매체 성과 비교 (M-1 vs M0) | `monthly-detailed-section-4-channel-performance.md` | `s4` |
| 5 | 캠페인 성과 비교 (M-1 vs M0) | `monthly-detailed-section-5-campaign-performance.md` | `s5` |

- section-4는 **section-3의 6개월 공유 응답을 재사용**해 별도 호출이 없다. section-5는
  `group_by:"campaign"`이라 granularity가 달라 공유하지 않는다(독립 4회 호출). section-2는
  `list_promotions` 1회 외에 신규 호출 없이 재사용만 한다.
- section-5만의 예외 규칙: 비교 불가 시 변화량을 생략하지 않고 **`(-)`로 명시 표시**한다
  (전월 캠페인 데이터 누락이 흔하기 때문) — 다른 섹션에 이 규칙을 옮기지 않는다.
- 섹션 데이터가 준비 안 되면 해당 `s*` 키를 빌더 입력에서 뺀다 → "데이터 준비 중" 카드로
  렌더링된다. 섹션을 임의로 생략하는 개념은 없다 — 항상 5개 전부.
