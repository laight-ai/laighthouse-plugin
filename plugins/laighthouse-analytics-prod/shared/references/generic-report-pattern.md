# 브랜드 비종속 보고서 패턴 (전 스킬 공용)

모든 보고서 스킬은 **어떤 브랜드, 어떤 매체, 어떤 지표명**에도 같은 방식으로 동작한다. 스킬
파일에는 브랜드명·매체명·지표 키를 리터럴로 두지 않고, 매 실행 시작에 아래 절차로 알아낸 값을
쓴다. 도구 시그니처는 `mcp-tools.md` 참고. 렌더링 쪽 모드 분기는 전부 공용 킷
(`shared/assets/report_kit.py`/`.js`/`.css`)에 있고, 각 스킬의 `assets/build_report.py`가
그것을 불러 쓴다 — 스킬마다 따로 구현하지 않는다.

## 1. 브랜드

사용자가 말한 브랜드명을 모든 호출의 `brand_name`과 제목·파일명에 **그대로** 쓴다.
`get_brand_list`는 서버가 `Unknown brand`로 거절했을 때만 호출한다.

## 2. 디스커버리 호출 (실행당 1회, 다른 호출보다 먼저)

```json
{ "brand_name": "<brand>", "start_date": "<그 스킬이 조회하는 가장 이른 날짜>", "end_date": "target_date",
  "time_grain": "total", "group_by": ["media"] }
```

- **`metrics`는 생략한다**(전체 지표). ⚠️ `metrics: []`로 부르면 봉투의 `metrics` 목록이 빈
  배열로 와서 지표 키를 알 수 없다(실측). 매체당 한 행이라 전체 지표를 받아도 응답이 작다.
- `start_date` = **그 스킬의 모든 섹션이 조회하는 가장 이른 날짜**(예: 일간 스킬은 min(당월 1일,
  target_date-6일), 월간/MTD 스킬은 5개월 전 1일). 보고 기간 시작이 아니다 — 창이 좁으면 앞선
  기간에만 집행된 매체가 `media_list`에서 빠진다.
- 응답을 **가공 없이 그대로** 스킬의 `assets/discover.py`에 넘긴다(캡처 스텁이면
  `{"json_files": ["<경로>"]}`). 출력:

| 키 | 의미 |
|---|---|
| `media_list` | `media`가 `null`이 아닌 값들, **응답 문자열 그대로**(응답 순서) |
| `has_organic` | `media: null` 행이 있으면 `true` (광고비 없이 매출만 귀속된 Organic) |
| `metric_keys` | 역할 → 실제 지표 키 (3절). `revenue`/`conversion`은 찾았을 때만 들어 있다 |
| `has_revenue` | `metric_keys`에 `revenue`가 있으면 `true` — 없으면 **매출 없음 모드**(7절) |
| `currency` | 광고비 지표의 `metric_units` 값, 없으면 `"₩"` |
| `missing` / `ambiguous` | 사용자에게 물어야 하는 역할 (3절) |
| `sources_of` | 매체별 `source` 값 목록 — `group_by`에 `source`가 함께 있을 때만(소재 스킬) |

- 브랜드에 `media` 차원이 없어 호출이 실패하면 `group_by: ["source"]`로 재호출한다
  (`discover.py`가 `source` 값을 `media_list`로 쓴다).
- 이후 매체 필터가 필요하면 `filters: {"media": ["<media_list의 값>"]}` (정확 일치).
  고정 매체 집합(Google/Meta/Naver 등)을 어디에도 가정하지 않는다.

## 3. 지표 역할 해석 (`discover.py`가 한다 — 참고용 규칙)

보고서 표·차트는 고정 **역할**로 구성된다. 봉투 `metrics`에서 각 역할의 실제 키를 찾는다:

| 역할 | 후보 (대소문자 무시, 순서대로) | 필수 |
|---|---|---|
| cost | `광고비`, `cost`, `spend`, `spending` | 필수 |
| impression | `노출`, `impression`, `impressions`, `imps` | 필수 |
| click | `클릭`, `click`, `clicks` | 필수 |
| revenue | `매출`, `revenue` | 선택 — 없으면 매출 없음 모드 |
| conversion | `전환`, `conversion(s)`, `구매`, `구매수`, `purchase(s)` | 선택 — 없으면 전환 컬럼 생략 |

1. **완전 일치**(대소문자 무시)를 먼저 찾는다.
2. 없으면 **접두 일치** `<후보>_…`를 찾는다 (예: `매출_AB`, `revenue_ga`). 하나면 그 키.
3. 접두 일치 후보가 여럿이면(예: `매출_AB`와 `매출_GA`) `ambiguous`에 들어간다 — conversion은
   revenue 키와 **접미어가 같은 후보**(`매출_AB` → `구매_AB`)가 하나면 그것을 쓰고, 그래도
   여럿이면 묻지 않고 생략한다.
- `missing`(필수 역할 미해결) 또는 `ambiguous`가 비어 있지 않으면 **한 번의 질문**으로 전부
  사용자에게 묻고, 답을 `metric_keys`에 반영한다. 둘 다 비어 있으면 묻지 않는다.
- **revenue를 못 찾는 것은 질문 사유가 아니다** — 매출 없음 모드로 진행한다(7절).
- 결과 `metric_keys` 맵을 모든 asset 스크립트에 **같은 값으로** 넘긴다. 빌더는 `<th>`·범례
  텍스트에 이 값을 그대로 쓴다.
- 비율(ROAS/CTR/CPC/CPA)은 역할 키의 원자 값 합으로 계산한다 — 서버 비율 지표를 합산하지
  않는다(계층 표는 예외: 레벨마다 따로 조회해 서버 값을 그대로 쓴다 — 8절).

## 4. 표시명

- 매체 라벨은 ELT 응답 값 **그대로** (`X Ads` 접미사·한국어 매핑 없음).
- Organic 행은 `has_organic`일 때만, 라벨 `"Organic"`. "Others" 행/개념은 없다(차트는 매체가
  8개를 넘으면 넘친 매체를 "그 외 매체 N개"로 묶는다 — 표에는 전부 나온다).

## 5. 월 목표 (`get_target_progress_v2`)

- **합계 카드(section-1)는 `media`를 생략(= `null`, 전체 매체)하고 1회만 호출한다.** 매체
  목록을 순회하지 않는다. 응답 헤더는 `media: all`.
- 매체별 목표가 꼭 필요한 표(현재 `mtd-detailed` section-6)만 `media_list`의 값을 **그대로**
  넣어 매체마다 호출한다. 서버가 대소문자 무시·한국어 별칭으로 매칭하므로 `.lower()`나 표기
  변환을 하지 않는다.
- 응답 처리:
  - 표(행 cost/revenue/roas × 열 target|actual|progress_ratio): `target > 0`인 행만 목표로 쓴다.
  - `No {media} budget/target available for {month}.` 한 줄 → 목표 없음(오류 아님).
  - 마트 전제 미충족(비용·매출 지표 또는 `media` 차원 없음) 한 줄 메시지 → 목표 없음(오류 아님).
  - 매칭되는 매체가 없으면 0 표가 온다 → target 0 이므로 목표 없음.
- ⚠️ `media: all`의 목표는 **목표가 저장된 매체만** 합산되고, 실적은 마트 전체다. 그래서
  실적(소진액·매출)은 **항상 `get_ad_performance`에서** 광고 매체 행(`media` non-null) 합으로
  가져오고, 목표 도구의 `actual`은 쓰지 않는다. 빌더가 "목표는 등록 매체 기준" 각주를 항상 단다.

## 6. 빌더 입력 (공통 계약)

- `metric_keys`: 3절의 맵. `has_organic`: 2절 값. `currency`: 2절 값.
- 매체별 행은 `{"name": "<media 값 그대로>", ...역할 키(cost/impression/click/revenue/conversion)
  로 된 원본 수치}`를 **디스커버리 순서**로, Organic은 `has_organic`일 때 마지막에 `cost` 없이.
- 표시할 컬럼·계열은 빌더(공용 킷)가 모드에 따라 고른다 — 모델은 **역할 원본 수치를 전부**
  넣고, 모드에 따라 행이나 값을 골라 빼지 않는다(없는 역할은 키 자체를 생략).

## 7. 모드 (공용 킷 `report_kit.Modes`가 판정)

### Organic 있음 / 없음 (`has_organic`)

| 위치 | 있음 | 없음 |
|---|---|---|
| 매체 성과 표 | 마지막에 Organic 행(광고비 `-`) | 행 없음 |
| 매체별 추이 차트 | 매체 계열 + Organic 계열(회색, 맨 위) + 각주 | 매체 계열만 |
| Executive Summary | 오거닉 비중 서술 허용 | 오거닉·전체 매출 대비 광고 매출 언급 금지 |
| ROAS·목표 실적 | **항상 광고 매체 기준**(Organic 매출 제외) | 동일 |

### 매출 있음 / 없음 (`has_revenue`)

| 위치 | 매출 있음 | 매출 없음 |
|---|---|---|
| 목표 카드 | 소진율 / 매출 달성률 / ROAS(목표 대비) | 소진율 / 기간 클릭(노출) / CTR(CPC) |
| 성과 혼합 차트 | 광고비·매출 막대 + ROAS 선 | 클릭 막대 + CTR 선 (광고비·노출·CPC는 툴팁) |
| 매체별 추이 | 매체별 매출 | 매체별 클릭 |
| 매체 성과 표 | 광고비·매출·(전환)·ROAS | 광고비·노출·클릭·CTR·CPC·(전환) |
| Executive Summary | ROAS·매출 중심 | CTR·CPC·클릭 중심 (매출·ROAS 언급 금지) |
| 소재 보고서 | ROAS·CTR 순위 | 클릭·CTR 순위, ROAS 차트 → 클릭 차트 |

- 매출 없음 모드에서는 Organic도 끈다(보여줄 광고 지표가 없다).
- 계층 표(8절)는 모드와 무관하게 봉투의 **모든 지표**를 보여준다.

## 8. 계층 표 (매체 → 캠페인 → 광고그룹 → 광고)

실무 상세 스킬의 캠페인 이하 성과는 공용 킷의 계층 표(`LHKit.treeTable`)로 그린다 — 시작은
매체 단위로 접혀 있고, ▶/▼로 펼치며, 지표 헤더 클릭 정렬(기본 광고비 내림차순), 이름 검색,
지표 컬럼 선택, 자식 50개 단위 "더 보기"를 제공한다. 각 셀은 비교 기간 값 아래에 기준 기간
대비 증감(비율 지표 `%p`, 그 외 `%`, 증가 빨강·감소 파랑)을 보여준다.

- **레벨마다 따로 조회한다** — 비율 지표(CTR/ROAS 등)를 하위 행에서 합산할 수 없으므로, 각
  레벨의 값은 그 레벨 `group_by`로 서버가 계산한 값을 그대로 쓴다. 같은 두 기간을 담는 호출:
  - 매체: `group_by: ["media"]`
  - 캠페인: `group_by: ["media", "campaign_name"]`
  - 광고그룹: `group_by: ["media", "campaign_name", "ad_group_name"]` — 매체마다 `filters`
  - 광고: `group_by: ["media", "campaign_name", "ad_group_name", "ad_name"]` — 매체마다 `filters`
- `metrics`는 **생략**(전체 지표) — 표가 모든 지표를 보여주고 사용자가 컬럼을 고른다.
- 응답(캡처 스텁 경로 포함)을 **전부** 빌더 입력의 `json_files`/`json`에 넘긴다. 빌더가
  `report_kit.build_tree`로 레벨을 판별하고(`group_by` 접두 길이), 기간(`date`/`month` 값)을
  기준·비교로 나누고, 트리를 만든다. 모델은 행을 고르거나 합치지 않는다.
- 광고비 기준 제외(threshold) 규칙은 없다 — 전부 넣고 광고비 순으로 정렬한다.
