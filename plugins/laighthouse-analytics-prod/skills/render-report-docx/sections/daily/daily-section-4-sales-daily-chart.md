# Daily Section 4: 최근 7일 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

---

## 분기 A: Google/Meta 브랜드

**MCP 도구:** `get_sales_performance_daily` (start_date=week_start, end_date=target_date)

### 필요 데이터
- `sales_daily.labels`: 날짜 레이블 배열 — 예: `["3/26(Thu)", ..., "4/1(Wed)"]`
- `sales_daily.revenue`: 매출 배열 ($)
- `sales_daily.ad_spend`: 광고비 배열 ($)
- `sales_daily.roas`: ROAS 배열 (%)

### DOCX 섹션 (분기 A)

```json
{
  "type": "chart",
  "heading": "Sales campaign: Daily performance in the last 7 days",
  "categories": "{sales_daily.labels}",
  "bar_series": [
    { "name": "Revenue", "values": "{sales_daily.revenue}" },
    { "name": "Ad Spend", "values": "{sales_daily.ad_spend}" }
  ],
  "line_series": { "name": "ROAS", "values": "{sales_daily.roas}" }
}
```

- `categories`는 `sales_daily.labels`(날짜 레이블 배열)를 그대로 넣는다.
- `bar_series`는 매출(`sales_daily.revenue`)과 광고비(`sales_daily.ad_spend`) 두 시리즈,
  `line_series`는 ROAS(`sales_daily.roas`) 한 시리즈다 — 원본 Chart.js 혼합 차트(막대 2개 + 꺾은선
  1개)와 동일 구성(mtd-section-4 패턴과 동일).
- 위 JSON의 문자열 자리(`"{sales_daily.labels}"` 등)는 실제 렌더링 시 그 배열/리스트 값으로 그대로
  치환한다(문자열이 아니라 JSON 배열이 들어간다).

---

## 분기 B: naver 브랜드 ⭐ 신규

**MCP 도구 호출: `get_naver_daily_attributed_sales`**

```json
{ "brand_name": "...", "start_date": "target_date - 6일", "end_date": "target_date" }
```

- naver 전용 MCP 도구. 브랜드 전체(5개 채널 합산) 일별 `ad_cost`/`clicks`/`purchases`/`revenue`를
  반환한다 — GFA VAT 조정 등 채널별 보정이 이미 서버에서 끝난 최종 집계값이다.
- `roas`는 이 스킬이 직접 계산한다: `revenue / ad_cost × 100`.

### 필요 데이터 (MCP)
- `sales_daily.labels`: 날짜 레이블 배열 — 예: `["4/22(수)", ..., "4/28(화)"]` (요일은 이 스킬이
  `logdate`로부터 계산)
- `sales_daily.revenue`: 매출 배열 (원) ← `revenue`
- `sales_daily.ad_spend`: 광고비 배열 (원) ← `ad_cost`
- `sales_daily.roas`: ROAS 배열 (%) ← `revenue / ad_cost × 100`

### DOCX 섹션 (분기 B)

```json
{
  "type": "chart",
  "heading": "최근 7일 성과",
  "categories": "{sales_daily.labels}",
  "bar_series": [
    { "name": "매출", "values": "{sales_daily.revenue}" },
    { "name": "광고비", "values": "{sales_daily.ad_spend}" }
  ],
  "line_series": { "name": "ROAS", "values": "{sales_daily.roas}" }
}
```

- `categories`/`bar_series`/`line_series` 매핑은 분기 A와 동일한 구조(라벨/매출/광고비/ROAS)다.
- **날짜 선택 탭(원본 HTML의 target_date 강조 스트립)은 이 DOCX 섹션에 포함하지 않는다** —
  스크린샷 시절부터 "순수 장식용" + "클릭 시 실제 동작 없음"으로 명시돼 있던 요소이고, 정적
  문서에는 클릭 인터랙션이 존재하지 않으므로 굳이 표로 재현할 실익이 없다는 판단이다(값 자체는
  이미 `categories`의 날짜 레이블에 전부 나타난다). 필요해지면 별도 요구사항으로 표/텍스트 형태를
  추가한다.

### 렌더링 규칙 (분기 B, 참고 — HTML 시절 UI 사양, DOCX 섹션에서는 탭 자체를 렌더링하지 않으므로 적용 안 됨)
- 날짜 탭 셀: `target_date`에 해당하는 셀만 `TAB_BG=#fee2e2`(연한 빨강), `TAB_COLOR=#dc2626`
  (스크린샷의 26(일) 하이라이트 참고 — 실제로는 그날이 "일요일"이라서가 아니라 **report의
  기준일(target_date)이라서** 강조되는 것이니, 요일과 무관하게 target_date 셀만 강조한다).
  나머지 셀은 `TAB_BG=white`, `TAB_COLOR=#374151`.
  ⚠️ 스크린샷에는 이 6일치 탭 아래 실제 내용이 비어 있다 — 클릭 시 무언가를 보여주는 실제
  인터랙션 사양은 확인되지 않았으므로, 이 스킬은 **순수 장식용 날짜 스트립**으로만 렌더링한다
  (클릭 핸들러를 만들지 않는다). 추후 실제 동작이 필요해지면 별도 요구사항으로 추가한다.
