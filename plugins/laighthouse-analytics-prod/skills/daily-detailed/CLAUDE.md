# daily-detailed 성능 최적화 변경 이력

`daily-summary`에 적용한 최적화(`daily-summary/CLAUDE.md` 참고)를 `daily-detailed`에도 구조가
맞는 범위에서 적용한 작업 기록. 새로운 최적화를 적용할 때마다 이 파일에 **날짜 + 무엇을 + 왜 +
검증 방법**을 추가한다 — 나중에 회귀가 생기면 어떤 변경이 원인인지 추적하기 위함.

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일(또는 최소) 호출 통합

- **section-1(목표 달성 현황)**: 매출 실적 호출(`get_ad_performance_monthly_table`,
  `media="airbridge"`)과 no-budget fallback 소진액(media별 3회 조건부 호출)을 **`media` 생략
  1회 호출**로 통합 — `daily-summary-section-1`에 이미 적용된 것과 완전히 동일한 패턴(이
  스킬의 section-1은 원래 `daily-summary`의 최적화 이전 section-1과 문구까지 거의 동일했다).
  목표 판정 결과를 기다리는 조건부 2차 라운드가 완전히 제거되어, `get_target_progress_v2` ×3과
  같은 배치에서 항상 함께 발사한다.
- **section-3(최근 7일 성과)**: 매체별 4회 호출(google/meta/naver `group_by:"total"` +
  airbridge `group_by:"media"`)을 **`media` 생략 1회 호출**(`group_by:"media"`)로 통합 —
  `daily-summary-section-3`와 동일한 패턴.
- **section-4(캠페인 성과, D-1 vs D-0)**: 매체별 4회 호출(google/meta/naver/airbridge 전부
  `group_by:"campaign"`)을 **`media` 생략 1회 호출**로 완전히 통합 — 네 매체 모두 `group_by`가
  동일해서 daily-summary의 패턴을 그대로 적용할 수 있었다.
- **section-5(광고그룹 및 광고 성과, D-1 vs D-0)**: 4회 호출 중 google/meta/naver
  (`group_by:"ad"`)만 **`media` 생략 1회 호출**로 통합했다. airbridge는 `group_by:"campaign"`
  으로 **다른 group_by**가 필요해서 이 통합 호출에 함께 넣을 수 없다 — `media`를 생략하면
  google/meta/naver/airbridge 전부가 **같은 group_by**로 반환되므로, airbridge까지 포함하려면
  이 섹션에 필요 없는 `group_by:"ad"`(캠페인/광고그룹/광고 단위)로 airbridge를 받게 되어
  캠페인 단위 집계가 깨진다. 따라서 이 섹션만 **2회 호출**(media 생략+`group_by:"ad"` 1회 +
  `media:"airbridge"`+`group_by:"campaign"` 1회)로 남았다 — 4회보다는 줄었지만 daily-summary
  수준의 완전 통합은 구조적으로 불가능하다.
- **왜**: `daily-summary/CLAUDE.md`에서 이미 실측 확인한 대로, `media` 생략 시 백엔드
  (`v2_ad_performance.py`)가 내부적으로 모든 `DataSource`를 순회해 매체별 분리 호출과 동일한
  행을 반환한다 — 이 동작은 브랜드나 report_type에 종속되지 않는 범용 도구 동작이므로
  `daily-detailed`에도 동일하게 적용 가능하다고 판단했다. 결과값이 바뀌지 않는다는 사용자
  전제조건은, `media`가 같은 `group_by`로 통합되는 호출에 한해서만 성립한다는 점을
  section-5에서 확인하고 그 경계를 지켰다.
- **영향받은 파일**: `daily-detailed-section-1-target-achievement.md`,
  `daily-detailed-section-3-daily-performance-7days.md`,
  `daily-detailed-section-4-campaign-performance.md`,
  `daily-detailed-section-5-ad-performance.md`, `SKILL.md`.

### 2. section-3 응답을 section-4/5가 재사용하는 것은 **적용하지 않음** (구조적으로 불가능)

`daily-summary`에서는 section-3의 `media` 생략 응답(7일 범위, `group_by:"media"`)을 section-4/5가
그대로 재사용했지만, `daily-detailed`에서는 이 재사용이 성립하지 않는다:
- section-3은 7일 범위지만 section-4/5는 D-1~D0 이틀 범위다 (날짜 범위는 부분집합 관계가
  맞다).
- 하지만 **`group_by` 단위 자체가 다르다** — section-3은 `group_by:"media"`(매체당 합산 한
  줄)인데, section-4는 `group_by:"campaign"`(캠페인별 행), section-5는 `group_by:"ad"`(광고
  단위 행)가 필요하다. `group_by:"media"` 응답에는 캠페인/광고그룹/광고 차원 자체가 없으므로,
  날짜 범위가 부분집합이어도 section-4/5가 필요로 하는 세부 단위를 section-3 응답에서 뽑아낼
  방법이 없다. 따라서 각 섹션이 독립적으로 호출을 유지한다.

### 3. `list_promotions` 중복 호출 — **적용 대상 없음**

이 스킬은 원래부터 `list_promotions`를 **section-3에서 딱 1회만** 호출하고, section-2
(Executive Summary)는 새 호출 없이 그 응답을 재사용한다. section-4/5는 `list_promotions`를
아예 쓰지 않는다. 즉 통합할 중복 호출이 처음부터 없었다 — `daily-summary`처럼 3회→1회로 줄일
대상이 없다.

### 4. `chart.umd.min.js`(약 208KB) 인라인 방식 변경

`daily-summary`와 동일한 이유·동일한 방식으로 변경했다 — 매 리포트마다 모델이 208KB를
자기 출력 텍스트로 재생성하는 대신, 저장 폴더에 이미 파일이 있으면 건너뛰고 없을 때만 1회
복사한 뒤 `<script src="chart.umd.min.js"></script>` 상대 경로로 참조한다. CSP로 상대 경로
로드가 막힌 호스트(Artifact 등)에서만 `{CHART_JS_INLINE}` 인라인을 최후 수단으로 쓴다.
자세한 안전성 근거(classic `<script src>`의 `file://` CORS 미적용 등)는 `daily-summary/
CLAUDE.md`의 해당 항목을 그대로 따른다 — 이 스킬 전용으로 새로 조사한 내용은 없다.
**영향받은 파일**: `SKILL.md`(6/7단계, 보고서 골격의 `<head>` 부분). 이 스킬은 이미
`assets/chart.umd.min.js`를 갖고 있었으므로 새로 자산을 추가할 필요는 없었다.

### 5. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지

`daily-summary`와 동일한 지침을 SKILL.md에 추가했다 — 이 스킬도 서브에이전트를 쓰지 않으므로
중간 파일 저장이 애초에 불필요하다.

### 6. 병렬 호출 지침 추가 (정확한 프레이밍으로 처음부터 작성)

이 스킬에는 원래 "병렬 호출 지침" 섹션 자체가 없었다(daily-summary는 있었지만 한 번 잘못된
주장을 했다가 같은 날 실측으로 정정한 이력이 있다). 처음부터 `daily-summary`의 **정정된**
프레이밍을 그대로 가져와 작성했다 — 배치는 "턴 오버헤드 제거" 효과만 있고 네트워크 레벨 진짜
동시 실행이 보장되지 않는다는 점을 명시했다. 진짜 속도 개선은 위 1번(호출 총 개수 축소)에서
나온다는 점도 동일하게 서술한다.

## 2026-08-09 (추가) — section-4/5의 `media` 생략 통합 호출을 매체별 개별 호출로 되돌림

**이건 위 1번 최적화의 전면 취소가 아니라 부분 교정이다.** section-1/3(둘 다 `group_by:"media"`
또는 `group_by:"total"`처럼 저카디널리티)의 `media` 생략 통합은 **그대로 유지**한다 — 이번
교정은 오직 **section-4(`group_by:"campaign"`)와 section-5(`group_by:"ad"`)**, 즉 캠페인/광고
단위로 행 수가 늘어날 수 있는 두 섹션에만 적용된다.

- **무엇을 되돌렸나**: section-4는 `media` 생략 1회 호출(google/meta/naver/airbridge 통합)을
  매체별 4회 호출로 되돌렸다. section-5는 google/meta/naver 3매체를 `media` 생략 1회로 묶었던
  것을 매체별 3회 호출로 되돌렸다 — airbridge는 원래부터(이전 최적화 당시에도) `group_by`가
  달라 별도 호출로 유지되고 있었고, 이번에도 그대로 유지된다. 즉 section-5는 2회 → 4회, section-4는
  1회 → 4회로 늘어났다.
- **왜**: `daily-detailed`의 자매 스킬인 `creative-summary`에서 실제 프로덕션 실행 중 회귀가
  관찰됐다 — `group_by:"ad"`에서 `media`를 생략한 7일 범위 응답이 766,576자까지 커져 모델
  컨텍스트에 담을 수 없었고, 모델이 그 큰 마크다운 표를 bash heredoc 파일로 손수 나눠 옮긴 뒤
  7일치 소재별 합산을 **머릿속 추론으로** 수행하다가, 여유 예산이 떨어지자 일부 합산값을
  **어림짐작(근사)** 해버렸다 — 데이터는 절대 추정하지 않는다는 § 데이터 처리 원칙을 위반하는
  실제 사고였다. 같은 세션의 별도 실측으로, `media` 단일 매체("meta")만으로도 `group_by:"ad"`
  7일 응답이 132,913자에 달한다는 것도 확인됐다 — 즉 `media` 생략이 유일한 원인이 아니라
  `group_by:"ad"`/`"campaign"` 자체가 이미 큰 응답을 만들고, `media` 생략은 거기에 불필요한
  매체(예: `ga4`) 행까지 더해 상황을 악화시킨다. `daily-detailed`의 section-4/5는 `creative-summary`
  와 동일한 `group_by:"campaign"`/`"ad"` 계열을 쓰므로 같은 위험이 있다고 판단해 선제적으로
  되돌렸다.
- **함께 추가한 것**: `SKILL.md`의 "실행 방식 절대 지침"(스크립트 파일 생성 금지 원칙) 옆에
  좁은 예외를 추가했다 — `group_by`가 `ad`/`campaign`/`ad-set`인 섹션에서는, MCP 응답을 받은
  즉시 **파일로 남기지 않는 1회성 Bash 명령**(grep/awk/jq 등)으로 매체 필터링·소재/캠페인별
  합산·비용 내림차순 정렬을 수행하고, 그 결과로 나온 작은 요약표만 컨텍스트에 남기도록 허용한다.
  이 예외는 재사용 가능한 파이프라인 스크립트 파일을 만드는 것과 다르다 — 결과가 나오면 버려지는
  즉석 명령이며, 위 프로덕션 사고의 근본 원인(큰 표를 손으로 옮기고 머릿속으로 합산하다 근사치를
  만든 것)을 막기 위한 조치다.
- **영향받지 않는 것**: section-1/3의 `media` 생략 통합, `chart.umd.min.js` 인라인 방식, 병렬
  호출 지침, 스크래치패드 저장 금지 원칙 — 전부 그대로 유지된다.
- **영향받은 파일**: `daily-detailed-section-4-campaign-performance.md`,
  `daily-detailed-section-5-ad-performance.md`, `SKILL.md`.

## 2026-08-09 (추가 2) — 자매 스킬 `creative-detailed` 실제 실행에서 드러난 두 가지 회귀를 되돌림/강화

`daily-detailed`와 같은 호출 형태(`group_by:"ad"`/`"campaign"`, chart.js 인라인)를 쓰는 자매
스킬 `creative-detailed`의 **실제 프로덕션 실행**(2026-08-09)에서 두 가지 문제가 관찰되어,
이 스킬에도 선제적으로 같은 교정을 적용했다.

### 1. `chart.umd.min.js` — "존재 확인 후 1회 복사 + 상대 경로 참조" 방식을 전면 폐기, 항상 인라인으로 복귀

- **무엇을 되돌렸나**: 위 "4. `chart.umd.min.js` 인라인 방식 변경" 항목에서 도입한
  존재-확인/1회-복사/상대경로(`<script src="chart.umd.min.js"></script>`) 분기를 전부
  제거했다. `SKILL.md`의 실행 순서 6단계와 보고서 골격 `<head>`/CDN 경고 절 모두 **호스트와
  무관하게 항상 `{CHART_JS_INLINE}`에 전체 인라인**하는 방식으로 되돌렸다.
- **왜**: `creative-detailed` 실행에서, 리포트가 샌드박스 출력 디렉터리(`/mnt/user-data/outputs/`)에
  저장되었는데 플랫폼 프리뷰가 저장된 HTML과 `chart.umd.min.js`를 **서로 별개의 다운로드
  파일**로 취급했다 — 상대 경로 `<script src>`가 sibling 파일을 로드하지 못해 **모든 차트가
  깨지거나 빈 화면**으로 렌더링됐다. "생애 첫 리포트 1회만 208KB를 다루고 이후는 존재 확인만
  한다"는 상각(amortize) 논리는 맞았지만, 그 전제(같은 폴더의 상대 경로 로드가 항상 성립한다)
  자체가 샌드박스 출력 환경에서는 깨졌다 — 속도 최적화가 정확성(차트가 실제로 보이는 것)보다
  우선할 수 없으므로 원복했다.
- **영향받은 파일**: `SKILL.md`(실행 순서 6단계, 보고서 골격의 CDN 경고 절과 `<head>`).
  CDN 경고 자체(외부 `<script src="https://cdn...">` 금지)는 이 문제와 무관하므로 그대로
  유지했다.

### 2. `group_by`가 `ad`/`campaign`/`ad-set`일 때 Bash 집계 — "해도 됨"에서 "반드시 해야 함"으로 강화

- **무엇을 바꿨나**: 바로 위 "2026-08-09 (추가)" 항목에서 추가한 Bash 집계 **예외/허용**
  문구를 **필수 절차**로 다시 썼다 — "may use Bash" 수준의 허용형 표현을 제거하고, `group_by`가
  `ad`/`campaign`/`ad-set`인 응답을 받으면 반드시 Bash로 전체 행을 정확히 집계해야 하며,
  "훑어보고 나머지는 추정"하는 부분 처리는 절대 금지한다고 명시했다. 또한 Bash 집계 도중
  effort/시간이 부족해지면 눈으로 훑어 근사치로 넘어가지 말고 더 작은 단위(예: 날짜별 분할 후
  합산)로 나눠서라도 집계를 끝까지 완료하도록, 그리고 정확한 계산 없는 순위/합계/TOP-N은
  보고서에 넣지 말고 차라리 "데이터 준비 중"으로 표시하도록 추가했다.
- **왜**: `creative-detailed` 실행에서, 이전의 "Bash를 써도 된다" 허용형 문구가 실제로는
  강제력이 부족했다 — 모델이 Bash로 집계를 시도하다가 "this task is too large for the effort
  budget... I should pivot to... manually scanning the tables directly"라고 판단하고 도중에
  포기한 뒤, 화면에 보이는 텍스트만 훑어 "백여 개가 넘는 광고 조합을 전부 확인하지 못했다"고
  스스로 인정하면서도 어림짐작한 순위/합계를 그대로 보고서에 넣었다 — § 데이터 처리 원칙(절대
  지침)이 금지하는 "값을 스스로 추정/판단"을 정확히 위반한 사례다. 예외를 옵션으로 남겨두면
  effort가 부족할 때 모델이 그 옵션을 포기하는 경로를 선택할 수 있다는 것이 확인되었으므로,
  포기 자체를 막기 위해 필수 절차로 강화했다.
- **영향받은 파일**: `SKILL.md`("실행 방식 절대 지침" 절의 Bash 집계 단락).

## 아직 적용 안 한 후보 (추가 조사/논의 필요)

- `get_target_progress_v2` 3회(media=google/meta/naver) 호출을 1회로 합치는 것 — `daily-summary`
  와 동일한 이유로 보류한다(도구 스키마가 `media`를 필수 enum으로 요구해 생략 불가능, 백엔드
  스키마 변경 필요, 매체별 메시지 포맷 차이로 로직 복잡화 우려). 자세한 내용은
  `daily-summary/CLAUDE.md`의 해당 항목 참고.
- (2026-08-09 위 되돌림으로 무효화됨) section-5의 google/meta/naver 통합 호출과 airbridge
  호출을 더 줄이는 방법 — 애초에 `group_by`가 다르면 하나로 합칠 수 없다는 것이 한계였고,
  이제는 응답 크기 문제로 google/meta/naver 통합 자체도 되돌렸으므로 이 후보는 더 이상 유효하지
  않다. section-4/5는 앞으로도 매체별 개별 호출을 유지한다 — 호출 수를 줄이는 방향의 추가
  최적화는 시도하지 않는다.
