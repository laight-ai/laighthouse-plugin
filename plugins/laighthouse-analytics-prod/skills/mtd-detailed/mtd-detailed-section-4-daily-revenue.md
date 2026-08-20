# Breezm MTD Section 4: 일일 매출 현황 (Daily Revenue)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 월초~target_date
일별 광고 매출 vs 전체 매출. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ⚠️ **ELT 이관 후 알려진 제약**: 이 차트의 `total_revenue`(오거닉 포함 전체 매출)는 현재
> 데이터 소스(ELT 광고 성과 — 광고 귀속 지표만 제공)에서 얻을 수 없다. 광고 매출을 전체
> 매출로 지어 넣지 말고, **`s4` 키를 빌더 입력에서 빼서 "데이터 준비 중" 카드로 렌더링한다.**
> 단, 아래 `list_promotions` 호출은 section-2/5가 재사용하므로 **여전히 수행한다.**
> 서버가 전체 매출 지표를 다시 제공하면 아래 규칙을 복원한다.

> ℹ️ 차트 HTML/Script/두 줄 라벨(날짜+요일)/프로모션 브래킷 오버레이(인덱스 계산·클램프 포함)는
> 전부 빌더가 한다 — 모델은 **일별 배열 2개와 프로모션 원본 목록**만 빌더 입력 JSON의 `s4`에
> 넣는다.

## MCP 도구 호출: `list_promotions` (월초~target_date, 1회)

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date" }
```

- 이 응답은 section-2(Executive Summary)/section-5(캠페인 분석)가 그대로 재사용한다.

## 빌더 `s4` 필드 — 현재는 사용하지 않는다 (위 제약 참고)

빌더 스키마는 `ad_revenue`/`total_revenue`(일별)/`promotions`/`labels`지만, `total_revenue`
소스가 없는 동안은 **`s4` 키 자체를 넣지 않는다** → "데이터 준비 중" 카드. `ad_revenue`만으로
차트를 채우거나 `total_revenue`에 광고 매출을 복사해 넣는 것은 금지다(전체 매출 정의 왜곡).
