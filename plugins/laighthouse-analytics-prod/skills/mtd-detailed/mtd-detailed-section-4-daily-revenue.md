# Breezm MTD Section 4: 일일 매출 현황 (Daily Revenue)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 월초~target_date
일별 광고 매출 vs 전체 매출. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ℹ️ **`total_revenue` 계산법**: `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속)도
> 응답에 정상적으로 포함되어 있다. 날짜별로 **모든 `media` 값(Google/Meta/Naver/`null`)의
> `매출_AB`를 합산**하면 `total_revenue`, **`media`가 `null`이 아닌 행만 합산**하면
> `ad_revenue`다.

> ℹ️ 차트 HTML/Script/두 줄 라벨(날짜+요일)/프로모션 브래킷 오버레이(인덱스 계산·클램프 포함)는
> 전부 빌더가 한다 — 모델은 **일별 배열 2개와 프로모션 원본 목록**만 빌더 입력 JSON의 `s4`에
> 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 + `list_promotions` × 1

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "time_grain": "day", "group_by": ["media"] }
```
```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date" }
```

- `get_ad_performance`는 `media`를 생략한다 — 이 섹션 전용 신규 호출이다(section-2/3은
  `time_grain:"month"`라 grain이 달라 공유하지 않는다).
- `list_promotions` 응답은 section-2(Executive Summary)/section-5(캠페인 분석)가 그대로
  재사용한다.

## 빌더 `s4` 필드 (일별 배열, 월초 → target_date)

| 필드 | 값 |
|---|---|
| `ad_revenue` | 날짜별: `media`가 `null`이 아닌 행(`Google`/`Meta`/`Naver`)의 `매출_AB` 합 |
| `total_revenue` | 날짜별: **모든** 행(`null` 포함)의 `매출_AB` 합 |
| `promotions` | `list_promotions` 응답 원본을 가공 없이 그대로 |
| `labels` | 생략 (빌더가 자동 생성) |

`ad_revenue`를 `total_revenue`에 복사하거나 둘을 같은 값으로 채우지 않는다 — `null` 행의
매출이 빠지면 `total_revenue`가 아니라 `ad_revenue`가 된다.
