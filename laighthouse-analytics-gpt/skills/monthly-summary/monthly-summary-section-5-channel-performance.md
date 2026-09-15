# Executive Monthly Section 5: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-summary` (항상 포함). 전월(M-1)과 당월(M0)을 **매체 단위**로 비교한다
— 행은 디스커버리로 받은 `media_list`의 각 매체 + (`has_organic`이면) Organic 한 행 × 광고비/
매출/(전환)/ROAS. 고정 매체 목록·"Others" 행은 없다.

> ℹ️ 표 HTML(`<thead>` 포함)/ROAS 계산/변화량·화살표·색상(네 지표 전부 증가=빨강·감소=파랑·
> 표시값 0.0=검정, M-1이 `-`/0이면 변화량 미표시)/`-` 표기/각주는 전부 템플릿+빌더가 처리한다
> — 모델은 매체별 **원시 수치**만 빌더 입력 JSON의 `s5.rows`에 넣고, 최상위에 `metric_keys`/
> `currency`를 넘긴다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

section-3이 1회 호출한 `get_ad_performance`(`filters` 생략, `time_grain:"month"`,
`group_by:["media"]`, 5개월 전~당월, `day_offset`=target_date.day) 응답에서 전월(M-1)·당월(M0)
두 달치 행만 골라 쓴다 — 필요한 범위(2개월)가 6개월 범위에 항상 포함되므로 별도 호출과 결과가
동일하다. `day_offset`이 이미 적용돼 있어 전월도 당월과 같은 일자까지 자른 동기 비교다.

- `cost`/`revenue`/`conversion`: 해당 매체 행의 해당 월 `metric_keys.cost`/`.revenue`/
  `.conversion` 키 값 — 한 행에 전부 들어있다(별도 조인 없음). `metric_keys`에 `conversion`이
  없으면 행에도 `conversion`을 넣지 않는다(빌더가 컬럼을 숨긴다).

## 행 매핑 (각 월 M-1/M0 각각, 행의 `media` 차원 값 기준)

- **매체 행**: `media_list`의 각 값마다 하나, `name`은 응답 문자열 **그대로**(접미사·번역
  없음). `media_list` 순서를 유지한다.
- **Organic**: `has_organic`일 때만, 마지막 행. `media`가 `null`인 행 — 광고비 없이 매출만
  귀속되는 행이며 정상적으로 조회된다. `cost`는 넣지 않고(광고비 개념 없음, 빌더가 `-`)
  `revenue`/`conversion`만 채운다.
- 디스커버리에 없는 매체를 지어 넣지 않는다. 해당 월에 행이 없는 매체는 `m1`/`m0`을 `{}`로
  둔다(빌더가 `-`).

## 빌더 입력 (매체당 하나, M-1/M0 각각 원본 수치)

```json
"metric_keys": {"cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출_AB", "conversion": "예약완료_AB"},
"currency": "₩",
"s5": { "rows": [
  { "name": "Kakao",
    "m1": { "cost": 1000000, "revenue": 50000000, "conversion": 120 },
    "m0": { "cost": 1100000, "revenue": 52000000, "conversion": 130 } },
  { "name": "TikTok",  "m1": {...}, "m0": {...} },
  { "name": "Organic",
    "m1": { "revenue": 30000000, "conversion": 80 },
    "m0": { "revenue": 28000000, "conversion": 75 } }
] }
```

빌더가 처리하는 규칙(참고 — 재구현 금지): `<thead>` 라벨은 `metric_keys`의 cost/revenue/
conversion 값(ROAS는 고정); ROAS = 매출÷광고비×100; 광고비/매출/전환 변화율은 상대 %(M-1이
0/`-`이면 미표시), ROAS 변화는 %p; 화살표(▲/▼)와 색상(**네 지표 전부 증가=빨강 #dc2626 /
감소=파랑 #2563eb / 표시값 0.0=검정·화살표 없음**); 행은 받은 순서대로 렌더링; `conversion`
역할이 없으면 전환 컬럼 생략. 값이 없는 지표는 `null`로 넘긴다 (0으로 만들지 않는다).

> 🚫 데이터가 비어있으면 `s5` 자체를 빌더 입력에서 뺀다("데이터 준비 중") — 다른 섹션·다른
> 월 값 재사용이나 근사치 대체는 그 숫자가 진짜 쿼리 결과라도 전부 금지다.
