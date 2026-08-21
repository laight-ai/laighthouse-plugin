# Breezm Executive Monthly Section 5: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
전월(M-1)과 당월(M0)을 매체 단위로 비교한다 — Naver Ads / Google Ads / Meta Ads / Organic /
Others **5개 항목 고정** × 광고비/매출/예약 완료/ROAS 4개 지표. ⚠️ Others는 현재 데이터
소스(ELT 광고 성과)에 대응하는 값이 없어 `-` 행으로 남는다. Organic은 `media`가 `null`인
행으로 정상 조회된다(아래 매핑 참고).

> ℹ️ 표 HTML/헤더/정렬(M0 매출 내림차순)/ROAS 계산/변화량·화살표·색상(네 지표 전부
> 증가=빨강·감소=파랑·표시값 0.0=검정, M-1이 `-`/0이면 변화량 미표시)/`-` 표기/각주는 전부
> 템플릿+빌더가 처리한다 — 모델은 항목별 **원시 수치**만 빌더 입력 JSON의 `s5.rows`에 넣는다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

section-3이 1회 호출한 `get_ad_performance`(`media` 생략, `time_grain:"month"`,
`group_by:["media"]`, 5개월 전~당월, `day_offset`=target_date.day) 응답에서 전월(M-1)·당월(M0)
두 달치 행만 골라 쓴다 — 필요한 범위(2개월)가 6개월 범위에 항상 포함되므로 별도 호출과 결과가
동일하다. `day_offset`이 이미 적용돼 있어 전월도 당월과 같은 일자까지 자른 동기 비교다.

## 항목 매핑 (각 월 M-1/M0 각각, 행의 `media` 차원 값 기준)

- **Naver Ads / Google Ads / Meta Ads**: `media`가 `Naver`/`Google`/`Meta`인 행.
- **Organic**: `media`가 `null`인 행 — 광고비 없이 매출만 귀속되는 행이며 정상적으로
  조회된다. `cost`는 `null`로 두고(광고비 개념 없음) `revenue`/`reservation`만 그 행의
  `매출_AB`/`예약완료_AB`로 채운다.
- **Others**: ⚠️ 대응하는 `media` 값이 없다(관찰된 값은 Google/Meta/Naver/`null` 4가지뿐,
  2026-08-21 기준) — 이 항목은 `rows`에 넣지 않는다(빌더가 `-` 행으로 채움). 다른 값으로
  지어 채우지 않는다.

## 빌더 `s5` 필드 — 5개 항목 전부, 순서 무관 (정렬은 빌더가 한다)

```json
{ "rows": [
  { "name": "Naver Ads",
    "m1": { "cost": 1000000, "revenue": 50000000, "reservation": 120 },
    "m0": { "cost": 1100000, "revenue": 52000000, "reservation": 130 } },
  { "name": "Organic",
    "m1": { "cost": null, "revenue": 30000000, "reservation": 80 },
    "m0": { "cost": null, "revenue": 28000000, "reservation": 75 } }
] }
```

| 필드 | 값 |
|---|---|
| `cost` | 해당 매체 행의 그 월 `광고비` |
| `revenue` | 해당 매체 행의 그 월 `매출_AB` |
| `reservation` | 해당 매체 행의 그 월 `예약완료_AB` |

- ROAS(매출 ÷ 광고비 × 100)와 변화량(광고비/매출/예약 %; ROAS %p)은 빌더가 계산한다 — 모델이
  미리 계산해 넣지 않는다. 값이 없는 지표는 `null`로 넘긴다 (0으로 만들지 않는다).
- 데이터가 없어도 5개 항목 자체를 생략하지 않는다 — 값만 `null`로 채운다.
- 데이터가 비어있으면 `s5` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
