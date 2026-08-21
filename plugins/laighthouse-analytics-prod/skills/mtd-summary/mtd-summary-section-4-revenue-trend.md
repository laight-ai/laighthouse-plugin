# Breezm Executive MTD Section 4: 매출 추이 (Revenue Trend)

**report_type:** `mtd-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 최근 6개월
(당월 포함) 라인 차트. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ℹ️ **`total_revenue` 계산법**: `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속)도
> 응답에 정상적으로 포함되어 있다. 월별로 **모든 `media` 값(Google/Meta/Naver/`null`)의
> `매출_AB`를 합산**하면 `total_revenue`, **`media`가 `null`이 아닌 행만 합산**하면
> `ad_revenue`다 — 둘 다 이미 받은 응답에서 바로 계산되며 별도 호출이 필요 없다.

> ℹ️ 차트 HTML/Script/월 라벨/각주(MTD 기준·전체 매출 정의·zero-fill)는 전부 빌더가 한다 —
> 모델은 아래 규칙으로 **6개월치 배열 2개**만 빌더 입력 JSON의 `s4`에 넣는다.

## MCP 호출 없음 — section-3의 공유 응답을 재사용

- 이 섹션은 `get_ad_performance`를 직접 호출하지 않는다 — section-3이 받은 공유 응답
  (`media` 생략, `time_grain:"month"`, `group_by:["media"]`, 5개월 전~당월,
  `day_offset`=target_date.day)에서 월별 `매출_AB` 합(= 광고 매출)을 얻을 수 있다.

## 빌더 `s4` 필드 (각 배열 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_revenue` | 월별: `media`가 `null`이 아닌 행(`Google`/`Meta`/`Naver`)의 `매출_AB` 합 |
| `total_revenue` | 월별: **모든** 행(`null` 포함)의 `매출_AB` 합 |
| `labels` | 생략 (빌더가 자동 생성) |
| `zero_fill` | 빌더 스키마대로(데이터 없는 월 0 채움 여부) |

`ad_revenue`를 `total_revenue`에 복사하거나 둘을 같은 값으로 채우지 않는다 — `null` 행의
매출이 빠지면 `total_revenue`가 아니라 `ad_revenue`가 된다.
