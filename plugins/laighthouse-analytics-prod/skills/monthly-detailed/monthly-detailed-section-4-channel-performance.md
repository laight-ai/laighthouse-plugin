# Monthly Section 4: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` (항상 포함). 매체 단위로 **전월(M-1)과 당월(M0)**을
비교한다 — 행은 디스커버리로 받은 `media_list`의 각 매체 + (`has_organic`이고 매출 있음 모드면)
Organic 한 행. 고정 매체 목록·"Others" 행은 없다. 캠페인 이하 세부와 봉투의 나머지 지표는
section-5 계층 표에 있다.

> ℹ️ 표 HTML(`<thead>` 포함)/비율 계산/변화율·화살표·색상(증가=빨강·감소=파랑·무변화=검정,
> 표시값 기준 판정)/통화·%·`-` 포맷·**모드별 컬럼 선택**은 전부 빌더(공용 킷)가 한다 — 모델은
> 매체별 **역할 원본 수치 전부**를 빌더 입력 JSON의 `s4.rows`에 넣고, 최상위에 `metric_keys`/
> `has_organic`/`currency`를 넘긴다.
>
> | 모드 | 컬럼 |
> |---|---|
> | 매출 있음 | 광고비 · 매출 · (전환) · ROAS |
> | 매출 없음 | 광고비 · 노출 · 클릭 · CTR · CPC · (전환) |

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

section-3가 호출한 `get_ad_performance` 1회(`filters`·`metrics` 생략, `time_grain:"month"`,
`group_by:["media"]`, 6개월, `day_offset`) 응답에서 **M-1·M0 두 달 행만 골라 쓴다** —
`day_offset`이 범위 내 모든 월에 균일하게 적용되므로 별도 호출과 값이 완전히 동일하다.
추가 호출 금지.

## 빌더 `s4.rows` 매핑 (매체당 하나, M-1/M0 각각 원본 수치)

- **매체 행**: `media_list`의 각 값마다 하나, `name`은 응답 문자열 **그대로**(접미사·번역
  없음). `media_list` 순서를 유지한다.
- **Organic**: `has_organic`이고 매출 있음 모드일 때만, 마지막 행. `media`가 `null`인 행 — 광고비
  없이 매출만 귀속되는 행이며 정상적으로 조회된다. `cost`/`impression`/`click`은 넣지 않고
  (빌더가 `-`) `revenue`(/`conversion`)만 채운다.
- 디스커버리에 없는 매체를 지어 넣지 않는다. 그 달에 행이 없는 매체는 해당 월을 `{}`로
  둔다(빌더가 `-`).

```json
"metric_keys": {"cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>", "revenue": "<revenue 키>", "conversion": "<conversion 키 — 있을 때만>"},
"has_organic": true,
"currency": "₩",
"s4": {"rows": [
  {"name": "<media 값 1>",
   "m1": {"cost": ..., "impression": ..., "click": ..., "revenue": ..., "conversion": ...},
   "m0": {...}},
  {"name": "<media 값 2>", "m1": {...}, "m0": {...}},
  {"name": "Organic", "m1": {"revenue": ..., "conversion": ...}, "m0": {...}}
]}
```

| 필드 | 값 |
|---|---|
| `cost`/`impression`/`click` | 해당 매체 행의 해당 월 cost/impression/click 키 값 |
| `revenue` | 해당 매체 행의 해당 월 revenue 키 값 — `metric_keys`에 revenue가 없으면 이 키 자체를 넣지 않는다 |
| `conversion` | 해당 매체 행의 해당 월 conversion 키 값 — `metric_keys`에 conversion이 없으면 이 키 자체를 넣지 않는다 |

빌더가 처리하는 것 (모델이 계산하지 않는다): `<thead>` 라벨은 `metric_keys`의 역할 값(ROAS/CTR/
CPC는 고정); ROAS = 매출÷광고비×100, CTR = 클릭÷노출×100, CPC = 광고비÷클릭; 금액·개수 변화율은
상대 %(M-1이 0/`-`이면 미표시), ROAS·CTR 변화는 %p; 표시값 0.0은 검정·화살표 없음; 행은 받은
순서대로; 매출 없음 모드면 Organic 행 제외.

- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중" 카드.
