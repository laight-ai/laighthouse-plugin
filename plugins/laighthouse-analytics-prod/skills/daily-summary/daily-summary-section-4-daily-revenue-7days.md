# Breezm Executive Daily Section 4: 일일 매출 현황 (최근 7일)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 기준일 포함
**최근 7일** 일별 광고 매출 vs 전체 매출 라인 차트 — section-3보다 간결하게 임원이 매출
추이만 한눈에 보는 섹션이다. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ℹ️ **`total_revenue` 계산법**: `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속)도
> 응답에 정상적으로 포함되어 있다. 날짜별로 **모든 `media` 값(Google/Meta/Naver/`null`)의
> `매출_AB`를 합산**하면 `total_revenue`, **`media`가 `null`이 아닌 행만 합산**하면
> `ad_revenue`다 — 둘 다 이미 받은 응답에서 바로 계산되며 별도 호출이 필요 없다.

> ℹ️ 라인 차트 HTML/Script/2줄 라벨(`[M/D, (요일)]`)/₩ 축·tooltip/프로모션 브래킷(라인 차트라
> 밴드 폭 보정 없음)은 전부 템플릿+빌더가 한다 — 모델은 아래 규칙으로 **7일치 배열 2개**만
> 빌더 입력 JSON의 `s4`에 넣는다.

## MCP 호출 없음 — section-3/2의 공유 응답을 재사용

- `get_ad_performance`(day grain, `group_by:["media"]`): section-3의 공유 응답에서 날짜별
  `매출_AB` 합(= 광고 매출)을 얻을 수 있다.
- `list_promotions`: section-2의 공유 응답(7일 룩백)을 재사용 — 범위 밖 항목은 빌더 clamp가
  자동 제외.

## 빌더 `s4` 필드 (각 배열 7개, 기준일-6일 → 기준일 순)

| 필드 | 값 |
|---|---|
| `ad_revenue` | 날짜별: `media`가 `null`이 아닌 행(`Google`/`Meta`/`Naver`)의 `매출_AB` 합 |
| `total_revenue` | 날짜별: **모든** 행(`null` 포함)의 `매출_AB` 합 |
| `promotions` | section-2 공유 `list_promotions` 응답을 가공 없이 그대로 |
| `labels` | 생략 (빌더가 자동 생성) |

`ad_revenue`를 `total_revenue`에 복사하거나 둘을 같은 값으로 채우지 않는다 — `null` 행의
매출이 빠지면 `total_revenue`가 아니라 `ad_revenue`가 된다.
