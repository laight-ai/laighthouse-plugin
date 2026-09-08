# Monthly Section 4: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` (항상 포함). 매체 단위로 **전월(M-1)과 당월(M0)**을
비교한다 — 행은 디스커버리로 받은 `media_list`의 각 매체 + (`has_organic`이면) Organic 한 행.
고정 매체 목록·"Others" 행은 없다. 지표 컬럼은 cost/CTR/[conversion/CPA]/revenue/ROAS 순서
고정이며, `metric_keys`에 conversion이 없으면 전환·CPA 두 컬럼이 빠진다.

> ℹ️ 표 HTML(`<thead>` 포함)과 **파생지표(CTR/CPA/ROAS)·변화량·화살표·색상·행 생성**은 전부
> 템플릿+빌더가 한다 — 모델은 아래 규칙으로 매체별 **월별 원본 수치만** 빌더 입력 JSON의
> `s4.channels`에 넣고, 최상위에 `metric_keys`/`currency`를 넘긴다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

section-3가 호출한 `get_ad_performance` 1회(`filters` 생략, `time_grain:"month"`,
`group_by:["media"]`, 6개월, `day_offset`) 응답에서 **M-1·M0 두 달 행만 골라 쓴다** —
`day_offset`이 범위 내 모든 월에 균일하게 적용되므로 별도 호출과 값이 완전히 동일하다.
추가 호출 금지.

## 빌더 `s4.channels` 매핑 (매체당 하나, M-1/M0 각각 원본 수치)

- **매체 행**: `media_list`의 각 값마다 하나, `name`은 응답 문자열 **그대로**(접미사·번역
  없음). `media_list` 순서를 유지한다.
- **Organic**: `has_organic`일 때만, 마지막 행. `media`가 `null`인 행 — 광고비 없이 매출만
  귀속되는 행이며 정상적으로 조회된다. `cost`/`impression`/`click`은 넣지 않고(광고비 개념
  없음 — 빌더가 광고비/CTR/CPA/ROAS를 `-`) `revenue`(/`conversion`)만 채운다.
- 디스커버리에 없는 매체를 지어 넣지 않는다. 그 달에 행이 없는 매체는 해당 월을 `null`로
  둔다(빌더가 전부 `-`).

```json
"metric_keys": {"cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>", "revenue": "<revenue 키>", "conversion": "<conversion 키 — 있을 때만>"},
"currency": "₩",
"s4": {"channels": [
  {"name": "Kakao",
   "m1": {"cost": ..., "impression": ..., "click": ..., "revenue": ..., "conversion": ...},
   "m0": {...}},
  {"name": "TikTok", "m1": {...}, "m0": {...}},
  {"name": "Organic", "m1": {"revenue": ..., "conversion": ...}, "m0": {...}}
]}
```

| 필드 | 값 |
|---|---|
| `cost`/`impression`/`click` | 해당 매체 행의 해당 월 cost/impression/click 키 값 |
| `revenue` | 해당 매체 행의 해당 월 revenue 키 값 |
| `conversion` | 해당 매체 행의 해당 월 conversion 키 값 — `metric_keys`에 conversion이 없으면 이 키 자체를 넣지 않는다 |
| 월 데이터 자체가 없으면 | 그 월을 `null`로 (빌더가 전부 `-`로 표시, 행 자체는 유지) |

빌더가 처리하는 것 (모델이 계산하지 않는다): `<thead>` 라벨은 `metric_keys`의 cost/conversion/
revenue 값(CTR/CPA/ROAS는 고정), CTR = click÷impression×100(노출 0이면 N/A), CPA = 광고비÷
전환(0이면 N/A), ROAS = 매출÷광고비×100(광고비 0이면 N/A), 변화량(광고비/전환/매출/CPA는 %,
CTR/ROAS는 %p 소수 1자리), M-1이 `-`/0이면 변화량 생략(이 섹션은 s5와 달리 `(-)`를 쓰지
않는다), 색상(증가=빨강, CPA만 감소=빨강, 표시값 0.0은 검정·화살표 없음), 행은 받은 순서대로.

- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중" 카드.
