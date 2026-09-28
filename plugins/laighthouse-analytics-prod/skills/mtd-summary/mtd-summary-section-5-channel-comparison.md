# Executive MTD Section 5: 매체 성과 비교 (전월 동기 vs 당월)

**report_type:** `mtd-summary` (항상 포함). 전월(M-1)과 당월(M0)을 **매체 단위**로 비교한다 —
행은 디스커버리로 받은 `media_list`의 각 매체 + (`has_organic`이고 매출 있음 모드면) Organic 한
행. 고정 매체 목록·"Others" 행은 없다. **전월은 전체 월이 아니라 당월과 같은 일자까지 자른 동일
기간(1일~target_date.day일) 비교다** — `day_offset`으로 구현되며, 관련 각주는 빌더가 넣는다.

> ℹ️ 표 HTML(`<thead>` 포함)/헤더 월 표기/비율 계산/변화량(%·%p)·화살표·색상/`-` 표기/각주·**모드별
> 컬럼 선택**은 전부 템플릿+빌더(공용 킷)가 한다 — 모델은 매체별 **M-1/M0 역할 원본 수치 전부**를
> 빌더 입력 JSON의 `s5.rows`에 넣고, 최상위에 `metric_keys`/`has_organic`/`currency`를 넘긴다.
>
> | 모드 | 컬럼 |
> |---|---|
> | 매출 있음 | 광고비 · 매출 · (전환) · ROAS |
> | 매출 없음 | 광고비 · 노출 · 클릭 · CTR · CPC · (전환) |

## MCP 호출 없음 — section-3의 공유 응답을 재사용

- 이 섹션은 별도 호출을 하지 않는다 — section-3의 공유 응답(6개월, `filters` 생략,
  `time_grain:"month"`, `group_by:["media"]`, `day_offset`=target_date.day)에서 **전월(M-1)과
  당월(M0) 행만** 골라 쓴다. 같은 `day_offset`이므로 same-day MTD cut 전제가 유지된다.
- `cost`/`impression`/`click`/`revenue`/`conversion`: 해당 매체 행의 해당 월 역할 키 값 — 한 행에
  전부 들어있다(별도 조인 없음). `metric_keys`에 없는 역할(revenue/conversion)은 행에도 넣지
  않는다.

## 행 매핑 (각 월 M-1/M0 각각, 행의 `media` 차원 값 기준)

- **매체 행**: `media_list`의 각 값마다 하나, `name`은 응답 문자열 **그대로**(접미사·번역
  없음). `media_list` 순서를 유지한다.
- **Organic**: `has_organic`이고 매출 있음 모드일 때만, 마지막 행. `media`가 `null`인 행 — 광고비
  없이 매출만 귀속되는 행이며 정상적으로 조회된다. `cost`는 넣지 않고(광고비 개념 없음, 빌더가
  `-`) `revenue`/`conversion`만 채운다.
- 디스커버리에 없는 매체를 지어 넣지 않는다. 해당 월에 행이 없는 매체는 `m1`/`m0`을 `{}`로
  둔다(빌더가 `-`).

## 빌더 입력 (매체당 하나, M-1/M0 각각 원본 수치)

```json
"metric_keys": {"cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>", "revenue": "<revenue 키>", "conversion": "<conversion 키>"},
"has_organic": true,
"currency": "₩",
"s5": { "rows": [
  { "name": "<media 값 1>",
    "m1": { "cost": 5000000, "impression": 420000, "click": 6100, "revenue": 25183500, "conversion": 120 },
    "m0": { "cost": 5100000, "impression": 450000, "click": 6400, "revenue": 26000000, "conversion": 128 } },
  { "name": "<media 값 2>", "m1": {...}, "m0": {...} },
  { "name": "Organic",
    "m1": { "revenue": 9000000, "conversion": 40 },
    "m0": { "revenue": 9500000, "conversion": 42 } }
] }
```

- 값이 없으면 키 생략 또는 `null` — 빌더가 `-`로 표시한다 (0으로 만들지 않는다).
- 빌더가 처리하는 것(참고 — 재구현 금지): `<thead>` 라벨(`metric_keys`의 역할 값, ROAS/CTR/CPC는
  고정), ROAS = 매출÷광고비×100, CTR = 클릭÷노출×100, CPC = 광고비÷클릭, 변화량(금액·개수는 상대 %
  — M-1이 `-`/0이면 미표시, ROAS·CTR은 %p), 화살표(▲/▼)와 색상(**모든 지표 증가=빨강 #dc2626 /
  감소=파랑 #2563eb / 표시값 0.0=검정·화살표 없음** — 반올림된 표시값 기준), 통화·정수·% 포맷, 행은
  받은 순서대로 렌더링, `conversion` 역할이 없으면 전환 컬럼 생략, 매출 없음 모드면 Organic 행 제외,
  고정 각주.
- 데이터가 비어있으면 `s5` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
