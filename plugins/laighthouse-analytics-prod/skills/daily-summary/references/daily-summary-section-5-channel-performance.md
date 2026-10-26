# Executive Daily Section 5: 매체별 성과 (D-1 vs D-0)

**report_type:** `daily-summary` (항상 포함). 비교 단위가 캠페인이 아니라 **매체**다 — 행은
디스커버리로 받은 `media_list`의 각 매체 + (`has_organic`이고 매출 있음 모드면) Organic 한 행 (임원이 캠페인
디테일 없이 매체 구조만 훑어보는 섹션 — 행 수가 적어 검색/페이지네이션 없음). 고정 매체
목록·"Others" 행은 없다.

> ℹ️ 표 HTML(`<thead>` 포함)/비율 계산/변화율·화살표·색상(증가=빨강·감소=파랑·무변화=검정,
> 표시값 기준 판정)/통화·%·`-` 포맷·**모드별 컬럼 선택**은 전부 빌더(공용 킷)가 한다 — 모델은
> 매체별 **역할 원본 수치 전부**를 빌더 입력 JSON의 `s5.rows`에 넣고, 최상위에 `metric_keys`/
> `has_organic`/`currency`를 넘긴다.
>
> | 모드 | 컬럼 |
> |---|---|
> | 매출 있음 | 광고비 · 매출 · (전환) · ROAS |
> | 매출 없음 | 광고비 · 노출 · 클릭 · CTR · CPC · (전환) |

## MCP 호출 없음 — section-3의 공유 응답을 재사용

section-3의 공유 응답(`filters` 생략, `time_grain:"day"`, `group_by:["media"]`, 7일) 중 **마지막
이틀**(target_date의 하루 전날 = D-1, target_date = D-0)에 해당하는 행만 쓴다. D-1과 D-0은
합산하지 않고 끝까지 따로 유지한다.

- `cost`/`impression`/`click`/`revenue`/`conversion`: 해당 매체 행의 해당 날짜 역할 키 값 —
  한 행에 전부 들어있다(별도 조인 없음). `metric_keys`에 없는 역할(revenue/conversion)은 행에도
  넣지 않는다.

## 행 매핑

- **매체 행**: `media_list`의 각 값마다 하나, `name`은 응답 문자열 **그대로**(접미사·번역
  없음). `media_list` 순서를 유지한다.
- **Organic**: `has_organic`이고 매출 있음 모드일 때만, 마지막 행. `media`가 `null`인 행 — 광고비 없이 매출만
  귀속되는 행이며 정상적으로 조회된다. `cost`는 넣지 않고(광고비 개념 없음, 빌더가 `-`)
  `revenue`/`conversion`만 채운다.
- 디스커버리에 없는 매체를 지어 넣지 않는다. 해당 날짜에 행이 없는 매체는 `d1`/`d0`을 `{}`로
  둔다(빌더가 `-`).

## 빌더 입력 (매체당 하나, D-1/D-0 각각 원본 수치)

```json
"metric_keys": {"cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>", "revenue": "<revenue 키>", "conversion": "<conversion 키>"},
"has_organic": true,
"currency": "₩",
"s5": { "rows": [
  {"name": "<media 값 1>", "d1": {"cost": 156158, "impression": 52000, "click": 830, "revenue": 7864000, "conversion": 12},
                           "d0": {"cost": 149000, "impression": 50100, "click": 790, "revenue": 6964000, "conversion": 10}},
  {"name": "<media 값 2>", "d1": {...}, "d0": {...}},
  {"name": "Organic", "d1": {"revenue": 20000000, "conversion": 40}, "d0": {...}}
] }
```

빌더가 처리하는 규칙(참고 — 재구현 금지): `<thead>` 라벨은 `metric_keys`의 역할 값(ROAS/CTR/CPC는
고정); ROAS = 매출÷광고비×100, CTR = 클릭÷노출×100, CPC = 광고비÷클릭; 금액·개수 변화율은 상대
%(D-1이 0/`-`이면 미표시), ROAS·CTR 변화는 %p; 화살표(▲/▼)는 원본 부호 기준, 반올림 표시값이 0.0이면
화살표 없이 검정; **모든 지표 증가=빨강(#dc2626)/감소=파랑(#2563eb)** ("감소가 긍정"인 지표
없음); 행은 받은 순서대로 렌더링; `conversion` 역할이 없으면 전환 컬럼 생략; 매출 없음 모드면 Organic 행 제외.

> 🚫 데이터가 비어있으면 `s5` 자체를 빌더 입력에서 뺀다("데이터 준비 중") — 다른 섹션·다른
> 날짜 값 재사용이나 근사치 대체는 그 숫자가 진짜 쿼리 결과라도 전부 금지다.
