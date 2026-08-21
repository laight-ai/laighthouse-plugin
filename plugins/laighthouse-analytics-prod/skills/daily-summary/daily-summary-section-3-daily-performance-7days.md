# Breezm Executive Daily Section 3: 최근 7일 성과 (Daily Performance, 7-Day)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 기준일 포함
최근 7일 일자별 광고 성과(광고비/매출/ROAS 혼합 차트). 매출은 Airbridge 귀속 매출
(`매출_AB`).

> ℹ️ 차트 HTML/Script/프로모션 브래킷 오버레이(인덱스 계산·클램프·밴드 폭 보정 포함)는 전부
> 템플릿+빌더가 한다 — 모델은 아래 규칙으로 **7일치 배열 3개**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (section-4/5 공유)

```json
{ "brand_name": "breezm", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "group_by": ["media"] }
```

- **`media` 파라미터를 생략한다** — 이 1회 호출로 날짜별·매체별(`Google`/`Meta`/`Naver`) 행에
  더해, `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속)도 함께 받는다. 각 행에
  `광고비`/`매출_AB`/`예약완료_AB` 등 지표가 함께 들어있다(별도 매출 응답 없음).
- **이 응답은 section-4/5가 그대로 재사용한다** — section-4는 날짜별 `매출_AB` 합(전체 매출은
  `null` 행 포함, 광고 매출은 제외한 합)을, section-5는 마지막 이틀(D-1, D-0) 행만 쓴다. 세
  섹션이 각자 호출하지 않는다.
- 이 섹션(`s3`)의 `ad_cost`/`revenue`는 **세 매체 행만** 합산한다 — `null`(Organic) 행은
  광고 성과 차트이므로 여기서는 제외한다(전체 매출이 필요한 곳은 section-4).

## `list_promotions` — 별도 호출 없음, section-2의 공유 응답(7일 룩백)을 재사용

## 빌더 `s3` 필드 (각 배열은 7개, 기준일-6일 → 기준일 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 날짜별: 세 매체 행의 `광고비` 합 |
| `revenue` | 날짜별: 세 매체 행의 `매출_AB` 합 |
| `roas` | 날짜별: 매출 ÷ 광고비 × 100 (광고비 0인 날은 `null`) — 매체별 행을 합산했으므로 행의 `ROAS_AB`를 더하지 말고 원자 지표 합으로 계산한다 |
| `promotions` | section-2 공유 `list_promotions` 응답 `items[]`의 `{title, date_begin, date_end}`를 **가공 없이 그대로** 담은 배열 (없으면 `[]`) — 인덱스 계산·클램프·범위 밖 제외·`M/D~D` 라벨 생성은 빌더가 한다 |
| `labels` | 생략 (빌더가 `M/D(요일)` 자동 생성) |

- 7일 전부 넣는다 — 매출 0원인 날도 0 그대로 (추정/보간 금지).
- 첫 응답에서 `metrics` 목록과 실제 `media` 값을 확인하고, 기대 값(`Google`/`Meta`/`Naver`,
  `광고비`/`매출_AB`)과 다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에 불일치 안내
  불릿을 추가한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
