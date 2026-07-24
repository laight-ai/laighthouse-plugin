# Executive-MTD Section 4: 주요 카테고리별 월간 매출액 증감

**report_type:** `executive-mtd` (항상 포함) — mtd(MK)에는 없는 신규 섹션.

이 섹션은 "이번 달 vs 전월" 카테고리별 매출 변동 중 **눈에 띄는(변동률이 큰) 카테고리만** 작은
카드로 보여준다. Monthly report의 `monthly-section-6-category-monthly-comparison.md`가 만드는
그룹 바 차트(전체 카테고리를 다 보여줌)와 달리, executive-mtd는 **표/차트를 통째로 보여주지
않고, MoM 변동률이 큰 카테고리만 선별해 카드로** 보여준다 — 임원이 스크롤 없이 "무엇이 크게
움직였는지"만 바로 보게 하려는 목적이다. (2번 스크린샷 참고 — 카테고리명 + 부호가 있는 %
변동률만 담은 작은 흰 카드 여러 개를 가로로 나열)

---

## 도구 선정 근거 (중요 — 반드시 읽고 넘어갈 것)

> ⚠️ **`get_sku_sales_monthly_table`(범용 GA 아이템 성과 테이블)을 여기 쓰지 않는다.** naver
> 기반 default generator 브랜드(남양유업 등)는 GA 아이템 카탈로그 테이블에 대한 읽기 권한이
> 없어 SQL 권한 오류로 항상 실패한다 (`SELECT command denied ... ga_itemperf_catalog`,
> 2026-07-22 확인 — Monthly report 스킬(`sections/Monthly/monthly-section-6-*.md`) 개발 시
> 이미 검증된 동일한 제약이다). 대신 naver 전용 `get_naver_category_sales`를 이번 달/전월 두 번
> 호출해 카테고리별 매출을 비교한다 — `get_sku_sales_monthly_table`의 "상위 N" 개념만 참고해
> 카드 선별 로직에 반영한다.

## MCP 도구 호출: `get_naver_category_sales` (두 번 호출)

```json
// 1) 이번 달(MTD, target_date까지)
{ "brand_name": "...", "start_date": "이번달 1일", "end_date": "target_date" }
// 2) 전월 동일 기간(전월의 같은 일수만큼)
{ "brand_name": "...", "start_date": "전월 1일", "end_date": "전월 1일 + (target_date의 일 - 1)" }
```

> ⚠️ **executive-mtd는 MTD 보고서이므로, "전월 전체"가 아니라 "전월의 동일 기간(day-of-month
> 매칭)"으로 비교해야 공정한 MoM이 나온다.** 예를 들어 기준일이 2026-03-15면 전월 구간은
> 2026-02-01~02-15다 (2월이 28일이라 15일을 넘지 않으면 그대로 사용; 만약 기준일의 일자가
> 전월의 마지막 날보다 크면 전월 마지막 날로 clamp한다 — 예: 기준일 3/31, 2월은 28일까지이므로
> 전월 구간은 2/1~2/28).

## 필요 데이터 (MCP)
- `curr_items[]`: 이번 달(MTD) 카테고리별 `{ category, sales }` 배열
- `prev_items[]`: 전월 동일 기간 카테고리별 `{ category, sales }` 배열

## 데이터 가공 (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고)

1. 두 배열을 카테고리명으로 매칭해 각 카테고리의 `mom_pct = (curr - prev) / prev × 100`을
   계산한다 (`prev`가 0이면 해당 카테고리는 "신규"로 별도 표시하고 계산에서 제외).
2. `|mom_pct|` 기준 내림차순 정렬한다.
3. **선별 규칙**: `|mom_pct| >= 10`(퍼센트포인트)인 카테고리를 전부 카드로 보여준다.
   - 그런 카테고리가 3개 미만이면, 임계값과 무관하게 `|mom_pct|` 상위 3개까지 채운다 (임원이
     "아무 특이사항도 없다"고 오해하지 않도록 최소 3개는 보여준다).
   - 카드가 6개를 초과하면 상위 6개까지만 보여준다 (레이아웃상 과밀 방지).
4. 위 계산은 전부 기계적 재집계(매칭·나눗셈·정렬)이며 값 자체를 임의로 보정·추정하지 않으므로
   상위 "데이터 처리 원칙"과 충돌하지 않는다.

## 응답 데이터 구조 (가공 후, 렌더링에 쓰는 최종 형태)

```json
{
  "category_mom_highlights": [
    { "category": "기타", "mom_pct": 27.2 },
    { "category": "단백질보충제", "mom_pct": 17.0 },
    { "category": "국내분유", "mom_pct": 5.1 },
    { "category": "커피", "mom_pct": -1.6 }
  ]
}
```

## PPT 섹션

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
  pptx의 `kpi_cards`는 `diff_value` 부호 기반 초록/빨강 2색만 지원하고 별도 색상 축을 추가할
  수단이 없다. 따라서 신규 카테고리는 `value: "신규"`, `diff_value`는 생략(또는 `null`)하여 기본
  텍스트색(무색)으로 렌더링하고, "신규"라는 텍스트 자체로 구분한다(색상 손실은 텍스트 라벨로
  보완).
- `diff_value`는 반드시 따옴표 없는 숫자로 넣는다(`"diff_value": 27.2`이지 `"diff_value": "27.2"`
  아님) — 문자열이면 `_diff_color`의 `> 0`/`< 0` 비교가 깨진다.
- 특이사항이 하나도 없는(모든 카테고리 `|mom_pct| < 10`이고 카테고리 수 자체가 3개 미만인)
  경우에는 카드 1개(`label: "안내"`, `value: "이번 기간 카테고리별 매출 변동이 두드러지지
  않았습니다"`, `diff_value` 없음)로 대체한다 — 빈 섹션으로 남기지 않는다.
