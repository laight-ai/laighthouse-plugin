# 목표 달성 현황 카드 (section-1 공용 규칙)

daily/mtd/monthly 스킬의 section-1(목표 달성 현황)이 공유하는 규칙이다. 스킬별 section-1 파일은
**기간**(아래 `{month}`/`{as_of}`/`{start}`/`{end}`)만 정하고 나머지는 이 파일을 따른다.

실적(소진액·매출·노출·클릭)은 전부 `get_ad_performance` 응답의 **광고 매체 행**(`media`
non-null) 역할 키 합이다 — Organic 매출은 넣지 않는다(ROAS는 항상 광고 매체 기준).

> ℹ️ 카드 3장의 HTML·파생 비율·N/A 포맷·각주는 전부 빌더(공용 킷 `s1_grid_html`)가 한다 —
> 모델은 아래 규칙으로 **원본 숫자만** 빌더 입력 JSON의 `s1`에 넣는다. 카드 구성은 모드로 정해진다:
>
> | 모드 | 카드 1 | 카드 2 | 카드 3 |
> |---|---|---|---|
> | 매출 있음 | 예산 대비 소진율 | 목표 매출 대비 달성률 | 실제 ROAS (목표 ROAS) |
> | 매출 없음 | 예산 대비 소진율 | 기간 클릭 (기간 노출) | CTR (CPC) |

## MCP 도구 호출: `get_target_progress_v2` × 1 (전체 매체)

```json
{ "brand_name": "<brand>", "month": "{month}", "as_of_date": "{as_of}" }
```

- **`media`를 생략한다**(= 전체 매체, 응답 헤더 `media: all`). 매체 목록을 순회하지 않는다.
- 응답은 markdown 표(행 cost/revenue/roas × 열 target|actual|progress_ratio). 아래는 전부
  **목표 없음**으로 처리한다(오류 아님, "데이터 준비 중" 아님):
  - `No all budget/target available for {month}.` 한 줄
  - 마트 전제 미충족 안내 한 줄
  - 호출 에러(서버가 아직 `media` enum만 받는 구버전이면 스키마 에러가 난다)
- `actual`/`progress_ratio` 열은 쓰지 않는다 — 목표는 목표가 저장된 매체만 합산되고 실적은 마트
  전체라 범위가 다르다. 실적은 아래 `get_ad_performance`에서만 가져온다.

## MCP 도구 호출: `get_ad_performance` × 1 (기간 실적)

```json
{ "brand_name": "<brand>", "start_date": "{start}", "end_date": "{end}", "time_grain": "month", "group_by": ["media"] }
```

- **`filters` 생략** — 매체당 한 행(`month` 키 포함). `media`가 `null`인 행(Organic)은 합산에서
  뺀다.
- **위 `get_target_progress_v2` 호출과 같은 배치(한 메시지)에서 동시에 발사한다.**
- 스킬이 같은 기간·grain의 `group_by:["media"]` 응답을 이미 다른 섹션용으로 받는다면 그 응답을
  재사용해도 된다(스킬 section-1 파일에 명시된 경우만).

## 빌더 `s1` 필드 (숫자 원본 그대로, 없으면 `null` — 포맷·파생 비율은 빌더가 한다)

| 빌더 필드 | 값 | 모드 |
|---|---|---|
| `목표_예산` | 목표 표 `cost` 행 `target` (0/없음/목표 없음이면 null) | 공통 |
| `소진액` | 광고 매체 행의 cost 키 합 | 공통 |
| `목표_매출` | 목표 표 `revenue` 행 `target` (0/없음이면 null) | 매출 있음 |
| `기간_매출` | 광고 매체 행의 revenue 키 합 | 매출 있음 |
| `기간_노출` | 광고 매체 행의 impression 키 합 | 매출 없음 |
| `기간_클릭` | 광고 매체 행의 click 키 합 | 매출 없음 |

- 소진율·매출 달성률·실제/목표 ROAS·CTR·CPC는 빌더가 위 값으로 계산한다(넣지 않는다).
  Executive Summary가 목표 ROAS가 필요하면 `목표_매출 ÷ 목표_예산 × 100`으로 같은 값을 쓴다.
- 각주는 빌더가 자동으로 단다: 목표가 하나라도 있으면 "목표는 등록 매체 기준 합계" 각주, 전혀
  없으면 "등록된 목표 없음" 각주.
- 응답 rows의 `media` 값이 디스커버리 `media_list`와 다르면 조용히 0을 만들지 말고,
  Executive Summary(`s2`)에 불일치 안내를 추가한다.
