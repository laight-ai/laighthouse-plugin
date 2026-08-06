# Executive-MTD Section 4: 주요 카테고리별 월간 매출액 증감 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/executive-mtd/executive-mtd-section-4-category-mom-highlights.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "kpi_cards",
  "cards": [
    { "label": "{category}", "value": "{CHANGE_LABEL}", "diff_value": {mom_pct} }
  ]
}
```

- `category_mom_highlights` 배열의 각 원소를 위 `cards` 배열의 항목 하나로 매핑한다(카드 개수 =
  선별된 카테고리 수, 최소 3개 ~ 최대 6개).
- `mom_pct > 0`이면 `CHANGE_LABEL = "+{mom_pct}%"`; `mom_pct < 0`이면 `CHANGE_LABEL = "{mom_pct}%"`
  (마이너스 기호 그대로, 예: `-1.6%`). `diff_value`는 `mom_pct` 그대로 **부호 있는 숫자**로 넣어
  `sections.py`의 `_diff_color`가 초록/빨강을 자동 판정하게 한다(양수=초록, 음수=빨강).
- **판단 사항**: "신규"(전월 매출 0) 카테고리는 원본 HTML에서 파랑(`#3b82f6`) 별도 색상을 썼으나,
  docx의 `kpi_cards`는 `diff_value` 부호 기반 초록/빨강 2색만 지원하고 별도 색상 축을 추가할
  수단이 없다. 따라서 신규 카테고리는 `value: "신규"`, `diff_value`는 생략(또는 `null`)하여 기본
  텍스트색(무색)으로 렌더링하고, "신규"라는 텍스트 자체로 구분한다(색상 손실은 텍스트 라벨로
  보완).
- `diff_value`는 반드시 따옴표 없는 숫자로 넣는다(`"diff_value": 27.2`이지 `"diff_value": "27.2"`
  아님) — 문자열이면 `_diff_color`의 `> 0`/`< 0` 비교가 깨진다.
- 특이사항이 하나도 없는(모든 카테고리 `|mom_pct| < 10`이고 카테고리 수 자체가 3개 미만인)
  경우에는 카드 1개(`label: "안내"`, `value: "이번 기간 카테고리별 매출 변동이 두드러지지
  않았습니다"`, `diff_value` 없음)로 대체한다 — 빈 섹션으로 남기지 않는다.
