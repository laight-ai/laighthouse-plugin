# Daily Section 5: 캠페인 성과 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/daily/daily-section-5-campaign-performance.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션 (분기 A)

```json
{
  "type": "table",
  "heading": "Performance by Campaign",
  "headers": ["Media", "Campaign", "Impression", "Click", "CTR (%)", "Cost ($)", "Revenue ($)", "ROAS (%)"],
  "rows": [
    ["{media}", "{campaign}", "{impression_fmt}", "{click_fmt}", "{ctr}", "{cost_fmt}", "{revenue_fmt}", "{roas}"]
  ]
}
```

`rows`에는 `sales_by_campaign` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로 넣는다
(검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한 표에 다 낸다,
mtd-section-9/10/11과 동일한 판단).

### 렌더링 규칙 (분기 A)
- 금액/노출/클릭 필드는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.

---

## 분기 B: naver 브랜드 ⭐ 재설계 (채널 단위 → 캠페인 단위)

mtd(MK)의 `mtd-section-9-campaign-performance.md`와 **거의 동일한 포맷**이지만, 날짜 범위가
"월초~target_date"가 아니라 **target_date 하루뿐**이다.

### MCP 도구 호출: `get_naver_campaign_performance`

```json
{ "brand_name": "...", "start_date": "target_date", "end_date": "target_date" }
```

- naver 전용 MCP 도구. 캠페인×채널 단위로 이미 groupby/합산/roas·ctr·cpc·avg_price 계산과
  정렬(`-roas,-ad_cost,-revenue,campaign,channel`)이 **서버에서 끝난 상태**로 반환된다.
- ⚠️ **naver 검색광고(SA) 3개 채널(BRS/PLINK/NVSHOP)만 다룬다** — GFA 애드부스트/디스플레이는
  캠페인 구조가 없는 프로그래매틱 디스플레이 상품이라 이 도구에 데이터가 없다. GFA 채널의 일별
  성과를 보려면 daily-section-2(목표 달성 현황)의 전체 합산 수치로만 확인 가능하다 (개별 채널
  분해는 이번 섹션 재구성에서 제외되었다 — 이전 버전의 "적정 광고비" 포함 채널 요약 표는 계산식
  불확실 문제로 삭제됨).
- 응답의 `ctr`/`roas`는 이미 percentage-scale이다 (예: 1017 → 1017%) — × 100 하지 않는다.
- `cpm` 필드는 이 도구에 없으므로 이 스킬이 직접 계산한다: `cpm = ad_cost / impressions × 1000`.

### 필요 데이터 (MCP + 가공)
- `campaign_performance`: 캠페인 배열
  ```json
  [
    { "campaign": "00_통합(BS)_MO", "channel": "BRS", "revenue": 4441630, "ad_cost": 494112,
      "roas": 898.91, "impressions": 5901, "clicks": 686, "ctr": 11.63, "cpc": 720.28,
      "cpm": 83.74, "purchases": 66 }
  ]
  ```
  (`cpm`은 위 공식으로 이 스킬이 추가 — 원본 응답의 `avg_price`는 이 표에서 쓰지 않는다,
  요청된 metric 목록에 없음)

### DOCX 섹션 (분기 B)

```json
{
  "type": "table",
  "heading": "캠페인 성과",
  "headers": ["광고 채널", "캠페인", "노출", "클릭", "광고비", "CPC", "CTR", "CPM", "구매건수", "매출", "ROAS"],
  "rows": [
    ["{channel_label}", "{campaign}", "{impressions_fmt}", "{clicks_fmt}", "{ad_cost_fmt}", "{cpc_fmt}", "{ctr}%", "{cpm_fmt}", "{purchases}", "{revenue_fmt}", "{roas}%"]
  ]
}
```

`rows`에는 (10,000원 미만 필터링 후) `campaign_performance` 배열의 모든 항목을 위 필드 매핑대로
한 행씩 그대로 넣는다 (검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한
표에 다 낸다, mtd-section-9 패턴과 동일).

## DOCX 관련 공통 참고 (두 분기)
검색창/페이지네이션 UI는 정적 문서에 존재하지 않으므로 두 분기 모두 표는 전체 행을 한 번에 낸다
— 별도 스크립트/상호작용 로직은 필요 없다.

## 렌더링 규칙 (분기 B)
- `channel_label` 매핑: `BRS`→네이버 브랜드검색, `PLINK`→네이버 파워링크, `NVSHOP`→네이버 쇼핑검색.
- 금액/노출/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷.
- ⚠️ **`ad_cost`(광고비)가 10,000원 미만인 캠페인 행은 표에서 제외한다** (2026-07-23 추가) —
  `get_naver_campaign_performance` 응답을 받은 뒤, 렌더링 전에 `ad_cost >= 10000`인 행만
  필터링한다. 소액 테스트성 캠페인이나 노출만 있고 예산이 거의 소진되지 않은 캠페인을 표에서
  걸러내기 위함이다. 이 필터링은 표시 목적의 후처리이며, daily-section-2(목표 달성 현황) 등
  다른 섹션의 합계 수치에는 영향을 주지 않는다(그 섹션들은 필터링 이전의 전체 합계를 그대로
  쓴다).
- 필터링 후 행이 하나도 남지 않으면 "이번 기간 10,000원 이상 집행된 캠페인이 없음" 안내 카드로
  대체한다 (빈 테이블로 남기지 않음).
- 매출이 0인 캠페인도 (광고비 조건을 만족하면) 그대로 표시한다 — 광고비만 나가고 전환이 없는
  캠페인도 중요한 신호다.
