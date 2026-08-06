# Executive-MTD Section 5: 매체별 성과 비교 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/executive-mtd/executive-mtd-section-5-media-roas-comparison.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "table",
  "heading": "매체별 성과 비교",
  "headers": ["채널", "{prev_period_label} ROAS", "{curr_period_label} ROAS", "변동"],
  "rows": [
    ["{channel_label}", "{prev_roas_fmt}%", "{curr_roas_fmt}%", "{CHANGE_LABEL}"]
  ]
}
```

- `media_roas_comparison.rows` 배열의 각 원소를 위 `rows` 배열의 행 하나로 매핑한다(`change_pp`
  오름차순 정렬 후).
- `CHANGE_LABEL`은 `change_pp > 0`이면 `"+{change_pp}%p"`, `change_pp < 0`이면 `"{change_pp}%p"`
  (마이너스 기호 유지, 예: `-179.7%p`)로 문자열에 미리 부호를 반영해 넣는다 — `table` 섹션은
  `kpi_cards`와 달리 `diff_value` 기반 자동 색상 판정을 지원하지 않으므로(셀 단위 조건부 서식
  없음), 원본 HTML의 `CHANGE_COLOR`(초록/빨강) 강조는 정적 문서에서 표현하지 않고 부호가 담긴
  텍스트만으로 증감 방향을 전달한다.
- `prev_roas`/`curr_roas`는 소수점 첫째자리까지 표시한다 (예: `823.5%`).
- `cost_sum`이 0이라 `roas`가 `null`인 채널은 `rows`에서 해당 행 자체를 제외한다.
- 데이터가 비어있으면 이 섹션 전체를 생략한다(임의로 채우지 않는다).

## 렌더링 규칙
- `rows`는 `change_pp` **오름차순**(가장 나쁜 변화, 즉 가장 큰 음수부터)으로 정렬한다 — 임원이
  가장 먼저 확인해야 할 악화 채널이 표 맨 위에 오도록 한다 (3번 스크린샷과 동일한 정렬).
- `change_pp > 0`이면 `CHANGE_LABEL = "+{change_pp}%p"`; `change_pp < 0`이면
  `CHANGE_LABEL = "{change_pp}%p"` (마이너스 기호 유지, 예: `-179.7%p`).
- `prev_roas`/`curr_roas`는 소수점 첫째자리까지 표시한다 (예: `823.5%`).
- `cost_sum`이 0이라 `roas`가 `null`인 채널은 표에서 해당 행 자체를 제외한다 (0%로 표시하지
  않는다 — 나눗셈 자체가 불가능한 상태이기 때문).
- 데이터가 비어있으면 이 섹션 전체를 생략한다.
