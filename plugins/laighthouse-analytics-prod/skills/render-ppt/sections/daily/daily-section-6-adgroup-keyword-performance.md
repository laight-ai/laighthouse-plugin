# Daily Section 6: 광고 그룹 및 키워드 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

⚠️ **이 파일은 기존 "daily-section-7-asset-group-table.md"를 대체한다.** 번호가 하나 당겨졌고
(옛 section 5 DTC Revenue 삭제로), naver 분기는 **4단계 트리(채널→캠페인→광고그룹→키워드) →
2단계 트리(광고그룹→키워드)**로 축소 재설계되었다 — 채널/캠페인 레벨은 이제
daily-section-5(캠페인 성과)가 전담하므로, 이 섹션은 그보다 한 단계 더 깊은 광고그룹/키워드
드릴다운만 담당한다.

---

## 분기 A: Google/Meta 브랜드 (변경 없음)

⚠️ "Asset Group"은 Google Performance Max 캠페인 전용 개념이라 naver에는 대응 개념이 없고,
PMax는 키워드 타겟팅 자체가 없는 상품이라 "키워드" 열은 이 분기에는 적용되지 않는다 (에셋그룹
레벨까지만 존재).

**MCP 도구:** `get_sales_by_asset_group_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

### 필요 데이터
- `sales_by_asset_group`: 에셋그룹 배열
  ```json
  [
    { "media": "Google Ads", "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "asset_group": "CITRUS Kiwi overlay pack assets", "impression": 509, "click": 15, "ctr": 2.95,
      "cost": 10, "revenue": 0 }
  ]
  ```
  ※ ROAS 컬럼 없음 (이미지 참조)

### PPT 섹션 (분기 A)

```json
{
  "type": "table",
  "heading": "Performance by Asset group",
  "headers": ["Media", "Campaign", "Asset Group", "Impression", "Click", "CTR (%)", "Cost ($)", "Revenue ($)"],
  "rows": [
    ["{media}", "{campaign}", "{asset_group}", "{impression_fmt}", "{click_fmt}", "{ctr}", "{cost_fmt}", "{revenue_fmt}"]
  ]
}
```

`rows`에는 `sales_by_asset_group` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로 넣는다
(검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한 표에 다 낸다). ROAS
컬럼은 원본 그대로 없음.

### 렌더링 규칙 (분기 A)
- 금액/노출/클릭 필드는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.

---

## 분기 B: naver 브랜드 ⭐ 재설계 (4단계 → 광고그룹·키워드 2단계 트리)

"광고그룹" 행 앞의 ▸ 아이콘을 누르면 그 그룹에 속한 키워드들이 펼쳐진다. daily-section-5(캠페인
성과)에서 이미 캠페인 단위를 다루므로, 여기서는 각 광고그룹이 어느 캠페인/채널에 속하는지를
**맨 왼쪽 "채널 / 캠페인" 컬럼**으로만 보여주고(2026-07-23: 참고용 표시일 뿐이지만 시인성을
위해 최좌측으로 이동함) 트리 자체는 광고그룹→키워드 2단계로 유지한다.

### MCP 도구 호출: `get_naver_sa_performance_daily` (동일 날짜로 2회 호출, `group_by`만 다름)

```json
// 1) 광고그룹 단위
{ "brand_name": "...", "start_date": "target_date", "end_date": "target_date", "group_by": "ad-group" }
// 2) 키워드 단위
{ "brand_name": "...", "start_date": "target_date", "end_date": "target_date", "group_by": "keyword" }
```

> ⚠️ **`get_naver_group_performance`/`get_naver_keyword_performance`(사전 집계 도구)를 여기 쓰지
> 않는다** — 이 도구들은 그룹/키워드명만 반환하고 **어느 광고그룹에 속하는지 연결 정보가 없다**
> (`get_naver_keyword_performance` 실제 호출 결과 확인, 2026-07-23: `keyword`/`impressions`/
> `clicks`/`ad_cost`/`cpc`/`ctr`/`cpm`/`purchases`/`revenue`/`roas`만 있고 `group_name`/
> `campaign_name` 필드 자체가 없음). 이 섹션처럼 **키워드를 소속 광고그룹 아래에 묶어서** 보여줘야
> 하는 트리에는 쓸 수 없다. 대신 원본 소스인 `get_naver_sa_performance_daily`를 `group_by`만
> 바꿔 호출한다 — 이 도구는 `ad-group`/`keyword` 레벨 응답 모두에 `nvr_media_type`(채널) +
> `campaign_name`(캠페인) + `group_name`(광고그룹, 키워드 레벨에서도 함께 옴)을 항상 반환하므로
> 부모-자식 매칭이 가능하다 (2026-07-22 실제 호출로 확인).
> 응답의 `ctr`/`cpc`/`cvr`/`roas` 필드는 이 레벨 호출에서 전부 `null`로 온다 — 이 스킬이
> `imp`/`click`/`cost_exc_vat`/`gross_conv_cnt`/`gross_conv_amnt`로부터 직접 계산한다.

### 데이터 가공 (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고)

1. **키워드 레벨** 원본에서 `term == "-"`인 행은 제거한다 (키워드 미지정 매칭 트래픽).
2. **키워드 노드**를 `(nvr_media_type, campaign_name, group_name)`으로 그룹핑해, 같은 키를 가진
   **광고그룹 노드**(1번 호출 응답)의 자식으로 붙인다.
3. 각 노드(광고그룹/키워드 모두)에서 비율 지표를 계산한다:
   - `ctr = click / imp × 100`
   - `cpc = cost_exc_vat / click` (click이 0이면 `null`)
   - `cpm = cost_exc_vat / imp × 1000`
   - `roas = gross_conv_amnt / cost_exc_vat × 100` (cost가 0이면 `null`)
   - `광고비 = cost_exc_vat`, `구매건수 = gross_conv_cnt`, `매출 = gross_conv_amnt` 그대로.
4. `nvr_media_type` → 표시 라벨: `BRS`→네이버 브랜드검색, `PLINK`→네이버 파워링크,
   `NVSHOP`→네이버 쇼핑검색.
5. ⚠️ **`ad_cost`(광고비)가 10,000원 미만인 행은 표에서 제외한다** (2026-07-23 추가) — 광고그룹
   노드와 키워드 노드 각각에 독립적으로 적용한다 (부모 그룹이 10,000원 이상이어도 특정 키워드가
   10,000원 미만이면 그 키워드만 빠지고, 반대로 그룹 자체가 10,000원 미만이면 그 그룹과 모든
   하위 키워드가 통째로 빠진다). 필터링은 3번(비율 지표 계산) 이후, 최종 트리를 만들기 전에
   적용한다.
   - 키워드는 개별 단가가 작아 이 기준을 넘는 경우가 드물다 — 필터링 후 특정 광고그룹의 키워드가
     0개가 되면, 그 광고그룹 행은 (10,000원 기준을 만족해 자체는 표에 남아 있더라도) 펼치기
     아이콘(▸) 없이 렌더링한다 (펼쳐도 보여줄 키워드가 없으므로).
6. 위 1~5단계는 전부 기계적 매칭·합산·나눗셈·필터링이며 raw 값 자체를 임의로 보정·추정하지
   않으므로 상위 "데이터 처리 원칙"과 충돌하지 않는다.

### 응답 데이터 구조 (가공 후, 렌더링에 쓰는 최종 트리 형태)

```json
{
  "adgroup_hierarchy": [
    {
      "level": "group", "group": "02_분유(스토어)", "channel_label": "네이버 브랜드검색", "campaign": "00_통합(BS)_MO",
      "impressions": 1315, "clicks": 206, "ad_cost": 133321, "cpc": 647.19, "ctr": 15.66, "cpm": 101.4,
      "purchases": 81, "revenue": 7204020, "roas": 5403.6,
      "children": [
        { "level": "keyword", "keyword": "아기사랑수",
          "impressions": 320, "clicks": 41, "ad_cost": 26100, "cpc": 636.6, "ctr": 12.81, "cpm": 81.6,
          "purchases": 15, "revenue": 1230000, "roas": 4712.6 }
      ]
    }
  ]
}
```

### PPT 섹션 (분기 B)

```json
{
  "type": "table",
  "heading": "광고 그룹 및 키워드 성과",
  "headers": ["채널 / 캠페인", "광고그룹", "키워드", "노출", "클릭", "광고비", "CPC", "CTR", "CPM", "구매건수", "매출", "ROAS"],
  "rows": [
    ["{channel_label} / {campaign}", "{group}", "전체", "{impressions_fmt}", "{clicks_fmt}", "{ad_cost_fmt}", "{cpc_fmt}", "{ctr}%", "{cpm_fmt}", "{purchases}", "{revenue_fmt}", "{roas}%"],
    ["", "", "└ {keyword}", "{impressions_fmt}", "{clicks_fmt}", "{ad_cost_fmt}", "{cpc_fmt}", "{ctr}%", "{cpm_fmt}", "{purchases}", "{revenue_fmt}", "{roas}%"]
  ]
}
```

- **판단 근거**: 원본 HTML은 접기/펼치기가 가능한 2단계 트리(광고그룹→키워드)였으나, `table`
  섹션 스키마(`headers`/`rows`: 문자열 리스트의 리스트)에는 트리·펼침 상태 개념이 없다. 정적
  문서에서는 애초에 펼치기 인터랙션이 불가능하므로, **광고그룹 행 바로 아래에 그 그룹의 모든
  키워드 행을 이미 펼쳐진 상태로 이어 붙인 하나의 평평한(flat) 표**로 만든다.
- 광고그룹 행: `채널 / 캠페인` 컬럼에 `{channel_label} / {campaign}`, `광고그룹` 컬럼에 그룹명,
  `키워드` 컬럼에는 "전체"(원본에서 광고그룹 행의 키워드 셀에 표시되던 값 그대로) — `adgroup_hierarchy`
  배열을 순회하며 만든다.
- 키워드 행: `채널 / 캠페인`/`광고그룹` 컬럼은 빈 문자열로 비우고, `키워드` 컬럼에 `└ {keyword}`
  (들여쓰기 표시용 접두사 — 원본의 자식 행 시각적 구분을 표에서도 유지하기 위한 판단)를 넣는다.
  각 광고그룹의 `children`(키워드) 배열을 그 광고그룹 행 바로 다음 줄들에 순서대로 넣는다.
- 키워드가 상위 20개로 잘린 경우, 그 뒤에 안내용 키워드 행 하나를 추가한다:
  `["", "", "└ 외 {N}개 키워드", "", "", "", "", "", "", "", "", ""]`.
- `cpc`가 `null`(클릭 0)이면 "-", `roas`가 `null`(광고비 0)이면 "-"로 표시한다.
- 검색창/페이지네이션/펼치기 아이콘은 정적 문서에 의미가 없으므로 전부 제거하고, 전체 트리를
  이미 펼쳐진 flat 표 하나로 낸다 (mtd 계열 표 섹션과 동일한 "전체 행을 한 표에" 판단을
  트리 구조에 맞게 확장 적용).

## 렌더링 규칙 (분기 B)
- 광고그룹 정렬: 매출 내림차순 (`-revenue`), 동률이면 광고비 내림차순. 키워드도 같은 그룹 안에서
  동일하게 정렬.
- `cpc`가 `null`(클릭 0)이면 "-" 표시, `roas`가 `null`(광고비 0)이면 "-" 표시.
- 광고그룹 하나에 키워드가 많을 수 있으므로, 매출 상위 20개까지만 자식으로 붙이고 나머지는
  "외 {N}개 키워드" 안내 행으로 대체한다.
- ⚠️ **광고비(`ad_cost`) 10,000원 미만인 행은 광고그룹/키워드 레벨 모두에서 표에 나타나지
  않는다** (데이터 가공 5번 참고, 2026-07-23 추가). 필터링 후 광고그룹이 하나도 남지 않으면
  "이번 기간 10,000원 이상 집행된 광고그룹이 없음" 안내 카드로 대체한다 (빈 테이블로 남기지
  않음).
- 이 섹션은 daily-section-5(캠페인 성과)와 같은 3개 SA 채널(브랜드검색/파워링크/쇼핑검색)만
  다룬다 — GFA 채널은 광고그룹/키워드 구조가 없다.
- (참고, HTML 시절 UI 사양 — 정적 문서에는 적용되지 않음) 원본 HTML에는 광고그룹 단위
  페이지네이션(10/20/50개)과 광고그룹명/채널·캠페인 컬럼 기준 검색 기능이 있었으나, DOCX
  섹션에서는 위 "PPT 섹션 (분기 B)"의 판단대로 전체 트리를 flat 표 하나로 이미 펼쳐서 낸다.

