# creative-summary 성능 최적화 변경 이력

`daily-summary`에 먼저 적용한 최적화 세트(`daily-summary/CLAUDE.md` 참고)를 `creative-summary`에
구조적으로 적용 가능한 범위에서 이식한 기록.

## 2026-08-09 (2) — section-1 `media` 생략 되돌림 + Bash 집계 예외 추가

같은 날 아래 "2026-08-09" 항목에서 적용한 `media` 생략 통합을, 실제 프로덕션 실행에서
드러난 문제로 **section-1(최우수 소재)에 한해서만** 되돌렸다. 이 스킬의 다른 부분(썸네일
호출, 병렬 호출, 스크래치패드 금지, chart.js 인라인 방식 등)에는 영향 없음.

- **무엇이 문제였나**: 실제 Claude Code 실행에서 `get_ad_performance_daily_table`을
  `group_by:"ad"`로 `media` 생략 호출했더니 응답이 **76만+자**(7일 윈도우)로 나왔다 — 컨텍스트에
  담기엔 너무 크다(참고로 `media="meta"` 단독 호출도 이미 132,913자로 컸는데, 생략 시 5~6배로
  커진 것). 모델이 이 크기를 감당하지 못해, 거대한 마크다운 표를 bash heredoc 파일에 손으로
  나눠 옮겨 적고 소재별 7일 합산(비용/노출/클릭 합계, campaign_name+asset_group+ad_name으로
  meta+airbridge 조인, 비용 내림차순 정렬)을 **머릿속 추론으로** 수행했다 — 그리고 effort
  예산이 부족해지자 일부 합산값을 "합리적인 근사치로 채우는" 방식으로 **추정값을 실제 값처럼
  보고서에 반영**했다. 이는 이 스킬의 "MCP 응답을 의심·재계산하지 않는다"는 원칙과는 별개로,
  **집계 자체의 정확성이 깨진 것**이라 명백한 정확성 위반이며, 이 단계에만 약 6분이 걸려 이
  스킬의 가장 큰 성능 병목이 됐다.
- **무엇을 되돌렸나**: section-1의 `get_ad_performance_daily_table` 호출을 `media` 생략 1회
  → `media="meta"`/`media="airbridge"` 각각 명시한 **2회 호출**로 원복(예전 방식과 동일,
  같은 7일 윈도우). section-3/4/5는 여전히 이 두 응답을 그대로 공유·재사용한다 — 공유 관계
  자체는 바뀌지 않았고, section-1이 그 데이터를 "어떻게 받아오는지"만 바뀌었다.
  - **영향받은 파일**: `SKILL.md`(실행 순서 2/3단계, 병렬 호출 지침, section-3/5 설명 문단),
    `creative-summary-section-1-top-creatives.md`, `creative-summary-section-3-daily-creative-
    total-performance.md`, `creative-summary-section-4-daily-CTR.md`,
    `creative-summary-section-5-daily-ROAS.md`(참조하는 MCP 호출 JSON 블록 표기만 갱신, 로직은
    무변경).
  - **범위 밖**: `get_ad_creative_info`(썸네일) 호출은 원래부터 `media` enum 구조가 아니어서
    이 되돌림과 무관 — 손대지 않았다. `get_target_progress_v2` 통합도 이 스킬에 해당 없음(원래
    안 씀).
- **왜 정당한 회귀가 아니라 이번 최적화 자체의 결함인가**: "호출 개수를 줄이자"는 목표는
  맞았지만, `group_by:"ad"`처럼 이미 행 수가 많은 고카디널리티 조회에서는 `media` 생략이
  얻는 "호출 1회 절감"보다 "응답 크기 5~6배 폭증"의 비용이 훨씬 크다 — 이번 사례로 실측
  확인됐다. `group_by:"total"`처럼 행 수가 적은 다른 호출들에는 이 트레이드오프가 적용되지
  않으므로, 이 되돌림은 section-1의 `group_by:"ad"` 호출에만 한정된다.
- **Bash 집계 예외 추가**: 위 사고가 재발하지 않도록, "실행 방식 절대 지침"(스크립트 파일
  생성 금지)에 좁은 예외를 추가했다 — 재사용 가능한 스크립트/노트북 **파일**을 만드는 것은
  여전히 금지지만, `group_by:"ad"`처럼 행이 많은 응답을 받았을 때 media 필터링·조인·소재별
  합산·정렬을 **파일로 남기지 않는 1회성 Bash 명령**(grep/awk/jq 등)으로 처리하고 그 결과
  요약표만 컨텍스트에 남기는 것은 허용한다. 근사치로 채우거나 일부만 계산하는 것은 이 예외
  아래에서도 여전히 금지다 — Bash 집계는 전체 행에 대해 정확한 값을 내므로 근사가 필요할
  이유가 없다.
  - **영향받은 파일**: `SKILL.md`("실행 방식 절대 지침" 문단에 예외 추가).

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합 (+ 섹션 간 중복 호출 제거)

- **무엇**: section-1(최우수 소재)이 `get_ad_performance_daily_table`을
  `media="meta"`/`media="airbridge"`로 각각 호출하던 것을 **`media` 생략 1회 호출**로
  통합(`group_by:"ad"`, 최근 7일). 이 응답에서 `media === "meta"`/`media === "airbridge"`
  행을 걸러 쓴다.
  - 추가로 발견한 것: section-4(일별 CTR)가 section-1과 **완전히 동일한 파라미터**
    (`media="meta"`, `group_by:"ad"`, 같은 7일 범위)로 다시 호출하고 있었고, section-5(일별
    ROAS)도 마찬가지로 section-1과 동일한 `media="airbridge"` 호출을 중복하고 있었다 —
    media 생략과 무관하게 이미 존재하던 순수 중복 호출. section-1의 통합 호출 하나를
    section-3/4/5가 전부 공유·재사용하도록 바꿔서 이 중복도 함께 제거했다.
  - 결과: 이 스킬의 데이터 호출이 소재 데이터 4회(section-1 2회 + section-4 1회 + section-5
    1회) → **1회**로, `get_ad_creative_info`(썸네일)까지 합쳐 총 **2회**로 줄었다(예전 5회).
- **왜**: `laighthouse-prism`의 `src/repositories/v2_ad_performance.py`
  (`query_daily`)를 직접 확인 — `media`가 `None`이면 `if media in (None, "google"/"meta"/
  "tiktok"/"naver"/"ga4"/"airbridge")` 조건으로 모든 `DataSource`를 순회해 합친 결과를
  반환한다(`group_by` 값과 무관하게 동일한 분기 구조 — `"ad"`를 포함해 어떤 `group_by`든
  같은 방식으로 동작). `daily-summary`에서 이미 검증된 것과 같은 메커니즘이라 값이 바뀌지
  않는다.
- **검증**: 코드 레벨로 `v2_ad_performance.py`의 `query_daily` 분기를 직접 읽어 확인(daily
  응답 로직은 `daily-summary`가 실측 검증한 것과 동일 코드 경로). 실제 MCP 응답 값 대조는
  이번 세션에서는 수행하지 않았음 — 아직 프로덕션 사용 전 실측 재확인을 권장한다(아래
  "확인 필요" 참고).
- **영향받은 파일**: `SKILL.md`(실행 순서 2/3단계), `creative-summary-section-1-top-
  creatives.md`, `creative-summary-section-3-daily-creative-total-performance.md`,
  `creative-summary-section-4-daily-CTR.md`, `creative-summary-section-5-daily-ROAS.md`.

### 2. `list_promotions` 중복 호출 — 해당 사항 없음

- `creative-summary`는 애초에 `list_promotions`를 어느 섹션에서도 호출하지 않는다(section-2
  Executive Summary도 "신규 MCP 호출 전혀 없음"으로 명시돼 있음) — 적용 대상 없음.

### 3. `chart.umd.min.js` 인라인 방식 변경

- **무엇**: `daily-summary`와 동일하게, "저장 폴더에 이미 존재하는지 확인 → 없을 때만 1회
  복사(전용 복사 도구 없으면 일반 파일 쓰기로라도) → `<script src="chart.umd.min.js">`
  상대 경로 참조"로 변경. CSP로 상대 경로가 막힌 호스트(Artifact 등)에서만 최후 수단으로
  기존 `{CHART_JS_INLINE}` 인라인 방식을 유지.
- **왜**: 기존 `creative-summary`는 매 리포트마다 208KB(~5만 토큰)를 그대로 응답 텍스트로
  재생성하는 예전 방식이었다(daily-summary의 최적화 이전 상태와 동일한 패턴).
- **영향받은 파일**: `SKILL.md`(6/7단계, 보고서 골격 `<head>` 부분, CDN 경고 문구).

### 4. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지

- **무엇**: `daily-summary`와 동일한 문구로 SKILL.md에 추가(기존에 이 규칙이 없었음).
- **왜**: `creative-summary`도 서브에이전트를 쓰지 않으므로 중간 저장용 파일이 불필요하다.

### 5. 병렬 호출 지침 추가

- **무엇**: "병렬 호출 지침 (성능 최적화)" 섹션을 신규 추가(기존에 없었음). `daily-summary`가
  실측으로 정정한 결론(배치의 실제 효과는 "턴 오버헤드 제거"이지 "네트워크 동시 실행"이
  아니며, 진짜 속도 개선은 호출 총 개수를 줄이는 것)을 처음부터 정확하게 반영해서 작성했다
  — `creative-summary`는 재측정 없이 daily-summary의 실측 결론을 그대로 인용한다.
- **왜**: 이 스킬도 서브에이전트 없이 오케스트레이터가 직접 MCP를 호출하는 구조라
  daily-summary와 동일한 논리가 적용된다.

## 적용하지 않은 것

- **`get_target_progress_v2` 통합**: 이 스킬은 애초에 `get_target_progress_v2`를 쓰지
  않는다(section-1의 설명에 "`get_target_progress_v2`나 `day_offset`은 쓰지 않는다"고 명시)
  — 해당 사항 없음.
- **`get_ad_creative_info` "media 생략" 시도**: 이 도구는 `media` enum이 아니라
  `google`/`meta`/`tiktok` 각각의 key 배열을 한 요청에 담아 보내는 형태라, `get_ad_performance_*`
  계열과 파라미터 모양 자체가 다르다. 이미 한 번의 호출로 필요한 모든 소재의 썸네일을
  가져오므로 추가로 통합할 여지가 없다 — 손대지 않았다.
- **`get_naver_*` 도구**: 이 스킬은 naver 전용 도구를 아예 쓰지 않는다 — 해당 사항 없음.

## 확인 필요 (다음 실제 실행 때 검증)

- 이번 변경은 `v2_ad_performance.py` 코드를 직접 읽고 안전성을 판단했지만, `daily-summary`
  최적화 때처럼 로컬 prism-local MCP 서버에 대해 **`media` 생략 응답과 기존 분리 호출 응답의
  실제 수치를 대조하는 실측**은 이번 세션에서 하지 않았다. 다음 `creative-summary` 실행 시
  section-1의 ROAS/CTR 순위·값, section-3의 전체 CTR/ROAS 추이, section-4/5의 상위 5개 소재
  선정 결과가 변경 전(각 매체 개별 호출)과 동일한지 한 번 대조해보는 것을 권장한다.
