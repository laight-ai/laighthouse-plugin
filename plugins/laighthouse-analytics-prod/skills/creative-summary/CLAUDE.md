# creative-summary 성능 최적화 변경 이력

`daily-summary`에 먼저 적용한 최적화 세트(`daily-summary/CLAUDE.md` 참고)를 `creative-summary`에
구조적으로 적용 가능한 범위에서 이식한 기록.

## 2026-08-11 — `daily-detailed`의 3가지 교정을 구조 확인 후 이식(2개 적용, 1개 신규 asset 스크립트로 대체 적용, 1개는 해당 없음)

자매 스킬 `daily-detailed`에서 2026-08-11에 적용한 세 가지 교정(조합 단계 중간 파일 금지
강화, 스켈레톤 게시를 필수 체크포인트로 승격, D-1/D-0 비교표 계산을 asset 스크립트로 이전)과
호출 수 재검토 1건을, `creative-summary`의 실제 구조를 확인한 뒤 해당되는 범위에서 적용했다.
`creative-detailed`와 자매 관계라 일부는 이미 이 CLAUDE.md의 기존 항목에 선제 반영돼 있었다
(예: Bash 집계 필수화, chart.js 인라인 방식) — 이번엔 그 나머지를 확인했다.

### 1. 적용 — 섹션 HTML 조합 단계까지 "중간 파일 생성 금지" 명시적으로 확장

기존 § 실행 방식 절대 지침은 "이 스킬이 만드는 파일은 오직 최종 보고서 HTML 하나뿐이다"라고
이미 적혀 있었지만, "집계 단계에는 Bash를 써도 된다"는 바로 아래 예외 문구와의 경계가
명시적으로 그어져 있지 않았다 — `daily-detailed`의 실제 프로덕션 사고(예외가 조합 단계까지
확장 해석되어 `section2.html`/`section4_rows.json`/스테이징 HTML 등 여러 중간 파일이
생성됨)와 동일한 오해가 이 스킬에서도 재발할 수 있는 구조였다. § 실행 방식 절대 지침에
"이 금지는 데이터 집계 단계뿐 아니라 섹션 HTML을 조합하는 단계에도 동일하게 적용된다"는
문장과, 금지 예시(섹션별 조각 파일 `section3.html`/`section4.html`, `gen_section.py`류 HTML
생성 스크립트, 중간 스테이징 HTML)를 구체적으로 추가했다.
- **영향받은 파일**: `SKILL.md`(§ 실행 방식 절대 지침).

### 2. 적용 — 스켈레톤 선(先) 게시를 번호 붙은 필수 체크포인트로 승격

이 스킬도 다른 대부분의 형제 스킬처럼 스켈레톤 선(先) 게시가 § 실행 방식 절대 지침 아래
별도 안내문(⏱ 표시)으로만 존재하고, 번호 붙은 § 실행 순서 목록에는 포함되지 않는 구조였다
— `daily-detailed`가 실제로 겪은 "스켈레톤 없이 전체를 다 만든 뒤 한 번에 저장하려다 툴호출
예산 소진" 사고와 같은 위험이 구조적으로 동일하게 존재했다. 안내문을 삭제하고, § 실행
순서의 2단계(소재 데이터 호출) 직후·3단계(나머지 데이터 호출) 이전에 번호 붙은 필수
체크포인트로 다시 넣었다. 뒤따르는 단계 번호를 3~8 → 4~9로 전부 다시 매겼다(나머지 도구
호출, Executive Summary, HTML 조합, chart.js 인라인, 렌더링/저장, 완료 메시지 — 그 내부
순서·내용은 무변경). 4단계(나머지 도구 호출)에 "섹션 데이터가 준비되는 대로 즉시 골격의
해당 placeholder를 교체·재게시한다"는 문장도 추가했다. 이 renumbering으로 영향받은 다른
단계 참조(완료 메시지 형식의 "저장 단계" 참조, 보고서 골격 절의 "chart.js 인라인 단계"
참조)도 함께 갱신했다.
- **영향받은 파일**: `SKILL.md`(§ 실행 방식 절대 지침, § 실행 순서 전체, § 완료 메시지
  형식, § 보고서 골격의 단계 참조).

### 3. 대체 적용 — D-1/D-0류 조인 비교표는 없음, 대신 section-3/4/5의 반복 계산을 `assets/creative_daily_series.py`로 이전

`daily-detailed`의 section-4/5가 쓰는 "D-1 vs D-0 조인+파생지표+변화율+화살표+색상+정렬+
`<tr>` HTML 생성" 패턴은 이 스킬에는 **존재하지 않는다** — creative-summary의 section-4/5는
이틀을 나란히 비교하는 표가 아니라 **7일 라인 차트**(광고비 상위 5개 소재의 일별 CTR/ROAS
추이)이고, HTML도 `<tr>` 행이 아니라 Chart.js 시리즈 배열이다. 따라서 `dxd_table_rows.py`를
그대로 가져다 쓸 수는 없었다.
- **대신 적용한 것**: 이 스킬 고유의 반복적·계산 집약적 섹션을 재검토한 결과, section-3(전체
  소재를 날짜별로 합산해 전체 CTR/ROAS 7일 추이를 내는, **5개로 좁혀지지 않는 열린 집계**)이
  바로 이 스킬 CLAUDE.md의 2026-08-09 (2)/(3) 항목에 기록된 실제 정확도 사고(`group_by:"ad"`
  응답을 손으로 합산하다 근사치를 반영한 사고)와 가장 정확히 같은 종류의 위험을 안고 있는
  단계였다. section-4/5(상위 5개 소재의 exact-match 필터링+날짜별 CTR/ROAS)도 조인 로직이
  section-3과 동일해서 같은 스크립트로 함께 처리할 수 있었다. 신규 asset 스크립트
  `assets/creative_daily_series.py`를 만들어 (a) 전체 소재 날짜별 합산(section-3의
  `overall.ctr_series`/`overall.roas_series`, "메타 응답에 있는 소재만 airbridge 매출을
  조인"하는 규칙 포함)과 (b) 상위 5개 소재의 exact-match 날짜별 시리즈(section-4의
  `top5.ctr_series`, section-5의 `top5.roas_series` — ROAS는 조인 실패/광고비 0일 때 `0`으로
  채우는 section-5 고유 규칙 포함)를 모두 계산하도록 했다. CTR은 응답의 `ctr` 필드(비율/%
  여부가 응답마다 다를 수 있어 혼동 위험이 있던 부분, section-4 파일에 있던 기존 경고문 참고)
  대신 항상 `click÷impression×100`으로 스크립트가 직접 계산해 이 판단 자체를 없앴다.
- **왜 asset 스크립트로 옮겼나(vs. 즉석 Bash)**: section-3의 집계는 소재 수만큼(닫힌 5개가
  아니라 열린 전체) 반복되는 조인+합산이라, 즉석 Bash 명령으로도 처리 가능하지만 매번 로직을
  다시 작성/검산하게 되면 daily-detailed에서 실제로 있었던 "모델이 프로즈로 한 줄씩 손계산"
  실패 모드를 피할 수 없다 — `chart.umd.min.js`를 매번 재생성하지 않고 파일로 두는 것과
  같은 논리로, 이미 검증된 스크립트를 두고 재사용하는 쪽을 택했다.
- **적용하지 않은 부분**: section-1(range_table 응답을 그냥 내림차순 정렬)과 section-4의
  "상위 5개 소재 선정"(하나의 필드로 정렬)은 계산이 단순한 정렬뿐이라 스크립트로 옮기지
  않았다 — 각 섹션 파일에 "스크립트 불필요"로 명시했다.
- **검증 방법**: `python3 -m py_compile assets/creative_daily_series.py`로 문법 확인.
  합성 데이터 3케이스로 로컬 실행 확인 — (1) 정상 매칭(2개 소재, 2일, 메타/airbridge 모두
  매칭), (2) 편측 미매칭(한 소재가 meta에는 있지만 airbridge에 없음 → section-3 전체 매출
  합산에서 제외되고 section-4/5의 해당 소재 ROAS는 0으로 채워짐), (3) 분모 0/데이터 완전
  누락(광고비·노출 0인 날, meta_rows에 그 날짜 행이 전혀 없는 날, top5_keys 중 어떤 날에도
  등장하지 않는 소재) — 세 케이스 모두 overall/top5 시리즈의 null/0 처리가 스펙과 일치함을
  확인했다.
- **영향받은 파일**: `assets/creative_daily_series.py`(신규), `SKILL.md`(§ 실행 방식 절대
  지침에 asset 스크립트 예외 추가), `creative-summary-section-3-daily-creative-total-
  performance.md`, `creative-summary-section-4-daily-CTR.md`,
  `creative-summary-section-5-daily-ROAS.md`.

### 4. 해당 없음 — `group_by:"campaign"`류 media 분리 호출 재검토

`daily-detailed`가 재검토한 대상은 section-4(`group_by:"campaign"`)가 media별로 쪼개져 있던
것을 다시 통합한 것이었다. `creative-summary`에는 `group_by:"campaign"` 호출이 **아예
없다** — section-1/3/4/5 전부 `group_by:"ad"`만 쓰고, 이미 이 CLAUDE.md의 2026-08-09 (2)
항목에서 실측 근거(`group_by:"ad"` 응답이 media 생략 시 76만+자로 폭증)를 갖고 `media`를
명시한 매체별 개별 호출로 확정돼 있다. 낮출 낮은 카디널리티 대상 자체가 없으므로 이 스킬에는
적용하지 않는다(과도한 일반화를 만들지 않기 위해 실측 근거가 없는 `group_by:"ad"` 호출 수를
임의로 줄이지 않았다).

## 2026-08-09 (4) — section-1 랭킹을 `get_ad_performance_range_table`로 전환 (Bash 집계 제거)

`laighthouse-prism`에 신규 MCP 도구 `get_ad_performance_range_table`이 추가됐다 —
`get_ad_performance_daily_table`과 파라미터(`brand_name`/`start_date`/`end_date`/`group_by`/
`media`/`campaign_type`/`limit`/`offset`)는 동일하지만, **날짜별 행이 아니라 구간 전체를
차원-그룹(media/campaign/asset_group/ad_name) 단위로 이미 합산한 1행씩** 돌려준다.
`is_active`는 구간 내 상태 변화 가능성 때문에 항상 비어 있다. 구간은 최대 92일.

- **무엇을 바꿨나**: section-1(최우수 소재, ROAS/CTR 1·2위 선정)이 쓰던
  `get_ad_performance_daily_table` × 2(`media="meta"`/`media="airbridge"`, `group_by:"ad"`,
  최근 7일) 호출을 `get_ad_performance_range_table` × 2(파라미터는 동일)로 바꿨다. section-1이
  필요한 건 처음부터 "7일 전체를 합친 소재별 누적 값"뿐이었으므로, 새 도구가 그 합산을 서버
  쪽에서 대신 해준다 — 응답을 받는 즉시 ROAS/CTR 내림차순으로 정렬만 하면 랭킹이 나온다.
- **왜**: `creative-detailed`(section-1의 원본, `creative-detailed/CLAUDE.md` 참고)의 실제
  프로덕션 실행(2026-08-09)에서, `group_by:"ad"` 응답을 Bash로 집계하다 "effort 예산에 비해
  너무 크다"고 판단해 집계를 중간에 포기하고 눈대중으로 추정한 순위·합계를 그대로 보고서에
  반영한 사고가 확인됐다(아래 "2026-08-09 (3)" 항목 참고). 이 사고의 근본 원인은 "소재별 7일
  합산"이라는 클라이언트 쪽 작업 자체였다 — `get_ad_performance_range_table`은 그 작업을
  아예 제거한다(집계할 날짜별 행 자체가 응답에 없다). 이제 section-1의 랭킹 선정에는 Bash
  집계가 "필수 단계"가 아니라 **적용할 대상이 없는 단계**가 됐다.
  - **영향받은 파일**: `creative-summary-section-1-top-creatives.md`(MCP 도구 호출/필요
    데이터 절), `SKILL.md`(실행 순서 2단계, "실행 방식 절대 지침"의 Bash 집계 필수 문단,
    "병렬 호출 지침"의 총 호출 수, 섹션 구성 설명 문단).
- **무엇이 바뀌지 않았나 (중요)**: section-3(최근 7일 전체 소재 CTR/ROAS 추이)·section-4(일별
  CTR, 광고비 상위 5개)·section-5(일별 ROAS, 광고비 상위 5개)는 **여전히 날짜별(daily) 데이터가
  필요하다** — 7일 트렌드 차트를 그리려면 날짜별 값이 있어야 하는데, `get_ad_performance_range_table`은
  구간을 한 행으로 뭉개버리므로 이 세 섹션에는 원천적으로 맞지 않는다. 그래서 이 세 섹션은
  여전히 `get_ad_performance_daily_table` × 2(`media="meta"`/`media="airbridge"`,
  `group_by:"ad"`, 같은 7일)를 별도로 호출해 공유한다(SKILL.md 실행 순서 2단계의 "2-b"로
  분리). 이 스킬의 전체 MCP 데이터 호출 수는 결과적으로 3회(daily 2회+creative_info 1회) →
  5회(range 2회 + daily 2회 + creative_info 1회)로 늘었다 — 호출 수 자체는 늘었지만, section-1의
  Bash 집계가 완전히 없어지고 section-4/5의 daily 필터링 범위도 아래처럼 줄어든 것이 그
  대가다.
  - **section-4/5의 Bash 집계가 더 단순해진 이유**: 예전에는 section-4가 daily 응답 전체를
    소재별로 합산해서 "광고비 상위 5개"를 직접 뽑아야 했다(열린 랭킹 집계, 소재 수만큼 열려
    있음). 이제는 section-1이 이미 호출한 range_table 응답(소재당 1행, 7일 합산 `cost` 포함)을
    그대로 정렬해서 상위 5개 키를 싸게 얻을 수 있으므로, section-4/5가 daily 응답에 대해 하는
    일은 "이미 알고 있는 정확한 5개 키(`campaign_name`+`asset_group`+`ad_name`)로 7일치 행을
    exact-match 필터링하는 것"(최대 5×7=35행, 닫힌 추출)으로 줄었다 — 여전히 필수·정확한
    Bash 처리이고 근사치는 여전히 금지지만, "전체 소재 랭킹"이 아니라 "5개 키 추출"이라 범위가
    훨씬 좁고 실수할 여지가 적다.
  - **section-3은 이 축소 대상이 아니다**: section-3은 "상위 5개"가 아니라 **모든** 소재를
    날짜별로 합산해야 하므로(전체 CTR/ROAS 추이가 목적), 여전히 daily 응답 전체에 대한 완전한
    집계가 필요하다 — section-4/5처럼 5개로 좁혀지는 예외가 적용되지 않는다.
  - **최종 렌더링 값은 무변경**: 이건 "어떤 도구로 데이터를 가져오고 클라이언트가 얼마나
    일해야 하는가"만 바뀐 메커니즘 변경이다. section-1의 ROAS/CTR 1·2위, section-3의 전체
    CTR/ROAS 추이, section-4/5의 상위 5개 소재 선정 결과와 일별 값은 이전과 동일해야 한다
    (range_table의 소재별 합산 값 = daily_table의 같은 소재 7일 행을 직접 더한 값과 같아야
    정상 — 다음 실제 실행 때 한 번 대조 확인을 권장한다).

## 2026-08-09 (3) — chart.js 상대 경로 참조 되돌림 + Bash 집계 "허용" → "필수"로 강화

같은 날 sibling 스킬 `creative-detailed`를 실제로 실행한 결과, 아래 "2026-08-09 (2)" 항목까지
반영된 상태의 두 가지 최적화가 모두 실전에서 깨지는 것이 확인되어 되돌리거나 강화했다.

- **무엇이 문제였나 (chart.js)**: `creative-detailed`를 샌드박스 출력 디렉터리
  (`/mnt/user-data/outputs/`)에 저장하는 호스트에서 실행했더니, 호스트의 미리보기가 저장된
  HTML과 `chart.umd.min.js`를 **서로 다른 두 개의 다운로드 파일**로 취급했다. 이 형태에서는
  상대 경로 `<script src="chart.umd.min.js"></script>`가 sibling 파일을 로드하지 못해 **모든
  차트가 깨진/빈 캔버스로 렌더링**됐다. "저장 폴더에 파일이 이미 있으면 상대 경로 참조,
  없으면 1회 복사"라는 최적화(아래 "2026-08-09 §3" 참고)는 로컬 `file://` 열람을 전제로 한
  것이었는데, 이 전제가 실제 배포 호스트 환경에는 들어맞지 않았다.
  - **무엇을 되돌렸나**: 상대 경로 `<script src>` 분기를 완전히 제거하고, **항상**
    `{CHART_JS_INLINE}` 자리에 `chart.umd.min.js` 전체 내용을 인라인하는 예전 방식(2026-08-09
    §3 이전 상태)으로 복귀했다. 파일 존재 확인/1회 복사 로직도 함께 제거했다. 외부 CDN
    `<script src>`를 쓰지 않는다는 경고문은 그대로 유지한다(이건 이번 문제와 무관하게 여전히
    유효).
  - **영향받은 파일**: `SKILL.md`(6단계, 보고서 골격 `<head>` 부분).
- **무엇이 문제였나 (Bash 집계)**: 같은 `creative-detailed` 실행에서, `group_by:"ad"` 응답을
  받은 모델이 Bash로 데이터를 파일에 옮겨 집계를 시작했지만, 중간에 "이 작업은 effort 예산에
  비해 너무 크다 → 표를 직접 눈으로 훑는 방식으로 전환해야 한다"고 판단하고 집계를 완료하지
  않은 채 포기했다. 그 결과 "100개 이상의 소재 조합을 전부 확인하지는 못했다"고 스스로 인정
  하면서도, 눈으로 훑어 추정한 순위·합계를 보고서에 그대로 반영했다 — 이는 이 스킬이 원래
  막고자 했던 "근사치를 실제 값처럼 반영"하는 정확도 사고와 동일한 종류의 위반이다. 원인은
  §2(아래) 예외 문구가 "Bash를 쓸 수도 있다"는 **허용**으로만 적혀 있어서, 시간 압박이 오면
  모델이 그 허용을 안 쓰고 대신 손으로 눈대중하는 쪽으로 이탈할 여지를 남겨둔 것이었다.
  - **무엇을 강화했나**: 해당 문구를 "Bash 집계는 선택지"에서 "`group_by:"ad"` 응답을 받으면
    **반드시** 완료해야 하는 필수 단계"로 재작성했다. "이 정도만 훑어보고 나머지는 추정" 같은
    부분 처리를 명시적으로 금지했고, effort가 부족하다고 느껴질 때의 탈출구를 "눈대중으로 넘어가는
    것"이 아니라 "더 작은 단위(예: 날짜별)로 쪼개서 Bash 집계를 끝까지 완료하는 것"으로
    지정했다. 정확한 계산이 끝내 불가능하면 해당 섹션을 "데이터 준비 중" placeholder로
    표시하도록 명시적 escape hatch를 추가했다 — 근사치를 정확한 값처럼 보여주는 것보다 항상
    낫다는 원칙을 문구에 직접 못박았다.
  - **영향받은 파일**: `SKILL.md`("실행 방식 절대 지침" 문단).

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

## 2026-08-11 (추가) — `assets/creative_daily_series.py`가 마크다운 표 원본을 직접 파싱하도록 확장

`daily-detailed`에서 발견된 것과 같은 문제(asset 스크립트가 JSON 행 배열을 요구하는데, 실제
`get_ad_performance_daily_table`은 마크다운 표 문자열을 반환해 "마크다운→JSON 변환" 단계가
문서화되어 있지 않던 것 — `daily-detailed/CLAUDE.md` 2026-08-11 (추가 3) 참고)가
`assets/creative_daily_series.py`에도 그대로 있는지 확인했다.

- **확인한 사실**: `get_ad_performance_daily_table`의 도구 스키마 설명이 "Ad performance
  daily data **as a markdown table**"임을 재확인했고, 실제 라이브 호출(`brand_name:"breezm"`,
  `start_date`/`end_date`:"2026-07-02"~"2026-07-03", `group_by:"ad"`, `media:"meta"`)로 원본
  응답이 JSON이 아니라 파이프(`|`) 마크다운 문자열임을 확인했다.
- **무엇을 바꿨나**: `creative_daily_series.py`에 `parse_markdown_table()`을 추가하고, 새 입력
  형태 `meta_markdown`/`airbridge_markdown`(문자열 또는 문자열 리스트)을 추가했다. 기존
  `meta_rows`/`airbridge_rows`(이미 파싱된 행 객체) 입력도 그대로 지원한다(하위 호환). `SKILL.md`
  와 section-3/4 파일의 asset 스크립트 호출 지침을 `meta_markdown`/`airbridge_markdown`을
  권장하는 방식으로 갱신했다.
- **검증 방법**: 실제 라이브 MCP 호출로 받은 원본 마크다운 문자열(meta, 2026-07-02~03,
  `group_by:"ad"`, 일부 소재)을 `meta_markdown`에 그대로 넣어 실행 — 2026-07-02 CTR
  0.9176...%(수동 계산 click 39÷impression 4250×100과 일치), 2026-07-03 CTR
  0.6999...%도 일치함을 확인했다. 기존 `meta_rows`/`airbridge_rows` 입력 형태에 대한 회귀
  테스트도 재실행해 이상 없음을 확인했다.
- **영향받은 파일**: `assets/creative_daily_series.py`, `SKILL.md`(§ 실행 방식 절대 지침의
  asset 스크립트 예외 문단), `creative-summary-section-3-daily-creative-total-performance.md`,
  `creative-summary-section-4-daily-CTR.md`.

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
