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

## 2026-08-09 (추가 2) — 형제 스킬 `creative-detailed` 실행 결과를 근거로 2건 되돌림/강화

### 8. `chart.umd.min.js` 상대 경로 `<script src>` 방식을 다시 항상-인라인으로 되돌림

- **무엇**: 위 3번 항목에서 도입한 "이미 있으면 건너뛴다 → 없을 때만 파일 복사, 저장본은
  `<script src="chart.umd.min.js"></script>` 상대 경로" 방식을 **완전히 제거**하고,
  `chart.umd.min.js`의 내용을 항상 `{CHART_JS_INLINE}`에 인라인하는 원래 방식으로 되돌렸다.
  SKILL.md의 6단계와 「보고서 골격」의 `<head>`/CDN 경고 문단을 모두 수정했다. 외부 CDN
  경고(무관한 내용)는 그대로 유지했다.
- **왜**: 형제 스킬 `creative-detailed`를 2026-08-09에 실제로 구동한 결과, 저장 위치가
  샌드박스 출력 디렉터리(`/mnt/user-data/outputs/`)였는데, 플랫폼 프리뷰가 저장된 HTML과
  `chart.umd.min.js`를 **서로 다른 두 개의 다운로드 가능 파일**로만 보여줬다 — 상대 경로
  `<script src>`가 실제로는 그 사이 파일을 로드하지 못해 **모든 차트가 깨진/빈 화면으로
  렌더링**됐다. `file://` 로컬 환경에서의 상대 경로 가정이 다른 호스트/저장 방식에서는
  깨진다는 것이 실측으로 확인된 셈이다 — 그래서 호스트를 가리지 않고 항상 인라인하는
  안전한 방식으로 되돌렸다.
- **영향받은 파일**: `SKILL.md` (6단계, 「보고서 골격」의 `<head>`/CDN 경고 문단).

### 9. section-5 Bash 집계 "권장"을 "필수"로 강화

- **무엇**: 위 7번 항목에서 추가한 "1회성 Bash 명령으로 집계할 수 있다"는 예외 문구를,
  "`group_by`가 `campaign`/`ad-set`/`ad`면 **반드시** Bash로 집계해야 한다"는 강한 필수
  규칙으로 다시 썼다. Bash 집계 도중 effort/시간이 부족해도 눈으로 훑어보고 넘어가지 말고
  더 작은 단위(예: 날짜별)로 쪼개서 Bash 집계를 끝까지 완료하라는 지침과, 정확한 계산 없이
  만든 순위/합계/TOP-N은 절대 포함하지 말고 차라리 "데이터 준비 중"으로 표시하라는 지침을
  추가했다.
- **왜**: 형제 스킬 `creative-detailed`(`group_by="ad"`, 같은 호출 계열)의 2026-08-09 실제
  실행에서, 7번 항목의 "may use Bash" 수준 문구가 충분히 강하지 않다는 것이 드러났다 —
  모델이 Bash로 파일에 데이터를 옮기기 시작했다가 "이 작업은 effort 예산에 비해 너무
  크다... 매체별로 훑어보는 쪽으로 전환해야겠다"며 중도에 포기하고, "백 개 이상의 광고
  조합을 전부 확인하지는 못했다"고 스스로 인정하면서도 **테이블을 눈으로 훑은 추정치로
  넘어가는 정확성 위반**을 저질렀다. 이는 6번 항목에서 되돌리려 했던 문제와 정확히 같은
  실패 양상이며, "may"(선택적) 문구로는 재발을 막지 못함을 보여준다.
- **영향받은 파일**: `SKILL.md` ("실행 방식 절대 지침" 섹션의 Bash 집계 예외 문단).

## 2026-08-09 (추가 3) — 신규 `get_ad_performance_range_table` 적용 검토 결과: 해당 없음

### 10. section-5를 `get_ad_performance_range_table`로 전환하는 것 검토 — 부적합 판정, 변경하지 않음

- **검토 배경**: 새 MCP 도구 `get_ad_performance_range_table`이 추가됨 — `get_ad_performance_daily_table`/
  `get_ad_performance_monthly_table`과 파라미터는 동일(`brand_name`/`start_date`/`end_date`/
  `group_by`/`media`/`campaign_type`/`limit`/`offset`)하지만, 응답이 날짜/월별 버킷이 아니라
  **지정한 전체 기간을 합산한 차원-그룹당 단일 행**(예: `group_by:"campaign"`이면 캠페인당
  기간 전체 합산 1행)이다. `is_active`는 항상 None. span은 최대 92일.
- **판정: 부적합 — section-5는 변경하지 않았다.** section-5(캠페인 성과 비교, M-1 vs M0)는
  같은 캠페인에 대해 **전월(M-1)과 당월(M0)을 각각 독립적으로 조인·집계**한 뒤 두 값을
  나란히 표시하고 변화량(%, %p)까지 계산하는 섹션이다 — "월별로 분리된 두 개의 합계"가
  핵심 요구사항이다. `get_ad_performance_range_table`은 `start_date`~`end_date`를 하나의
  구간으로 **합산**하므로, M-1 시작일~M0 종료일을 span으로 주면 두 달 값이 하나의 행으로
  뭉개져 M-1/M0을 더 이상 구분할 수 없다(정확히 이 작업 지시문이 경고한 "PER-CAMPAIGN-PER-
  월별 비교가 필요한 경우는 부적합" 케이스에 해당). 두 번(M-1 구간 1회 + M0 구간 1회)
  나눠 부르는 방법도 검토했으나, 그러면 기존 `get_ad_performance_monthly_table` 4회 호출
  대비 얻는 이득이 없다(호출 수가 줄지 않고, `day_offset` 파라미터가 없어 "당월을
  target_date까지만 자르고 전월도 동일 일자까지만 자르는" MTD 동기 비교 로직을 별도로
  직접 구현해야 해 오히려 더 복잡해진다).
- **결론**: section-5의 4회 매체별 `get_ad_performance_monthly_table` 호출(위 6번 항목에서
  `media` 생략 통합을 이미 되돌린 상태)은 그대로 유지한다. `get_ad_performance_range_table`을
  쓰는 변경은 수행하지 않았다.
- **영향받은 파일**: 없음(검토만 수행, 코드/스킬 파일 변경 없음).

## 2026-08-11 — 자매 스킬 `daily-detailed`의 세 가지 개선을 이 스킬의 실제 구조에 맞춰 이식

`daily-detailed`에서 2026-08-11에 적용된 세 가지 개선(조합 단계 중간 파일 금지 강화, 스켈레톤
선(先) 게시를 필수 체크포인트로 승격, D-1/D-0 비교표 계산을 검증된 asset 스크립트로 이전)을
그대로 복사하지 않고 `monthly-detailed`의 실제 파일(§ 실행 방식 절대 지침, § 실행 순서,
section-5의 M-1/M0 비교 스펙)을 확인한 뒤 구조에 맞게 재적용했다. 네 번째 항목(`group_by`가
`campaign`/`ad`인 응답의 호출 수 재검토)은 조사 후 변경하지 않기로 판단했다 — 아래 4번 참고.

### 1. § 실행 방식 절대 지침: "중간 파일 생성 금지"를 섹션 HTML 조합 단계까지 명시적으로 확장

- **무엇**: 기존에는 "이 스킬이 만드는 파일은 오직 최종 보고서 HTML 하나뿐이다"라는 문장이
  있었지만, 이게 데이터 집계 단계에만 적용되는지 섹션 조합 단계에도 적용되는지 명시하지
  않았다. `daily-detailed`의 실제 프로덕션 사고(예외 조항이 조합 단계까지 확장 해석되어
  `section2.html`/`section4_rows.json`/임시 스테이징 HTML 등 여러 중간 파일을 만들다가 최종
  저장 직전 툴호출 제한에 걸림)를 근거로, "이 금지는 데이터 집계 단계뿐 아니라 **섹션 HTML을
  조합하는 단계에도 동일하게 적용된다**"는 문장과 구체적 금지 예시(`section5.html`,
  `section5_rows.json`, 임시 스테이징 HTML)를 추가했다.
- **왜**: `monthly-detailed`도 `daily-detailed`와 동일하게 서브에이전트 없이 오케스트레이터가
  직접 MCP를 호출하고 HTML을 조합하는 구조라, 같은 예외-조항 오독이 그대로 재현될 수 있다.
  실제 사고가 이 스킬에서 발생한 것은 아니지만, 구조가 동일한 자매 스킬에서 이미 확인된
  실패 양상을 선제적으로 막는다.
- **검증 방법**: 다음 `monthly-detailed` 실행에서 최종 저장 HTML 외에 `.html`/`.json` 등의
  Write 호출이 없는지 확인한다.
- **영향받은 파일**: `SKILL.md`(§ 실행 방식 절대 지침).

### 2. § 실행 순서: 스켈레톤 선(先) 게시를 번호 붙은 필수 체크포인트로 승격

- **무엇**: 기존에는 스켈레톤 게시 지침이 § 실행 방식 절대 지침 아래 별도 안내문으로만
  존재했고, 번호 붙은 § 실행 순서 목록에는 포함되지 않았다. 이 안내문을 삭제하고, § 실행
  순서의 2단계(target/achievement 데이터 확보) 직후에 **번호 붙은 3단계 필수 체크포인트**로
  다시 넣었다. 뒤따르는 단계(나머지 데이터 호출 → Executive Summary → HTML 조합 →
  chart.js 인라인 → 렌더링/저장 → 완료 메시지)의 번호를 전부 4~9로 한 칸씩 다시 매기고,
  이를 참조하던 다른 위치(완료 메시지 형식의 "7단계에서 저장한" → "8단계", 보고서 골격의
  "위 6단계 참고" → "위 7단계")도 함께 수정했다. 4단계(나머지 도구 호출)에도 "섹션 데이터가
  준비되는 대로 즉시 골격의 해당 placeholder를 교체·재게시한다"는 문장을 추가했다.
- **왜**: `daily-detailed/CLAUDE.md`가 이미 문서화한 대로, 절차가 "권장" 수준의 별도
  안내문으로만 존재하면 예산이 부족한 실행에서 모델이 가장 먼저 건너뛰는 대상이 된다.
  `monthly-detailed`도 같은 구조(서브에이전트 없음, 5개 섹션 순차 조합)라 같은 위험이
  있다고 판단해 선제적으로 승격했다.
- **검증 방법**: 다음 `monthly-detailed` 실행에서 (a) target/achievement 응답 수신 직후
  Artifact 게시가 실제로 한 번 일어나는지, (b) 이후 섹션 완성 때마다 재게시가 일어나는지
  확인한다.
- **영향받은 파일**: `SKILL.md`(§ 실행 방식 절대 지침, § 실행 순서 2~9단계, § 완료 메시지
  형식·보고서 골격 절의 단계 참조).

### 3. section-5(캠페인 성과 비교, M-1 vs M0)의 계산을 새 asset 스크립트(`assets/monthly_campaign_rows.py`)로 이전

- **조사 결과**: `mtd-detailed-section-7`류의 조인+파생지표+변화율+화살표+색상+필터+정렬+
  `<tr>` HTML 생성 패턴이 이 스킬에도 있는지 확인한 결과, `monthly-detailed-section-5-
  campaign-performance.md`가 정확히 이 패턴이었다 — 다만 비교 기준이 D-1/D-0가 아니라
  **M-1/M0(전월 vs 당월)**이고, ① 캠페인 이름 정확 일치로 월별 독립 조인, ② 6개 파생지표
  (광고비/CTR/예약 완료/예약 완료 CPA/매출/ROAS), ③ M-1 값이 없거나 0이어서 비교가
  불가능하면(daily처럼 변화량 칸을 비우는 게 아니라) **"(-)"를 화살표·색 없이 회색으로
  명시 표시**, ④ 필터 기준 ₩300,000(daily는 ₩10,000)이라는 점이 `daily-detailed`의
  `assets/dxd_table_rows.py`와 달랐다. `daily-detailed`의 스크립트를 그대로 복사하면
  "(-)" 규칙과 필터 기준이 섹션 스펙과 맞지 않으므로, 이 스킬 전용 스크립트를
  `assets/monthly_campaign_rows.py`로 새로 작성했다.
- **무엇**: `assets/monthly_campaign_rows.py`(신규)를 만들어 section-5의 조인·파생지표·
  변화율·화살표·색상·₩300,000 필터·M0 광고비 내림차순 정렬·`<tr>` HTML 생성을 전부 이
  스크립트로 옮겼다. 입력은 `{"m1_month":..., "m0_month":..., "media_rows":[...],
  "airbridge_rows":[...]}`(월별로 google/meta/naver 응답을 합친 리스트 + airbridge 응답
  리스트), 출력은 `[{"search":..., "html":...}, ...]`. `SKILL.md`의 § 실행 방식 절대
  지침에 이 스크립트를 필수로 호출하라는 예외 조항을 추가했고, section-5 파일에 "계산·
  조인·정렬·HTML 생성" 절을 추가해 기존 "필요 데이터" 절은 "계산 명세(참고용)"로
  재규정했다.
- **왜**: `daily-detailed`에서 이미 검증된 해법(`chart.umd.min.js`를 실행 중에 다시 만들지
  않고 파일로 두고 그대로 쓰는 것과 동일한 패턴 — "매번 재생성/재판단하지 말고 이미 있는
  검증된 걸 써라")을, 계산 스펙이 다른 이 섹션에 맞게 새로 작성해 적용했다. 모델이 매번
  월별 조인·파생지표·변화율·색상 로직을 사고 과정에서 손으로 계산하거나 즉석 `.py` 파일을
  만드는 대신, 검증된 스크립트에 데이터만 파이프하면 되도록 했다.
- **검증 방법**: `python3 -m py_compile assets/monthly_campaign_rows.py`로 문법 검사를
  통과했다. 로컬에서 4가지 합성 케이스를 실행해 확인했다: ① 정상 매칭(M-1/M0 둘 다 매체+
  airbridge 데이터 존재, 광고비/CTR/예약 완료/CPA/매출/ROAS 변화율·화살표·색상 정상 계산),
  ② M-1에 캠페인 자체가 없는 신규 캠페인(모든 M-1 셀 "-", 변화량 전부 "(-)" 회색), ③
  분모 0 엣지 케이스(노출 0 → CTR "N/A", 예약 완료 0(M-1/M0 모두 0) → 예약 완료 변화율
  "(-)"로 0-division 회피, revenue 0인 달의 ROAS는 0.0%로 정상 계산), ④ M0 광고비가
  임계값(₩300,000) 이하인 캠페인이 실제로 출력에서 제외되는지 확인 — 4개 케이스 모두
  기대한 대로 동작했고 M0 광고비 내림차순 정렬도 확인했다. Windows 환경을 감안해 stdin/
  stdout에 UTF-8 인코딩을 강제했다(`io.TextIOWrapper(..., encoding="utf-8")`).
- **영향받은 파일**: `assets/monthly_campaign_rows.py`(신규), `SKILL.md`(§ 실행 방식 절대
  지침), `monthly-detailed-section-5-campaign-performance.md`.

### 4. section-5의 매체별 4회 호출을 다시 통합할지 재검토 — 실측 근거 없어 변경하지 않음

- **배경**: `daily-detailed`는 한때 "`creative-summary`에서 `group_by:"ad"` 응답이
  7일 창만으로도 766,576자까지 커진 사례"를 근거로 자신의 section-4(`group_by:"campaign"`)
  까지 매체별 개별 호출로 되돌렸다가, 이후 실제 실행 기록(매체당 2일치 4~14행)을 재확인하고
  `group_by:"campaign"`은 카디널리티가 낮다는 것을 근거로 다시 `media` 생략 1회 호출로
  재통합했다 — `group_by:"ad"`(광고/키워드 단위)의 실측 위험을 `group_by:"campaign"`
  (캠페인 단위)에 근거 없이 확장 적용한 과도한 일반화였다는 것.
- **검토**: `monthly-detailed`의 section-5도 `group_by:"campaign"`을 쓰고, 이 스킬의
  CLAUDE.md 6번 항목(2026-08-09)이 동일한 `creative-summary`의 `group_by:"ad"` 사례를
  근거로 매체별 4회 호출로 되돌린 바 있어, `daily-detailed`와 같은 과도한 일반화가 아닌지
  재검토했다.
- **판정: 변경하지 않는다.** `daily-detailed`가 재통합한 근거는 "실제 실행 기록으로 확인한
  낮은 행 수(매체당 2일치 4~14행)"라는 **실측**이었다. `monthly-detailed`의 section-5는
  이런 실측이 없고, section-5 파일 자체에 이미 "`monthly-detailed`는 월 단위 date span을
  쓰므로 daily 계열 스킬보다 행 수가 더 늘어날 수 있어 이 위험이 더 크다"는 캐비어트가
  적혀 있다 — 캠페인 단위 집계라는 점은 daily의 section-4와 같지만, 조회 범위가 "이틀"이
  아니라 "두 달"이라 그 두 달 사이 생성/교체되는 캠페인 수가 이틀보다 많을 가능성이 실제로
  있다(같은 section-5 파일이 "캠페인 단위에서는 전월 데이터, 특히 airbridge 매출/예약
  쪽이 아예 없는 경우가 매체 단위보다 훨씬 흔하다"고도 명시한다 — 캠페인 turnover가 이미
  관찰된 스킬이다). 실측 근거 없이 호출 수를 낮추지 말라는 원칙에 따라, section-5는 계속
  매체별 4회 호출을 유지한다.
- **영향받은 파일**: 없음(검토만 수행, 코드/스킬 파일 변경 없음).

## 2026-08-11 (추가) — `assets/monthly_campaign_rows.py`가 마크다운 표 원본을 직접 파싱하도록 확장

`daily-detailed`에서 같은 문제(§ `dxd_table_rows.py`가 JSON 행 배열을 요구하는데, 실제
`get_ad_performance_daily_table`은 마크다운 표 문자열을 반환해 "마크다운→JSON 변환" 단계가
누락돼 있던 것)가 발견되어(`daily-detailed/CLAUDE.md` 2026-08-11 (추가 3) 항목 참고),
`get_ad_performance_monthly_table`을 쓰는 이 스킬의 `assets/monthly_campaign_rows.py`에도
동일한 문제가 있는지 확인했다.

- **확인한 사실**: `get_ad_performance_monthly_table`의 도구 스키마 설명도 "Ad performance
  monthly data **as a markdown table**"로 명시되어 있고, 실제로 라이브 호출
  (`brand_name:"breezm"`, `start_month`/`end_month`:"2026-06", `group_by:"campaign"`,
  `media:"google"`)로 원본 응답을 확인한 결과 JSON 행 배열이 아니라 파이프(`|`) 마크다운
  문자열 하나였다 — `daily-detailed`와 완전히 같은 문제.
- **무엇을 바꿨나**: `monthly_campaign_rows.py`에 `parse_markdown_table()`을 추가하고(월간
  응답의 날짜 필드가 `logdate`가 아니라 `month`인 점만 다르게 반영), 새 입력 형태
  `{"markdown": ["<응답1 원본>", ...]}`을 추가했다. `SKILL.md`와
  `monthly-detailed-section-5-campaign-performance.md`의 asset 스크립트 호출 지침을 이
  `markdown` 입력 형태를 권장하는 방식으로 갱신하고, "손으로 옮겨 적지 않는다"/"파서
  스크립트를 새로 만들지 않는다"는 경고를 추가했다.
- **검증 방법**: 실제 라이브 MCP 호출로 받은 원본 마크다운 문자열(google, 2026-06,
  `group_by:"campaign"`)을 그대로 `markdown` 배열에 넣어 실행 — ₩278,991 캠페인(N2.SubK)이
  ₩300,000 필터로 정확히 제외되고, 나머지 3개 캠페인이 M0 광고비 내림차순으로 CTR 값까지
  정확히 나오는 것을 확인했다. M-1 데이터가 없는 상태(이번 테스트는 M0만 제공)에서 모든 M-1
  셀과 변화량이 스펙대로 "-"/"(-)"로 나오는 것도 확인했다.
- **영향받은 파일**: `assets/monthly_campaign_rows.py`, `SKILL.md`(§ 실행 방식 절대 지침),
  `monthly-detailed-section-5-campaign-performance.md`.

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
