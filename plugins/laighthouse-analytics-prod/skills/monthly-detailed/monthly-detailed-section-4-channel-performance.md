# Breezm Monthly Section 4: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체 단위로
**전월(M-1)과 당월(M0)**을 비교한다 — Naver Ads / Google Ads / Meta Ads / Organic / Others
5개 항목 고정. 지표는 6개(광고비/CTR/예약 완료/예약 완료 CPA/매출/ROAS, 순서 고정).

> ℹ️ 표 HTML과 **파생지표(CTR/CPA/ROAS)·변화량·화살표·색상·M0 매출 내림차순 정렬·행 생성**은
> 전부 템플릿+빌더가 한다 — 모델은 아래 규칙으로 5개 항목의 **월별 원본 수치만** 빌더 입력
> JSON의 `s4.channels`에 넣는다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

section-3가 호출한 `get_ad_performance_monthly_table` 1회(`media` 생략, `group_by:"media"`,
6개월, `day_offset`) 응답에서 **M-1·M0 두 달 행만 골라 쓴다** — `day_offset`이 범위 내 모든
월에 균일하게 적용되므로 별도 호출과 값이 완전히 동일하다. 추가 호출 금지.

## 빌더 `s4.channels` 매핑 (5개 항목, M-1/M0 각각)

각 월의 airbridge 행을 `channel` 값으로 분류한다: `"Naver Ads"`/`"Google Ads"`/`"Meta Ads"`/
`"Organic"` 정확 일치, **그 외 모든 channel 값은 전부 Others로 합산**(조용히 버리지 않는다).

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
| `cost`/`impression`/`click` | Naver/Google/Meta Ads만 — 대응하는 매체 행(naver/google/meta)의 해당 월 값. **Organic/Others는 이 세 키를 아예 넣지 않는다**(광고비 개념 없음 → 빌더가 광고비/CTR/CPA/ROAS를 `-`로 표시) |
| `revenue` | 해당 항목으로 분류된 airbridge 행(들)의 `airbridge_revenue` 합 |
| `reservation` | 해당 항목으로 분류된 airbridge 행(들)의 `reservation` 합 |
| 월 데이터 자체가 없으면 | 그 월을 `null`로 (빌더가 전부 `-`로 표시, 행 자체는 5개 고정) |

빌더가 처리하는 것 (모델이 계산하지 않는다): CTR = click÷impression×100(노출 0이면 N/A),
CPA = 광고비÷예약 완료(0이면 N/A), ROAS = 매출÷광고비×100(광고비 0이면 N/A), 변화량
(광고비/예약 완료/매출/CPA는 %, CTR/ROAS는 %p 소수 1자리), M-1이 `-`/0이면 변화량 생략
(이 섹션은 s5와 달리 `(-)`를 쓰지 않는다), 색상(증가=빨강, CPA만 감소=빨강, 표시값 0.0은
검정·화살표 없음), M0 매출 내림차순 정렬.

- ⚠️ `campaign-type` 금지.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중" 카드.
