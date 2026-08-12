# Breezm MTD Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 최근 6개월(당월
포함), 연-월 단위. 매출은 Airbridge 매출, 광고 채널은 `Google Ads`/`Meta Ads`/`Naver Ads` 행.

> ℹ️ 차트 HTML/Script/축·tooltip 포맷(₩콤마, ROAS 축 min:0)은 전부 템플릿+빌더가 처리한다 —
> 모델은 아래 규칙으로 **6개월치 배열 3개**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1 (`media` 생략)

```json
{ "brand_name": "breezm", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "media", "day_offset": "target_date.day" }
```

- **`media` 생략** — 1회 호출로 전 매체를 받는다: `media`가 `google`/`meta`/`naver`인 행(매체당
  월별 합산 한 줄, `cost`), `airbridge`인 행(월별·`channel`별 여러 줄). `ga4` 등은 무시.
- **`day_offset: target_date.day` 필수** — 없으면 당월이 실제 오늘 날짜까지 누적되어 섹션 1/6과
  어긋난다.
- ⚠️ `campaign-type` 금지, `group_by`는 문자열 `"media"` 그대로.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 월별: google/meta/naver 세 행의 `cost` 합 |
| `revenue` | 월별: airbridge 행 중 광고 채널 3종의 `airbridge_revenue` 합 |
| `roas` | 월별: 매출 ÷ 광고비 × 100 (광고비 0인 달은 `null`) |
| `labels` | 생략 (빌더가 `{YY}년 {M}월` + 당월 `(진행 중)` 자동 생성) |
| `zero_fill_note` | 데이터가 없어 0으로 채운 월이 있을 때만: `* {YY}년 {MM}월~{YY}년 {MM}월은 데이터가 수집되지 않아 광고비 또는 매출이 0으로 표시되었습니다.` 완성 문구. 없으면 필드 자체를 생략 |

- **최근 6개월 고정** — 행이 없는 월도 제외하지 않고 0으로 채워 항상 6개 전부 넣는다(광고비만
  있고 매출이 없는 월은 매출/ROAS만 0). 당월 기준일 각주(`* {YY}년 {M}월은 기준일...`)는
  빌더가 자동 생성한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → "데이터 준비 중" 카드 (추정/보간 금지).
- 첫 airbridge 응답의 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 Executive
  Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
