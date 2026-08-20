# Breezm Monthly Section 4: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체 단위로
**전월(M-1)과 당월(M0)**을 비교한다 — Naver Ads / Google Ads / Meta Ads / Organic / Others
5개 항목 고정. 지표는 6개(광고비/CTR/예약 완료/예약 완료 CPA/매출/ROAS, 순서 고정).
⚠️ Organic/Others는 현재 데이터 소스(ELT 광고 성과)에서 제공되지 않아 `-` 행으로 남는다
(아래 매핑 참고).

> ℹ️ 표 HTML과 **파생지표(CTR/CPA/ROAS)·변화량·화살표·색상·M0 매출 내림차순 정렬·행 생성**은
> 전부 템플릿+빌더가 한다 — 모델은 아래 규칙으로 5개 항목의 **월별 원본 수치만** 빌더 입력
> JSON의 `s4.channels`에 넣는다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

section-3가 호출한 `get_ad_performance` 1회(`media` 생략, `time_grain:"month"`,
`group_by:["media"]`, 6개월, `day_offset`) 응답에서 **M-1·M0 두 달 행만 골라 쓴다** —
`day_offset`이 범위 내 모든 월에 균일하게 적용되므로 별도 호출과 값이 완전히 동일하다.
추가 호출 금지.

## 빌더 `s4.channels` 매핑 (5개 항목, M-1/M0 각각)

`media` 차원 값 `Naver`/`Google`/`Meta` 행을 각각 `"Naver Ads"`/`"Google Ads"`/`"Meta Ads"`
항목으로 매핑한다. **`Organic`/`Others`는 현재 데이터 소스에서 제공되지 않는다** — 예전
airbridge `channel` 행이 주던 값이다. 두 항목은 `channels`에 넣지 않거나 두 달 다 `null`로
넣는다(빌더가 `-` 행으로 렌더링) — 다른 값으로 지어 채우지 않는다.

```json
{"channels": [
  {"name": "Naver Ads",
   "m1": {"cost": ..., "impression": ..., "click": ..., "revenue": ..., "reservation": ...},
   "m0": {...}},
  {"name": "Google Ads", ...}, {"name": "Meta Ads", ...},
  {"name": "Organic", "m1": {"revenue": ..., "reservation": ...}, "m0": {...}},
  {"name": "Others", ...}
]}
```

| 필드 | 값 |
|---|---|
| `cost`/`impression`/`click` | 해당 매체 행의 해당 월 `광고비`/`노출`/`클릭` |
| `revenue` | 해당 매체 행의 해당 월 `매출_AB` |
| `reservation` | 해당 매체 행의 해당 월 `예약완료_AB` |
| 월 데이터 자체가 없으면 | 그 월을 `null`로 (빌더가 전부 `-`로 표시, 행 자체는 5개 고정) |

빌더가 처리하는 것 (모델이 계산하지 않는다): CTR = click÷impression×100(노출 0이면 N/A),
CPA = 광고비÷예약 완료(0이면 N/A), ROAS = 매출÷광고비×100(광고비 0이면 N/A), 변화량
(광고비/예약 완료/매출/CPA는 %, CTR/ROAS는 %p 소수 1자리), M-1이 `-`/0이면 변화량 생략
(이 섹션은 s5와 달리 `(-)`를 쓰지 않는다), 색상(증가=빨강, CPA만 감소=빨강, 표시값 0.0은
검정·화살표 없음), M0 매출 내림차순 정렬.

- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중" 카드.
