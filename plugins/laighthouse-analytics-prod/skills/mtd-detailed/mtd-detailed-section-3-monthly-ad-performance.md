# Breezm MTD Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 최근 6개월(당월
포함), 연-월 단위. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ℹ️ 차트 HTML/Script/축·tooltip 포맷(₩콤마, ROAS 축 min:0)은 전부 템플릿+빌더가 처리한다 —
> 모델은 아래 규칙으로 **6개월치 배열 3개**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`media` 생략)

```json
{ "brand_name": "breezm", "start_date": "5개월 전 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"], "day_offset": "target_date.day" }
```

- **`media` 생략** — 1회 호출로 월별·매체별(`Google`/`Meta`/`Naver`) 행을 전부 받는다. 각
  행에 `month`("YYYY-MM") 키와 `광고비`/`매출_AB`/`예약완료_AB` 등 지표가 함께 들어있다
  (별도 매출 응답 없음).
- **`day_offset: target_date.day` 필수** — 없으면 당월이 실제 오늘 날짜까지 누적되어 섹션 1/6과
  어긋난다.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 월별: 세 매체 행의 `광고비` 합 |
| `revenue` | 월별: 세 매체 행의 `매출_AB` 합 |
| `roas` | 월별: 매출 ÷ 광고비 × 100 (광고비 0인 달은 `null`) — 매체별 행을 합산했으므로 행의 `ROAS_AB`를 더하지 말고 원자 지표 합으로 계산한다 |
| `labels` | 생략 (빌더가 `{YY}년 {M}월` + 당월 `(진행 중)` 자동 생성) |
| `zero_fill_note` | 데이터가 없어 0으로 채운 월이 있을 때만: `* {YY}년 {MM}월~{YY}년 {MM}월은 데이터가 수집되지 않아 광고비 또는 매출이 0으로 표시되었습니다.` 완성 문구. 없으면 필드 자체를 생략 |

- **최근 6개월 고정** — 행이 없는 월도 제외하지 않고 0으로 채워 항상 6개 전부 넣는다(광고비만
  있고 매출이 없는 월은 매출/ROAS만 0). 당월 기준일 각주(`* {YY}년 {M}월은 기준일...`)는
  빌더가 자동 생성한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → "데이터 준비 중" 카드 (추정/보간 금지).
- 첫 응답에서 `metrics` 목록과 실제 `media` 값을 확인하고, 기대 값과 다르면 조용히 0을
  만들지 말고 Executive Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
