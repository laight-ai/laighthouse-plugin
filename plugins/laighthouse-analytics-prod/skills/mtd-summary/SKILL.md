---
name: mtd-summary
description: >
  브리즘(Google/Meta/Naver 광고 성과를 Airbridge 매출과 엮어 추적하는 airbridge 기반 브랜드)
  전용 Executive MTD 보고서 생성 스킬. "Executive MTD 보고서", "임원용 MTD 보고서", "executive mtd" 요청 시 사용.
  `mtd-detailed`(상세 MTD 보고서)를 임원이 딥다이브 없이 훑어볼 수 있도록 5개 섹션으로 재구성한 보고서. 대상 브랜드는 브리즘 하나뿐이다.
metadata:
  version: "2.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 Executive MTD 보고서**(HTML)로 렌더링한다. **대상
브랜드는 브리즘(airbridge 기반) 하나뿐이다.** 다른 종류의 브리즘 보고서는 각각 별도 스킬이다
(`mtd-detailed`/`daily-detailed`/`daily-summary`/`monthly-detailed`/`monthly-summary`/
`creative-detailed`/`creative-summary`). 이 스킬은 호출되면 항상 Executive MTD 보고서를
렌더링한다 — weekly나 다른 브랜드는 지원하지 않는다(요청받으면 알맞은 스킬을 안내하거나
미지원임을 알린다).

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
  `campaign_name` 등), **지표 키는 테넌트별**이다 — 브리즘은 한국어 지표명 `광고비`(비용)/
  `노출`/`클릭`/`매출_AB`/`예약완료_AB`와 서버 계산 비율 지표 `ROAS_AB`/`CPM`/`CTR`/`CVR`/
  `CPA`/`CPA_AB`를 쓴다. **응답의 `metrics` 목록이 유효한 지표 키의 유일한 진실이다** —
  키를 추측하지 않는다.
- ⚠️ 비율 지표(`ROAS_AB`/`CTR` 등)는 요청한 grain 기준으로 서버가 이미 % 값으로 계산해 준다 —
  ×100 불필요. **행별 비율 값을 합산해 상위 기간/상위 그룹 비율을 만들지 않는다**(필요하면
  원자 지표 합으로 다시 계산).
- ⚠️ `group_by`는 **차원명 문자열 리스트**다 (예: `["media"]`) — 예전의 문자열 enum이 아니다.
  생략하면 총계만 온다(day/month grain이면 `date`/`month` 키 포함).
- `media` 필터 값은 `"Google"`/`"Meta"`/`"Naver"` (대소문자 변형·한국어 표기는 서버가 흡수).
- ⚠️ `get_target_progress_v2`의 ROAS류 수치는 비율값(0.87)이므로 ×100 해서 %로 쓴다 —
  이 도구 응답만 여전히 markdown 표다.
- `media`를 생략하고 `group_by:["media"]`로 조회하면 `media`가 `null`인 행이 온다 — 이게
  `Organic`이다(광고비 없이 매출만 귀속). 정상 응답이니 버리지 말고 섹션 규칙대로 매핑한다.
  `Others`는 대응하는 `media` 값이 없어 `-`/"데이터 준비 중"으로 남긴다 — 다른 값으로 지어
  채우지 않는다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답은 이미 정제가 끝난 최종 데이터다 — 그대로 스크립트에 넘기고, 값을 의심·보정·
> 재계산·추정하지 않는다.** 예외는 각 섹션 파일에 명시된 표기 변환뿐이다(ROAS ×100, 6개월
> 고정 표시의 0 채움 등). 데이터가 비거나 갭이 있어도 채우거나 추정하지 않는다.
>
> 🚫 **응답이 크다고 느껴져도 선택지는 정확히 둘뿐이다**: (1) 원본을 가공 없이 전부 규칙대로
> 집계해 빌더에 넘기거나, (2) 정말 처리 불가능하면 그 섹션을 "데이터 준비 중"으로 표시한다
> (빌더 입력에서 해당 `s*` 키를 빼면 된다). **다른 섹션·다른 월 값의 재사용, 비슷해 보이는
> 숫자 생성, 부분 전사 후 추정은 — 그 대체 숫자가 진짜 쿼리 결과라도 — 전부 금지다.** 이미
> 정상적으로 받은 응답은 그대로 쓴다. 응답을 못 받았을 때만 (2)로 간다.

## 실행 방식 절대 지침

> 이 스킬의 렌더링은 전부 **미리 검증된 asset 스크립트**가 한다 — 모델이 실행 중
> `.py`/`.js` 스크립트 파일을 새로 만들거나, HTML을 직접 타이핑하거나, 섹션별 조각 파일
> (`section2.html` 등)·중간 스테이징 HTML을 만들었다가 다시 읽어 합치는 것은 전부 금지다.
>
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션 1~5
>   마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의 호출로**
>   완성한다. 모델은 소량 값 JSON만 따옴표 있는 heredoc(`<<'PYEOF'`)으로 stdin에 넘긴다 —
>   포맷팅(₩콤마/%/N/A)·월 라벨·각주 문구·section-5의 ROAS/변화량/화살표/색상/정렬까지 빌더가
>   처리한다. 입력 스키마는 스크립트 상단 docstring 참고.
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다. 응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>`
>   스텁으로 오는 경우(현재 이 스킬의 도구는 캡처 대상이 아니라 드물다) 그 파일을 Read로 통째로
>   컨텍스트에 올리지 말고, Bash에서 파일을 직접 파싱해 필요한 집계값만 추출한다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 브리즘 Executive MTD 보고서 |
| brand_name | 항상 `breezm` | breezm |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `mtd-summary` 고정.
2. **1차 배치 (한 메시지에 동시 발사)**: `get_target_progress_v2` ×3(google/meta/naver) +
   `get_ad_performance` ×1(당월 1일~target_date, `time_grain:"month"`, `group_by:["media"]`, media 생략)
   — section-1용 (`mtd-summary-section-1-target-achievement.md` 참고).
3. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 2단계 응답 수신 즉시, 다음 단계 전에
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 8단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 툴호출 예산이 바닥나면 사용자는 아무것도 못
   본다 — 자매 스킬에서 실제 사고 사례가 있는 필수 단계다.
4. **2차 배치 (한 메시지에 동시 발사)**: `get_ad_performance` ×1(5개월 전 1일~target_date, `time_grain:"month"`, `group_by:["media"]`, media 생략,
   5개월 전~당월 6개월, `day_offset`=target_date.day — **section-3/4/5가 공유**) +
   `list_promotions` ×1(당월 1일보다 30일 앞선 날짜 ~ target_date — section-2용).
   각 섹션 파일의 호출 명세를 그대로 따른다.
5. **계산**: section-1 값 판정(섹션 파일의 계산 규칙), section-3 배열 3개·section-4 배열 2개·
   section-5 채널별 M-1/M0 수치를 4단계 공유 응답에서 산출한다 (각 섹션 파일의 빌더 입력
   매핑 표 참고).
6. **section-2 Executive Summary 작성** — `list_promotions` 외 신규 MCP 호출 없이 다른 섹션
   응답만 재사용해 AI가 직접 작성 (`mtd-summary-section-2-executive-summary.md`의 규칙).
7. **최종 빌드**: `assets/build_report.py`에 값 JSON을 heredoc으로 넘겨 최종 HTML을 생성한다.
   출력 경로(`out`)는 `~/Downloads/laighthouse-reports/브리즘_mtd-summary_{기준_일자}.html`
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
> 개수 축소 — 이 스킬은 `media` 생략 통합과 section-3 응답의 4/5 공유로 데이터 호출이 **총
> 6회**(예전 최대 17회+)다, (b) asset 스크립트(재타이핑·손계산 제거)에서 나온다.

- section-1의 당월 1개월 호출을 section-3의 6개월 호출에 **의도적으로 합치지 않는다** —
  이론적으로 당월 데이터는 6개월 응답에도 있지만, 합치면 section-1(스켈레톤 직후 첫 렌더링)이
  더 무거운 6개월 조회 완료까지 기다려야 해서 스켈레톤 선게시 목적과 어긋난다.
- `get_target_progress_v2`는 도구 스키마가 `media`를 필수 enum으로 요구해 3회를 1회로 합칠 수
  없다 (백엔드 스키마 변경 필요 — `daily-summary/CLAUDE.md` 참고).

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
브리즘 Executive MTD 보고서({기준_일자}) 생성 완료.
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
| 1 | 목표 달성 현황 | `mtd-summary-section-1-target-achievement.md` | `s1` |
| 2 | Executive Summary | `mtd-summary-section-2-executive-summary.md` | `s2` |
| 3 | 월별 광고 성과 (6개월 차트) | `mtd-summary-section-3-monthly-ad-performance.md` | `s3` |
| 4 | 매출 추이 (6개월 라인 차트) | `mtd-summary-section-4-revenue-trend.md` | `s4` |
| 5 | 매체 성과 비교 (전월 vs 당월) | `mtd-summary-section-5-channel-comparison.md` | `s5` |

- section-3의 6개월 공유 응답을 section-4(광고 매출)/section-5(마지막 2개월)가 재사용한다
  — 별도 호출 없음. section-2만 `list_promotions` 1회를 새로 호출한다.
- 섹션 데이터가 준비 안 되면 해당 `s*` 키를 빌더 입력에서 뺀다 → "데이터 준비 중" 카드로
  렌더링된다. 섹션을 임의로 생략하는 개념은 없다 — 항상 5개 전부.
- section-1의 no-budget 메시지는 오류가 아니다 — `s1`을 빼지 말고 N/A(null) 규칙대로 채운다.
