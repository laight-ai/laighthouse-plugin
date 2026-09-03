---
name: daily-detailed
description: >
  브랜드 비종속 데일리 보고서 생성 스킬. "데일리 보고서", "일간 보고서", "daily 보고서" 요청 시 사용.
  최근 7일 등 짧은 기간 단위로 매일 확인하는 실무자용 일자별 성과 보고서(캠페인·광고그룹·광고 단위
  D-1 vs D-0 비교 포함). 사용자가 말한 브랜드의 매체·지표를 실행 시작에 디스커버리해서 어떤 브랜드에도
  같은 방식으로 동작한다.
metadata:
  version: "2.0.0"
---


> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계
> 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 스크립트 실행 → 완료 순서로 진행한다.


## 역할

MCP 데이터를 받아 **라이트하우스 스타일 데일리 성과 보고서**(HTML)로 렌더링한다. 다른 종류의
보고서는 각각 별도 스킬이다 (`mtd-detailed`/`mtd-summary`/`daily-summary`/`monthly-detailed`/
`monthly-summary`/`creative-detailed`/`creative-summary`). 이 스킬은 호출되면 항상 데일리 보고서를
렌더링한다 — weekly는 지원하지 않는다(요청받으면 알맞은 스킬을 안내하거나 미지원임을 알린다).

**브랜드 비종속**: 사용자가 말한 브랜드명을 모든 MCP 호출의 `brand_name`과 제목·파일명에 그대로
쓴다. 매체 목록(`media_list`/`has_organic`)과 지표 키(`metric_names` → 역할별 `metric_keys`)는
실행 시작의 **디스커버리 호출**로 알아낸다 — 절차·역할 해석 규칙은
`shared/references/generic-report-pattern.md`가 단일 소스다. 이 파일과 섹션 파일에서 "cost/
impression/click/revenue/conversion 키"라 하면 그 맵의 값을 뜻한다. 매체 구분은 행의 `media`
차원 값이며, 매출/전환은 각 행에 지표로 함께 들어온다(별도 조인 불필요).

generic 도구(`get_ad_performance`)와 `get_target_progress_v2`, `list_promotions`만 쓴다.

공통 호출 규칙 (`get_ad_performance`):
- ℹ️ 응답은 **JSON 봉투**다: `{"source": "elt", "tenant": "<brand>", "time_grain": "day"|"month"|
  "total", "dimensions": [...], "metrics": [...], "row_count": N, "rows": [...]}`. 행의 차원
  키는 영문(`date`(day grain)/`month`(month grain, "YYYY-MM")/`media`/`campaign_id`/
  `campaign_name`/`ad_group_id`/`ad_group_name`/`ad_id`/`ad_name` 등), **지표 키는 테넌트별**
  이다. **응답의 `metrics` 목록이 유효한 지표 키의 유일한 진실이다** — 키를 추측하지 않고,
  디스커버리 응답에서 역할별 `metric_keys`를 한 번 정해 그 키만 쓴다.
- ⚠️ 비율 지표(ROAS/CTR 등)는 요청한 grain 기준으로 서버가 이미 % 값으로 계산해 준다 —
  ×100 불필요. **행별 비율 값을 합산해 상위 기간/상위 그룹 비율을 만들지 않는다**(필요하면
  원자 지표 합으로 다시 계산). 이 스킬의 모든 ROAS/CTR/CPA는 역할 키의 원자 값으로 계산한다.
- ⚠️ `group_by`는 **차원명 문자열 리스트**다 (예: `["media"]`,
  `["media","campaign_id","campaign_name"]`) — 예전의 문자열 enum(`total`/`campaign` 등)이
  아니다. 생략하면 총계만 온다(day/month grain이면 `date`/`month` 키 포함). `metrics` 생략 시
  테넌트 전체 지표가 온다.
- 매체 필터는 `filters: {"media": ["<media_list의 값>"]}` (정확 일치, 디스커버리 응답 문자열
  그대로) — 예전의 `media: str` 파라미터는 제거됐다. 이 스킬에서 필터를 쓰는 곳은 section-5
  (매체별 1회 호출)뿐이고 나머지는 `filters` 생략으로 전 매체를 한 번에 받는다.
- `group_by:["media"]` 응답의 `media`가 `null`인 행이 `Organic`이다(광고비 없이 매출만 귀속,
  `has_organic`일 때). 정상 응답이니 버리지 말고 섹션 규칙대로 다룬다. 디스커버리에 없는 매체
  행을 지어 넣지 않는다.
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
>   않는다(경로만 넘긴다). 빌더에 넘기는 것과 **같은** `metric_keys`/`currency`/`threshold`를
>   함께 넘긴다.
> - **`assets/build_report.py`** — 최종 HTML 조립·저장. `assets/report-template.html`(섹션 1~5
>   마크업·스크립트의 단일 진실 공급원)에 값을 치환하고 chart.js를 인라인해 **한 번의 호출로**
>   완성한다. 모델은 소량 값 JSON만 heredoc으로 넘긴다 — 섹션별 HTML 조각 파일(part1.html 등)을
>   만들거나 chart.js를 타이핑하는 방식은 금지된 과거 패턴이다. 입력 스키마는 스크립트 상단
>   docstring과 아래 「빌더 입력 계약」 참고.
> - dxd 실행과 빌더 실행은 **한 번의 Bash 호출 안에 이어서** 담을 수 있다
>   (`dxd s4 > f1 && dxd s5 > f2 && build_report`) — 왕복을 늘리지 않는다.
> - MCP 응답을 스크래치 파일에 옮겨 적었다가 다시 읽는 왕복, 별도 파서/생성 스크립트 작성,
>   응답 원본의 재타이핑은 전부 금지다.
> - (최후 폴백) Bash/python3가 전혀 없는 호스트에서만, `assets/report-template.html`을 Read해서
>   placeholder를 직접 치환한다 — 그 외 호스트에서는 절대 이 경로를 쓰지 않는다.

## 빌더 입력 계약 (dxd_table_rows.py · build_report.py 공통)

두 스크립트는 브랜드·매체·지표명을 전혀 모른다 — 아래 값을 모델이 디스커버리 결과로 채워
**둘 다에 같은 값으로** 넘긴다(`generic-report-pattern.md` 6절):

| 키 | 값 | 비고 |
|---|---|---|
| `metric_keys` | `{"cost": ..., "impression": ..., "click": ..., "revenue": ..., "conversion": ...}` | 역할 해석 결과(3절). `conversion`은 정해졌을 때만 넣는다 — 없으면 section-4/5의 전환·CPA 컬럼이 통째로 빠진다. `<th>` 텍스트에 이 값이 그대로 들어간다. |
| `currency` | 통화 기호 문자열 | 생략 시 `"₩"`. 모든 금액 포맷·차트 축·각주에 이 값이 쓰인다(리터럴 ₩ 없음). |
| `threshold` | 숫자 | section-4/5 "D-0 광고비 ≤ threshold 제외" 기준, 생략 시 `10000`(₩ 기준값). 통화가 다르면 그 통화에서 같은 의미의 값을 명시한다. dxd와 빌더에 같은 값. |
| `s4.rows_file` / `s5.rows_file` | dxd 출력 파일 경로 | dxd 출력 행: `[{"search": "<매체 캠페인 [광고그룹 광고] 소문자>", "html": "<tr>...</tr>"}]`. 매체 라벨은 행의 `media` 값 **그대로**(`null`은 `"Organic"`), 매체 순서·개수는 응답이 정한다(고정 행 목록 없음). |

`dxd_table_rows.py`는 `metric_keys`를 생략하면 봉투 `metrics`에서 패턴의 후보 목록으로 자동
해석하지만, 빌더는 `<th>`를 만들기 위해 반드시 `metric_keys`가 필요하므로 **항상 둘 다에 명시**해
어긋남을 없앤다.

## 입력 파라미터

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 (`{브랜드명} 데일리 보고서`) | acme 데일리 보고서 |
| brand_name | 사용자가 말한 브랜드명 그대로 | acme |
| 기준 일자 | 보고서 기준 날짜 (`target_date`, D-0) | 2026-08-10 |

섹션 구성은 고정 5개(아래 표) — 사용자가 섹션을 고르는 개념이 없다.

---

## 실행 순서

1. 파라미터를 파싱한다. report_type은 `daily-detailed` 고정.
2. **디스커버리 1회** (`generic-report-pattern.md` 2절): `get_ad_performance`(당월 1일~
   target_date, `time_grain:"total"`, `group_by:["media"]`, `metrics:[]`) → `media_list`/
   `has_organic`/`metric_names`. 여기서 역할별 `metric_keys`를 정한다(3절; cost/impression/
   click/revenue 미해결이면 한 번에 질문, conversion 미해결이면 역할 없음).
3. **1차 배치 (한 메시지에 동시 발사)**: `get_target_progress_v2` × len(media_list)
   (media=각 값 `.lower()`; 미지원/에러는 목표 없음) + `get_ad_performance` ×1(당월 1일~
   target_date, `time_grain:"month"`, `group_by:["media"]`, `filters` 생략) — section-1용
   (`daily-detailed-section-1-target-achievement.md` 참고).
4. ⏱ **필수 체크포인트 — 스켈레톤 선(先) 게시.** 3단계 응답 수신 즉시, 다음 단계 전에
   `python3 assets/build_report.py`를 `{"skeleton": true, ...}`로 1회 호출해 전 섹션 "데이터
   준비 중" 골격을 만들고 게시한다(아래 9단계와 같은 출력 경로/Artifact — 이후 재게시로 교체).
   이 단계를 건너뛰고 끝에서 한꺼번에 내놓으려다 툴호출 예산이 바닥나면 사용자는 아무것도 못
   본다 — 실제 사고 사례가 있는 필수 단계다.
5. **2차 배치 (한 메시지에 동시 발사)**: section-3(`time_grain:"day"`, 7일, `group_by` 생략
   1회 + `list_promotions` 1회), section-4(`time_grain:"day"`, 이틀,
   `group_by:["media","campaign_id","campaign_name"]`, `filters` 생략 1회),
   section-5(`time_grain:"day"`, 이틀, `group_by:["media","campaign_name","ad_group_name",
   "ad_name"]`, **`media_list`의 매체마다 `filters:{"media":[<값>]}`로 1회씩** = len(media_list)회).
   각 섹션 파일의 호출 명세를 그대로 따른다.
6. **계산**: section-1 값 판정(섹션 파일의 계산 규칙), section-3 배열 3개 산출,
   section-4/5는 `dxd_table_rows.py` 실행(`> /tmp/s4_rows.json`, `> /tmp/s5_rows.json`,
   `metric_keys`/`currency`/`threshold` 포함).
7. **section-2 Executive Summary 작성** — 신규 MCP 호출 없이 다른 섹션 응답만 재사용해 AI가
   직접 작성 (`daily-detailed-section-2-executive-summary.md`의 규칙).
8. **최종 빌드**: `assets/build_report.py`에 값 JSON(`metric_keys`, `currency`, `threshold` 포함)
   을 heredoc으로 넘겨 최종 HTML을 생성한다. 출력 경로(`out`)는
   `~/Downloads/laighthouse-reports/{브랜드명}_daily-detailed_{기준_일자}.html`
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
> 개수 축소(section-1/3/4의 `filters` 생략 통합 — section-5만 고카디널리티라 매체별 유지), (b)
> 캡처 훅(대용량 응답의 파일 우회), (c) asset 스크립트(재타이핑·손계산 제거)에서 나온다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
{브랜드명} 데일리 보고서({기준_일자}) 생성 완료.
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
