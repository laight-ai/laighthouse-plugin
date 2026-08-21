# Breezm Executive Daily Section 5: 매체별 성과 (D-1 vs D-0)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 비교 단위가
캠페인이 아니라 **매체**다 — Naver Ads / Google Ads / Meta Ads / Organic / Others **5개 행
고정** 표 (임원이 캠페인 디테일 없이 매체 구조만 훑어보는 섹션 — 행 수 고정이라 검색/
페이지네이션 없음).

> ℹ️ 표 HTML/ROAS 계산/변화율·화살표·색상(증가=빨강·감소=파랑·무변화=검정, 표시값 기준 판정)/
> D-0 매출 내림차순 정렬/₩·%·`-` 포맷은 전부 템플릿+빌더가 한다 — 모델은 매체별 **원본 수치**만
> 빌더 입력 JSON의 `s5.rows`에 넣는다.

## MCP 호출 없음 — section-3의 공유 응답을 재사용

section-3의 공유 응답(`media` 생략, `time_grain:"day"`, `group_by:["media"]`, 7일) 중 **마지막
이틀**(target_date의 하루 전날 = D-1, target_date = D-0)에 해당하는 행만 쓴다. D-1과 D-0은
합산하지 않고 끝까지 따로 유지한다.

- `광고비`/`매출`/`예약 완료`: 해당 매체(`Google`/`Meta`/`Naver`) 행의 해당 날짜
  `광고비`/`매출_AB`/`예약완료_AB` — 한 행에 전부 들어있다(별도 조인 없음).

## 5개 항목 매핑

- **Naver Ads / Google Ads / Meta Ads**: `media` 차원 값 `Naver`/`Google`/`Meta` 행.
- **Organic**: `media` 값이 `null`인 행 — 광고비 없이 매출만 귀속되는 행이며 정상적으로
  조회된다(제공 안 되는 게 아니다). `cost`는 비워두고(광고비 개념 없음) `revenue`/
  `reservation`만 그 행의 `매출_AB`/`예약완료_AB`로 채운다.
- **Others**: ⚠️ 대응하는 `media` 값이 없다(관찰된 값은 Google/Meta/Naver/`null` 4가지뿐,
  2026-08-21 기준) — 이 항목은 `rows`에 넣지 않는다(빌더가 `-` 행으로 채움). 다른 값으로
  지어 채우지 않는다.

## 빌더 `s5.rows` (매체당 하나, D-1/D-0 각각 원본 수치)

```json
"s5": { "rows": [
  {"name": "Naver Ads",  "d1": {"cost": 156158, "revenue": 7864000, "reservation": 12},
                         "d0": {"cost": 149000, "revenue": 6964000, "reservation": 10}},
  {"name": "Google Ads", "d1": {...}, "d0": {...}},
  {"name": "Meta Ads",   "d1": {...}, "d0": {...}},
  {"name": "Organic",    "d1": {"revenue": 20000000, "reservation": 40}, "d0": {...}},
  {"name": "Others",     "d1": {...}, "d0": {...}}
] }
```

빌더가 처리하는 규칙(참고 — 재구현 금지): ROAS = 매출÷광고비×100; 광고비/매출/예약 완료
변화율은 상대 %(D-1이 0/`-`이면 미표시), ROAS 변화는 %p; 화살표(▲/▼)는 원본 부호 기준,
반올림 표시값이 0.0이면 화살표 없이 검정; **네 지표 전부 증가=빨강(#dc2626)/감소=파랑
(#2563eb)** ("감소가 긍정"인 지표 없음); D-0 매출 내림차순 정렬; 누락 채널은 `-` 행으로 채워
항상 5행.

> 🚫 데이터가 비어있으면 `s5` 자체를 빌더 입력에서 뺀다("데이터 준비 중") — 다른 섹션·다른
> 날짜 값 재사용이나 근사치 대체는 그 숫자가 진짜 쿼리 결과라도 전부 금지다.
