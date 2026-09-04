# 브랜드 비종속 보고서 패턴 (전 스킬 공용)

모든 보고서 스킬은 **어떤 브랜드, 어떤 매체, 어떤 지표명**에도 같은 방식으로 동작한다. 스킬
파일에는 브랜드명·매체명·지표 키를 리터럴로 두지 않고, 매 실행 시작에 아래 절차로 알아낸 값을
쓴다. 도구 시그니처는 `mcp-tools.md` 참고.

## 1. 브랜드

사용자가 말한 브랜드명을 모든 호출의 `brand_name`과 제목·파일명에 **그대로** 쓴다.
`get_brand_list`는 서버가 `Unknown brand`로 거절했을 때만 호출한다.

## 2. 디스커버리 호출 (실행당 1회, 다른 호출보다 먼저)

```json
{ "brand_name": "<brand>", "start_date": "<그 스킬이 조회하는 가장 이른 날짜>", "end_date": "target_date",
  "time_grain": "total", "group_by": ["media"], "metrics": [] }
```

- `start_date` = **그 스킬의 모든 섹션이 조회하는 가장 이른 날짜**(예: 일간 스킬은 min(당월 1일,
  target_date-6일), 월간/MTD 스킬은 5개월 전 1일). 보고 기간 시작이 아니다 — 창이 좁으면 앞선
  기간에만 집행된 매체가 `media_list`에서 빠진다.
- 응답 `rows`는 매체당 한 행. 여기서 세 값을 도출한다:
  - `media_list` — `media`가 `null`이 아닌 값들, **응답 문자열 그대로**(순서 유지).
  - `has_organic` — `media: null` 행이 있으면 `true` (미귀속/Organic).
  - `metric_names` — 봉투의 `metrics` 리스트(유효한 지표 키의 유일한 진실).
- 브랜드에 `media` 차원이 없어 호출이 실패하면 `group_by: ["source"]`로 재호출하고 `source`
  값을 `media_list`로 쓴다.
- 이후 매체 필터가 필요하면 `filters: {"media": ["<media_list의 값>"]}` (정확 일치).
  고정 매체 집합(Google/Meta/Naver 등)을 어디에도 가정하지 않는다.

## 3. 지표 역할 해석 (실행당 1회)

보고서 표는 고정 **역할**(cost / impression / click / revenue / 선택 conversion)로 구성된다.
`metric_names`에서 각 역할의 실제 키를 아래 후보 순서로 **정확 일치**시켜 정한다:

| 역할 | 후보(순서대로) |
|---|---|
| cost | `광고비`, `cost`, `spend` |
| impression | `노출`, `impressions`, `impression` |
| click | `클릭`, `clicks`, `click` |
| revenue | `매출_AB`, `매출`, `revenue` |
| conversion | `예약완료_AB`, `예약완료`, `purchases`, `conversions`, `전환` |

- cost/impression/click/revenue 중 하나라도 못 정하면 **한 번의 질문**으로 미해결 역할 전부를
  사용자에게 묻는다(어떤 키를 쓸지).
- conversion을 못 정하면 그 역할은 **없음** — 전환·CPA류 컬럼을 숨긴다(묻지 않음).
- 결과를 `metric_keys` 맵으로 빌더에 넘긴다: `{"cost": "광고비", "impression": "노출",
  "click": "클릭", "revenue": "매출_AB", "conversion": "예약완료_AB"}` (conversion은 있을 때만).
- 비율(ROAS/CTR/CPA 등)은 역할 키의 원자 값 합으로 계산한다 — 서버 비율 지표를 합산하지 않는다.

## 4. 표시명

- 매체 라벨은 ELT 응답 값 **그대로** (`X Ads` 접미사·한국어 매핑 없음).
- Organic 행은 `has_organic`일 때만, 라벨 `"Organic"`. "Others" 행/개념은 없다.

## 5. 월 목표 (`get_target_progress_v2`)

`media`를 생략해 1회 호출하면 naver/google/meta/tiktok 4개 매체 블록이 전부 온다 —
`media_list`와 대소문자 무관 일치하는 블록만 쓰고 나머지는 버린다. 서버는
naver/google/meta/tiktok만 지원한다 — `media_list`의 값이 그 외이면 그 매체는 **목표 없음**
(목표 셀 `-`)으로 처리한다. 매체명을 리터럴로 열거하지 않는다.

## 6. 빌더 입력 (공통 계약)

- `channels`/행: 매체별 행은 `{"name": "<media 값 그대로>", ...역할 키(cost/revenue/conversion
  …)로 된 원본 수치}`를 **디스커버리 순서**로, Organic은 `has_organic`일 때 마지막에 `cost` 없이
  넣는다. 빌더는 받은 행을 그 순서대로 렌더링한다(고정 행 목록 없음).
- `metric_keys`: 3절의 맵. 빌더는 `<th>` 텍스트에 이 값을 쓰고, `conversion`이 없으면 전환·
  CPA 컬럼을 생략한다.
- `currency`: 통화 기호 문자열, 생략 시 `"₩"`. 빌더/템플릿은 리터럴 ₩ 대신 이 값을 쓴다.
- 구현 예시: `skills/daily-summary/assets/build_report.py` (`__S5_THEAD_HTML__`,
  `__CURRENCY__` 토큰).
