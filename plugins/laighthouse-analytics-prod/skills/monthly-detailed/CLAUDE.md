# monthly-detailed 성능 최적화 변경 이력

`daily-summary`에서 검증된 최적화를 `monthly-detailed`에 구조적으로 적용 가능한 범위까지
이식한 기록. 새로운 최적화를 적용할 때마다 이 파일에 **날짜 + 무엇을 + 왜 + 검증 방법**을
추가한다 — 나중에 회귀가 생기면 어떤 변경이 원인인지 추적하기 위함. `daily-summary/CLAUDE.md`가
1차 조사·실측을 담당했고, 여기서는 그 결론을 재검증 없이 재사용했다(같은 백엔드 API를 쓰므로
`media` 생략 동작은 브랜드/report_type에 무관하게 동일하다).

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합 (+ 섹션 간 응답 재사용)

- **무엇**:
  - section-1의 매출 실적(`get_ad_performance_monthly_table`, `media="airbridge"`,
    `group_by:"media"`) + no-budget fallback 소진액(media별 3회 조건부 호출, `group_by:"total"`)을
    **`media` 생략 1회 호출**(`group_by:"media"`)로 통합 — `daily-summary`와 동일한 패턴.
  - section-3의 매체별 4회 호출(google/meta/naver `group_by:"total"` + airbridge
    `group_by:"media"`)을 **`media` 생략 1회 호출**(`group_by:"media"`)로 통합.
  - section-4는 원래 자신만의 4회 호출(전월~당월, `day_offset`)을 냈으나, **호출 자체를
    완전히 제거**하고 section-3의 공유 응답을 재사용하도록 변경 — section-4가 필요로 하는
    전월(M-1)·당월(M0) 두 달은 section-3의 6개월 범위(5개월 전~당월) 안에 완전히 포함되고,
    `day_offset`도 두 섹션이 동일한 값을 쓴다. `laighthouse-prism`의
    `src/repositories/v2_ad_performance.py`(`query_monthly`, `_query_*_monthly`)를 직접
    확인해 `day_offset`이 범위 내 **모든 월에 균일하게** 적용됨을 검증했다(`extract("day",
    logdate) <= day_offset`가 각 매체 쿼리마다 무조건 걸린다) — 즉 section-3의 6개월 응답에
    들어있는 M-1/M0 행은 section-4가 별도로 호출했을 때와 완전히 동일한 값이다. 이건
    `daily-summary`에는 없던 형태의 최적화(섹션 간 "완전한 호출 제거" 재사용)라 별도로
    기록한다.
  - section-5의 매체별 4회 호출(google/meta/naver/airbridge, 전부 `group_by:"campaign"`)을
    **`media` 생략 1회 호출**(`group_by:"campaign"`)로 통합 — 이 섹션은 4회 호출이 원래부터
    전부 같은 `group_by` 값을 썼으므로(daily-summary의 경우처럼 group_by가 갈리지 않음)
    가장 단순한 형태의 통합이었다. section-3/4가 쓰는 `group_by:"media"` 응답과는 행
    granularity가 달라 서로 공유하지 않는다(섹션 파일에 명시).
- **왜**: `daily-summary/CLAUDE.md`의 실측 결론과 동일 — MCP 호출은 배치해도 사실상 순차
  처리되므로, 턴을 줄이는 것보다 호출 총 개수를 줄이는 것이 실제 속도에 더 직접적으로
  기여한다. 데이터 호출이 조건부 최대 19회(3+3(조건부)+4+4+4+1) → 7회(모두 한 배치,
  조건부 라운드 없음)로 줄었다.
- **검증**: `media` 생략 시 google/meta/naver 행이 매체당 이미 합산된 한 줄로 오고 그 값이
  기존 매체별 분리 호출과 동일하다는 것은 `daily-summary`에서 이미 실측 검증되었고
  (2026-07-23~29 범위/단일 날짜/월간 데이터 전부 일치 확인, `daily-summary/CLAUDE.md` 참고),
  같은 백엔드 함수(`query_monthly`)를 쓰므로 `monthly-detailed`에도 동일하게 적용된다.
  이 세션에서는 추가로 `v2_ad_performance.py`를 읽어 (a) `group_by`가 응답 행의 스키마
  자체(`impression`/`click`/`airbridge_revenue`/`reservation` 등 모든 필드)를 바꾸지 않고
  그룹 기준만 바꾼다는 것, (b) `day_offset`이 범위 내 모든 월에 동일하게 적용된다는 것
  두 가지를 코드 레벨에서 확인해 section-4의 "호출 제거 후 재사용"이 안전함을 검증했다.
  실제 리포트를 생성해 통합 전/후 수치를 대조하는 실측은 수행하지 않았다 — Claude Code
  세션에서는 실제 MCP 서버에 대한 리포트 생성 실행이 불가능해, 이 부분은 daily-summary와
  달리 코드 레벨 검증에 그쳤다(아래 "검증 필요" 참고).
- **영향받은 파일**: `monthly-detailed-section-1-target-achievement.md`,
  `monthly-detailed-section-3-monthly-ad-performance.md`,
  `monthly-detailed-section-4-channel-performance.md`,
  `monthly-detailed-section-5-campaign-performance.md`, `SKILL.md`.

### 2. `list_promotions` 통합 — 적용 대상 아님

- **조사 결과**: `monthly-detailed`는 `list_promotions`를 section-2에서 **1회만** 호출한다
  (30일 룩백). `daily-summary`처럼 여러 섹션이 겹치는 범위로 각자 호출하는 구조가 아니므로
  통합할 대상 자체가 없다. 변경하지 않았다.

### 3. `chart.umd.min.js` 인라인 방식 변경

- **무엇**: `daily-summary`와 동일하게 SKILL.md의 6단계와 「보고서 골격」 섹션을 "이미
  있으면 건너뛴다 → 없을 때만 생성(전용 복사 도구 우선, 없으면 일반 파일 쓰기 도구로)" +
  로컬 저장본은 `<script src="chart.umd.min.js"></script>`(상대 경로) 방식으로 교체했다.
  기존에는 매 리포트마다 208KB 전체를 `{CHART_JS_INLINE}`에 그대로 타이핑하는 방식이었다.
  CSP로 상대 경로 로드가 막힌 호스트(Artifact 등)에서만 기존 인라인 방식을 최후 수단으로
  남겨뒀다.
- **왜**: `daily-summary/CLAUDE.md`의 6번 항목과 동일한 근거 — 208KB ≈ 5만 토큰을 매
  리포트마다 출력 토큰으로 재생성하는 비용을 제거한다. classic `<script src>`가 `file://`
  로컬 상대경로 로딩에서 CORS 제약이 없다는 것도 동일하게 적용된다(HTML 로딩 메커니즘은
  report_type과 무관).
- **영향받은 파일**: `SKILL.md` (6/7단계, 보고서 골격의 `<head>` 부분).

### 4. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지

- **무엇**: SKILL.md에 "MCP 응답을 파일로 저장했다가 다시 Read하지 않는다"는 지침을 추가했다
  (기존 `monthly-detailed` SKILL.md에는 이 규칙이 없었다 — `daily-summary`에는 있었음).
- **왜**: `daily-summary`와 동일한 이유 — `monthly-detailed`도 서브에이전트를 쓰지 않는
  구조라 중간 저장용 파일 자체가 불필요하다.

### 5. 병렬 호출 지침 섹션 추가

- **무엇**: 기존 `monthly-detailed` SKILL.md에는 "병렬 호출 지침" 섹션 자체가 없었다(개별
  단계 설명에만 산발적으로 언급). `daily-summary`의 병렬 호출 지침 섹션(배치의 실제 효과는
  "턴 오버헤드 제거"이지 네트워크 동시 실행이 아니라는 실측 정정 포함)을 이식하고, 통합 후
  호출 목록(7회)을 `monthly-detailed`에 맞게 다시 작성해 추가했다.
- **왜**: 배치 자체는 공짜 이득이므로 명시적으로 지시해두는 것이 안전하고, 실측으로 이미
  확인된 "배치의 진짜 효과" 오해를 새 스킬에도 반복하지 않기 위해 daily-summary의 정정
  설명을 그대로 가져왔다.

## 2026-08-09 (추가) — section-5의 `media` 통합 되돌림 + Bash 집계 예외 추가

### 6. section-5(`group_by:"campaign"`) 통합을 4회 매체별 호출로 되돌림

- **무엇**: 위 "1." 항목에서 `media` 생략 1회 호출로 통합했던 section-5
  (`monthly-detailed-section-5-campaign-performance.md`)를 **google/meta/naver/airbridge
  4회 매체별 호출로 되돌렸다.** SKILL.md의 병렬 호출 지침(4번 항목, 호출 총 개수)도 7회 →
  10회로 다시 수정했다.
- **왜**: 실제 운영 중 형제 스킬 `creative-summary`(같은 도구 계열, `group_by:"ad"`)에서
  `media` 생략 1회 호출이 **7일 창만으로도 766,576자** 응답을 만들어낸 사례가 발견됐다.
  모델이 이 거대한 응답을 컨텍스트에 담지 못해 bash heredoc으로 표 일부를 손으로 옮겨 적고
  머릿속으로 합산하다가 **일부 합계를 근사치로 채우는 실제 정확성 사고**로 이어졌다(해당
  단계에 ~6분 소요). `group_by`가 `total`/`media`처럼 저-카디널리티인 경우(section-1/3/4가
  쓰는 `group_by:"media"`)는 매체 수만큼만 행이 늘어나 안전하지만, `campaign`/`ad`/`ad-set`
  단위는 캠페인/광고 수만큼 행이 곱해져 위험이 다르다. `monthly-detailed`는 날짜 span이
  daily 계열보다 넓은 월 단위라 이 위험이 daily보다 더 크다. section-1(`group_by:"media"`,
  1번 항목)과 section-3/4(같은 `group_by:"media"` 공유)는 저-카디널리티이므로 **손대지
  않았다** — `campaign` 단위인 section-5만 되돌렸다.
- **영향 범위 확인**: `monthly-detailed-section-2-executive-summary.md`(Executive Summary)가
  section-5의 **계산된 캠페인별 데이터**를 재사용하지만, 이는 section-5가 만들어낸 결과값을
  재사용하는 것이지 section-5의 원본 MCP 응답(호출 방식)을 재사용하는 게 아니다 — 데이터
  내용은 4회 매체별 호출이든 1회 통합 호출이든 동일하므로, 이 되돌림이 section-2에 영향을
  주지 않는다. section-3/4는 `group_by:"media"` 응답을 쓰고 section-5와 애초에 공유하지
  않으므로(위 "적용하지 않은 항목" 참고) 마찬가지로 영향 없음.
- **영향받은 파일**: `monthly-detailed-section-5-campaign-performance.md`, `SKILL.md`
  (병렬 호출 지침 4번 항목·총 호출 수).

### 7. "실행 방식 절대 지침" 스크립트 금지에 1회성 Bash 집계 예외 추가

- **무엇**: SKILL.md의 "🚫 별도 스크립트·노트북 파일을 절대 생성하지 않는다" 문단 바로
  아래에, `group_by`가 `ad`/`campaign`/`ad-set`인 섹션에서는 MCP 응답을 받은 즉시 **파일로
  남기지 않는 1회성 Bash 명령**(grep/awk/jq 등)으로 매체 필터링·캠페인별 합산·정렬을 수행하고
  그 결과 요약표만 컨텍스트에 남기라는 예외를 추가했다.
- **왜**: 위 6번 항목의 사고 원인 중 하나가 "스크립트 금지 = Bash도 쓰면 안 된다"는 과잉
  해석이었다 — 재사용 가능한 파이프라인 파일을 만들지 말라는 원래 취지와, "큰 표를 손으로
  옮겨 적거나 머릿속으로 합산하지 말라"는 요구가 충돌하면서 모델이 후자를 손으로 하려다
  근사치를 채웠다. 1회성·파일 미생성 Bash 집계는 기존 금지 원칙(재사용 가능한 스크립트
  파일 생성 금지)을 위반하지 않으면서 이 문제를 해결한다.
- **영향받은 파일**: `SKILL.md` ("실행 방식 절대 지침" 섹션).

## 적용하지 않은 항목 (검토했으나 구조상 해당 없음/보류)

- **`get_target_progress_v2` 3회 통합**: `daily-summary`와 동일하게 `media`가 필수 enum이라
  생략 불가능함을 재확인했다. `monthly-detailed`도 동일 도구를 동일한 방식(media=google/
  meta/naver 3회)으로 쓰므로 손대지 않았다.
- **`get_naver_*` 도구**: `monthly-detailed`는 애초에 naver 전용 도구를 전혀 쓰지 않는다
  (브리즘은 generic 도구만 사용) — 해당 없음.
- **section-3/4 응답과 section-5 응답의 통합**: section-3/4는 `group_by:"media"`, section-5는
  `group_by:"campaign"`으로 행 granularity가 다르다(campaign 단위 vs media 단위 집계) —
  하나의 응답으로 둘 다 충당할 수 없어 별도 호출을 유지했다.
- **실제 리포트 생성 실측(before/after 소요 시간 비교)**: Claude Code 세션에서는 이 플러그인
  스킬을 실제 호스트(Claude Desktop/claude.ai)에서 구동해 시간을 잴 방법이 없다 —
  `daily-summary`의 6번 항목과 동일한 한계. 실제 사용자가 `monthly-detailed`로 리포트를
  생성해 (a) 통합 전/후 렌더링된 수치가 완전히 동일한지, (b) 소요 시간이 실제로 줄었는지
  확인해줘야 한다.
