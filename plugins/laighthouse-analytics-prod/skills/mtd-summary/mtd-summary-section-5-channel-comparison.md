# Breezm Executive MTD Section 5: 매체 성과 비교 (전월 vs 당월)

**report_type:** `mtd-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 전월(M-1)과
당월(M0)을 **Naver Ads / Google Ads / Meta Ads / Organic / Others 5개 항목 × 광고비/매출/
예약 완료/ROAS 4개 지표**로 비교. **전월은 전체 월이 아니라 당월과 같은 일자까지 자른 동일
기간(1일~target_date.day일) 비교다** — `day_offset`으로 구현되며, 관련 각주는 빌더가 넣는다.
⚠️ Organic/Others는 현재 데이터 소스(ELT 광고 성과)에서 제공되지 않아 `-` 행으로 남는다
(아래 매핑 참고).

> ℹ️ 표 HTML/헤더 월 표기/ROAS 계산/변화량(%·%p)·화살표·색상/정렬/각주는 전부 빌더가 한다 —
> 모델은 아래 규칙으로 항목별 **M-1/M0 원본 수치**만 빌더 입력 JSON의 `s5.channels`에 넣는다.

## MCP 호출 없음 — section-3의 공유 응답을 재사용

- 이 섹션은 별도 호출을 하지 않는다 — section-3의 공유 응답(6개월, `media` 생략,
  `time_grain:"month"`, `group_by:["media"]`, `day_offset`=target_date.day)에서 **전월(M-1)과
  당월(M0) 행만** 골라 쓴다. 같은 `day_offset`이므로 same-day MTD cut 전제가 유지된다.
- 광고비/매출/예약은 해당 매체(`Google`/`Meta`/`Naver`) 행의 해당 월
  `광고비`/`매출_AB`/`예약완료_AB` — 한 행에 전부 들어있다(별도 조인 없음).

## 항목 매핑 (각 월 M-1/M0 각각, 행의 `media` 차원 값 기준)

- **Naver Ads / Google Ads / Meta Ads**: `media`가 `Naver`/`Google`/`Meta`인 행.
- **Organic / Others**: ⚠️ **현재 데이터 소스(ELT 광고 성과)에서 제공되지 않는다** — 예전
  airbridge `channel` 행이 주던 값이다. 두 항목은 `channels`에 넣지 않는다(빌더가 5행
  고정으로 `-` 행을 채운다) — 다른 값으로 지어 채우지 않는다.

## 빌더 `s5.channels` 필드 (M-1/M0 각각, 원본 수치 그대로)

```json
{"channels": [
  {"name": "Naver Ads",
   "m1": {"cost": 5000000, "revenue": 251835000, "reservation": 120},
   "m0": {"cost": 5100000, "revenue": 260000000, "reservation": 128}},
  ...
]}
```

| 필드 | 값 |
|---|---|
| `name` | 5개 항목명 중 하나 (그 외 값은 빌더가 에러) |
| `cost` | 해당 매체 행의 해당 월 `광고비` |
| `revenue` | 해당 매체 행의 해당 월 `매출_AB` |
| `reservation` | 해당 매체 행의 해당 월 `예약완료_AB` |

- 값이 없으면 키 생략 또는 `null` — 빌더가 `-`로 표시한다. 항목 자체가 없으면 배열에서 빼도
  된다(빌더가 5행 고정으로 `-` 행을 채운다).
- 빌더가 처리하는 것: ROAS(매출÷광고비×100, 광고비 `-`/0이면 `-`), M0 매출 내림차순 정렬,
  변화량(광고비/매출/예약은 %, ROAS는 %p — M-1이 `-`/0이면 미표시), 화살표(▲/▼)와 색상
  (**네 지표 전부 증가=빨강 #dc2626 / 감소=파랑 #2563eb / 표시값 0.0=검정·화살표 없음** —
  반올림된 표시값 기준), ₩콤마/정수/% 포맷, 고정 각주 2줄.
- 데이터가 비어있으면 `s5` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
