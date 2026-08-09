# creative-detailed 성능 최적화 변경 이력

`daily-summary`(같은 플러그인, `daily-summary/CLAUDE.md` 참고)에 적용한 최적화를
`creative-detailed`에 구조적으로 적용 가능한 부분만 이식한 작업 기록.

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합 (적용함)

- **무엇**: `get_ad_performance_daily_table`을 `media="meta"` 1회 + `media="airbridge"` 1회로
  나눠 부르던 section-1의 두 호출을 **`media` 생략 1회 호출**로 통합했다. 게다가 section-3
  (`media="meta"` 재호출)과 section-4(`media="airbridge"` 재호출)도 사실상 section-1과
  **완전히 동일한 파라미터**(같은 7일 범위, 같은 `group_by:"ad"`)로 다시 호출하고 있었다 —
  이 중복도 함께 제거했다. section-1/3/4/5가 이제 이 **단일 호출 1개**를 전부 공유한다.
  - section-1: `media` 생략 호출 실행, 응답에서 `media`가 `"meta"`/`"airbridge"`인 행을 각각
    골라 조인.
  - section-3: 신규 호출 없음 — section-1 응답의 `meta` 행만 재사용.
  - section-4: 신규 호출 없음 — section-1 응답의 `airbridge` 행만 재사용(기존에도 section-3의
    meta 데이터는 재사용했지만 airbridge는 별도로 재호출하고 있었음).
  - section-5: 기존에도 "새 호출 없음"이었으나, section-1이 이제 두 응답이 아니라 단일 응답을
    가지므로 문서상 참조만 갱신.
- **왜**: `get_ad_performance_daily_table`을 `media` 생략으로 부르면 v2_ad_performance.py가
  내부적으로 모든 `DataSource`를 순회해 한 응답에 담아 반환한다는 것이 laighthouse-prism
  백엔드 코드로 이미 검증되어 있다(daily-summary에서 실측 확인, 값 불변). 이 스킬은 원래도
  meta/airbridge 두 매체만 필요했으므로, 매체별로 나눠 부르던 것을 하나로 합치면 값은 그대로
  두고 호출 수만 준다. 실제 이전 호출 수는 section-1(2회) + section-3(1회, section-1과 중복)
  + section-4(1회, section-1과 중복) = **4회**였는데, 이제 **1회**로 줄었다.
- **결과 값 불변 근거**: `media` 생략 응답은 매체별 분리 호출 응답의 상집합(superset)이며,
  각 섹션은 필요한 매체(`meta`/`airbridge`)의 행만 걸러 쓰므로 조인·집계 로직과 최종 수치는
  기존과 동일하다. daily-summary에서 이미 이 필터링 방식이 값을 바꾸지 않음을 실제 API
  응답 대조로 확인했다(2026-07-23~29 범위, 단일 날짜, 월간 데이터 모두 일치).
- **영향받은 파일**: `SKILL.md`(실행 순서 2단계, 섹션 설명, 공통 규칙),
  `creative-detailed-section-1-top-creatives.md`,
  `creative-detailed-section-3-daily-CTR.md`,
  `creative-detailed-section-4-daily-ROAS.md`,
  `creative-detailed-section-5-daily-creative-performance.md`.

### 2. `list_promotions` 중복 호출 정리 (해당 없음)

- 이 스킬은 애초에 `list_promotions`를 전혀 호출하지 않는다. section-2(Executive Summary)가
  "소재 단위 분석이라 캠페인/매체 차원의 프로모션과 결이 다르다"는 이유로 명시적으로
  `list_promotions`를 부르지 않기로 설계되어 있다(`creative-detailed-section-2-executive-summary.md`
  참고). 다른 어떤 섹션도 이 도구를 쓰지 않으므로 dedup 대상 자체가 없다.

### 3. `chart.umd.min.js` 인라인 방식 변경 (적용함)

- **무엇**: 기존에는 실행 순서 6단계에서 "이 스킬 폴더의 `assets/chart.umd.min.js` 파일을 읽어
  그 내용 전체를 `{CHART_JS_INLINE}` 자리에 그대로 삽입한다"고만 되어 있어, 매 리포트마다
  모델이 208KB(약 5만 토큰)를 응답 텍스트로 재생성해야 했다. `daily-summary`와 동일한 방식으로
  변경: 파일로 저장하는 사본은 저장 폴더에 `chart.umd.min.js`가 이미 있으면 건너뛰고, 없을
  때만 파일 복사/쓰기 도구로 1회 생성한 뒤 `<script src="chart.umd.min.js"></script>`(상대
  경로)로 참조한다. Artifact처럼 CSP로 상대 경로 로드가 막힌 "채팅 내부 표시" 사본만, 그리고
  텍스트 재생성이 아닌 도구(파일 복사·치환)가 없을 때만 최후 수단으로 `{CHART_JS_INLINE}`
  치환을 쓴다.
- **구조적 차이(daily-summary와 다르게 유지한 부분)**: `daily-summary`는 호스트가 Artifact/
  `show_widget`을 지원하지 않으면 "채팅 내부 표시" 사본 자체를 만들지 않도록 조건부로
  바꿨지만, `creative-detailed`는 원래 "완성된 HTML을 두 곳(채팅 내부 표시 + 파일 저장)에
  동시에 낸다 — 하나만 하고 끝내지 않는다"는 요구가 명시적으로 있었다. 이 요구는 성능
  최적화 대상이 아니므로 그대로 유지했고, 각 출력 경로(채팅 내부/파일 저장)가 각자의 제약에
  맞는 최적화 방식(상대 경로 vs 인라인)을 쓰도록만 나눴다.
- **검증**: 상대 경로 `<script src>`가 `file://`에서 CORS 제약 없이 동작한다는 것은
  `daily-summary/CLAUDE.md`에 이미 조사·기록되어 있다(classic script 태그는 ES 모듈/
  `fetch`와 달리 로컬 상대 경로 로딩에 제약이 없음). 같은 근거를 그대로 적용했다.
- **영향받은 파일**: `SKILL.md` (6/7단계, 보고서 골격의 `<head>` 부분).

### 4. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지 (신규 추가)

- **무엇**: SKILL.md에 "MCP 응답을 파일로 저장했다가 다시 Read하지 않는다"는 지침을 새
  "병렬 호출 지침" 섹션 안에 추가했다(기존에는 이 규칙 자체가 없었다).
- **왜**: `daily-summary`와 동일한 이유 — 이 스킬도 서브에이전트를 쓰지 않으므로 중간 파일이
  불필요하다.

### 5. 병렬 호출 지침 프레이밍 (신규 추가, 단 "배치할 게 별로 없다"고 정직하게 기술)

- **무엇**: SKILL.md에 병렬 호출 지침 섹션을 새로 추가했다. 다만 `daily-summary`처럼 "6개
  호출을 한 메시지에 전부 배치한다"는 식의 지침을 그대로 복사하지 않았다 — 위 1번 최적화
  이후 이 스킬의 데이터 호출은 사실상 **2개뿐**이고(소재 데이터 1회 + `get_ad_creative_info`
  1회), 후자는 전자의 결과(ROAS/CTR 랭킹)가 있어야 파라미터를 만들 수 있어 **순차 의존
  관계**다. 3단계("나머지 generic 도구 호출")에 해당하는 신규 호출도 이 스킬에는 없다
  (section-3/4/5가 전부 2단계 응답을 재사용). 따라서 "독립적인 호출을 병렬 배치하라"는
  지침을 넣되, 실제로 배치할 대상이 이 스킬에는 거의 없다는 점을 함께 명시했다 — 없는
  병렬성을 과장해서 서술하지 않기 위함이다.

## 검토했지만 적용하지 않은 항목

- `get_target_progress_v2` 관련 최적화 — 이 스킬은 애초에 `get_target_progress_v2`를 쓰지
  않는다(실행 순서 2단계에 명시). 해당 사항 없음.
- `get_naver_*` 도구 — 이 스킬은 naver 전용 도구를 쓰지 않는다. 해당 사항 없음.
- `get_ad_creative_info` — 이미 여러 소재의 키(`meta` 배열)를 한 번에 받는 설계라 추가로
  통합할 여지가 없다(기존에도 이미 최적).
- 매출/보고서 산출값 자체를 바꾸는 변경은 전혀 하지 않았다 — 모든 변경은 "같은 데이터를
  더 적은 호출로 가져오는" 재배선(rewiring)이며, 각 섹션의 계산·조인·렌더링 로직은
  그대로다.

## 2026-08-09 (같은 날 후속 수정) — 위 1번(`media` 생략 통합) 되돌림 + Bash 집계 예외 추가

바로 위 1번 항목("`media` 생략으로 다중 호출 → 단일 호출 통합")을 **부분적으로 되돌렸다**.
구조적으로 동일한 호출 패턴을 쓰는 `creative-summary`의 실제 Claude Code 프로덕션 실행에서
이 최적화가 역효과를 낸 것이 확인되어, `creative-detailed`도 선제적으로 되돌렸다.

### 1. `get_ad_performance_daily_table`(`group_by:"ad"`) — `media` 생략 → `media="meta"`/`media="airbridge"` 2회 호출로 되돌림

- **무엇**: section-1이 공유 호출하던 `get_ad_performance_daily_table`(`group_by:"ad"`,
  `media` 생략 1회)을 **`media="meta"` 1회 + `media="airbridge"` 1회, 총 2회**로 되돌렸다.
  section-1/3/4/5가 이 2회 호출의 응답을 공유·재사용하는 구조 자체는 그대로 유지했다 —
  달라진 것은 "몇 개의 매체 값을 한 응답에 담아 받는가"뿐이다.
- **왜**: `creative-summary`(동일 플러그인, 구조적으로 동일한 `media` 생략 + `group_by:"ad"`
  호출 패턴)의 실제 프로덕션 실행에서, `media` 생략 응답(7일 윈도우)이 **766,576자**에
  달해 모델이 컨텍스트에 제대로 들고 있을 수 없었다. 그 결과 모델이 거대한 마크다운 표를
  bash heredoc 파일에 수동으로 옮겨 적어가며 소재별 7일 합산(비용/노출/클릭, meta+airbridge를
  `campaign_name`+`asset_group`+`ad_name`으로 조인, 광고비 내림차순 랭킹)을 **직접 손으로**
  계산했고, effort 예산이 부족해지자 일부 합산값을 **"합리적인 근사치로 채워 넣는"** 방식으로
  때웠다 — 이는 명백한 정확성 위반이며(보고서 데이터는 절대 근사치로 채우면 안 된다), 이
  단계에만 약 6분이 소모됐다. 같은 세션에서 별도로 확인한 바, `media="meta"` **단독**
  호출만으로도 `group_by:"ad"` 7일 응답이 132,913자로 이미 크지만, `media` 생략은 여기에
  google/naver 등 이 스킬이 쓰지 않는 매체 행까지 더해 5~6배로 응답을 불려 문제를 악화시켰다.
  `creative-detailed`는 `creative-summary`와 완전히 동일한 호출 패턴(같은 도구, 같은
  `group_by`, 같은 7일 윈도우, 같은 두 매체)을 쓰므로 동일한 문제가 재현될 것으로 판단해
  선제적으로 되돌렸다.
- **영향받은 파일**: `SKILL.md`(실행 순서 2단계, 병렬 호출 지침, 섹션 구성/공통 규칙 설명),
  `creative-detailed-section-1-top-creatives.md`,
  `creative-detailed-section-3-daily-CTR.md`,
  `creative-detailed-section-4-daily-ROAS.md`,
  `creative-detailed-section-5-daily-creative-performance.md`.
- **결과 값 불변**: 두 호출로 나누든 하나로 합치든 응답에 담기는 수치 자체는 동일하다(위 1번
  항목에서 이미 확인된 superset 관계) — 이번 변경은 순전히 "몇 회로, 얼마나 큰 응답을 받는가"
  만 되돌린 것이며 조인·집계·렌더링 로직은 바꾸지 않았다.

### 2. `SKILL.md` "실행 방식 절대 지침"에 Bash 집계 예외 추가 (신규)

- **무엇**: "`.py`/`.js`/`.ipynb` 등 스크립트·노트북 파일을 만들지 않는다"는 기존 절대 지침
  바로 아래에, **파일로 남기지 않는 1회성 Bash 명령**(grep/awk/jq 등)으로 media 필터링·
  `campaign_name`+`asset_group`+`ad_name` 조인·소재별 합산·정렬까지 수행하고 그 결과로 나온
  작은 요약표만 컨텍스트에 남기는 것은 허용된다는 예외를 명시적으로 추가했다.
- **왜**: 위 1번에서 확인된 근본 원인 중 두 번째는 "결정적 집계 도구의 부재"다 — 스크립트
  금지 원칙이 "재사용 가능한 파이프라인 파일을 만들지 말라"는 취지인데, 이것이 "Bash를
  절대 쓰지 말라"로 과도하게 해석되어 모델이 큰 표를 직접 손으로 옮겨 적고 머릿속으로 합산하게
  만들었다(위 사고의 두 번째 근본 원인). `media`를 명시해 응답 크기를 줄여도(위 1번), 소재
  수가 많은 브랜드에서는 여전히 `group_by:"ad"` 응답이 커질 수 있으므로, 이 예외를 명시해
  "응답이 크면 즉석 Bash 명령으로 집계 후 결과만 사용"하는 경로를 남겨둔다. 이 예외는 재사용
  가능한 스크립트 파일을 만드는 것과 다르다 — 결과가 나오면 버려지는 1회성 명령이며, 근사치로
  채우거나 일부만 계산하는 것은 여전히 금지된다.
- **영향받은 파일**: `SKILL.md`("실행 방식 절대 지침" 섹션), 각 데이터 호출 지점에서
  응답이 클 경우를 대비한 안내가 추가된 `creative-detailed-section-1-top-creatives.md`.
