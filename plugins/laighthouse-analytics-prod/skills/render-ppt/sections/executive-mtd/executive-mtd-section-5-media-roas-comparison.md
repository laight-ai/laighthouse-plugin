# Executive-MTD Section 5: 매체별 성과 비교

**report_type:** `executive-mtd` (항상 포함) — mtd(MK)에는 없는 신규 섹션.

이 섹션은 채널별로 "이번 달(MTD) ROAS vs 전월(동일 기간) ROAS"와 그 변동(%p)만 보여주는 표다.
Monthly report의 `monthly-section-8-media-comparison-table.md`가 채널마다 광고비/매출/ROAS를
전부 보여주는 것과 달리, executive-mtd는 **ROAS와 변동(%p)만** 보여준다 — 임원에게는 예산 집행
디테일보다 "효율이 좋아지고 있는지 나빠지고 있는지"가 먼저 보여야 하기 때문이다. (3번 스크린샷
참고 — 채널 / 전월 ROAS / 이번달 ROAS / 변동(%p) 4개 컬럼의 단일 표, 변동이 나쁜 채널이 위로
오도록 정렬)

---

## 도구 선정 근거 (중요 — 반드시 읽고 넘어갈 것)

> ⚠️ **`get_naver_monthly_ad_performance`는 참고했지만 이 표를 직접 만들 수는 없다.** 이 도구는
> executive-mtd-section-2(월별 광고 성과 차트)을 위한 것으로, **5개 채널을 이미 합산한 브랜드
> 전체 총계** 한 줄만 월별로 반환한다 (채널 구분 없음, 2026-07-22 확인 — Monthly report 스킬
> 개발 시 이미 검증된 동일한 제약이다). 채널별로 쪼개야 하는 이 표에는 쓸 수 없다.
> 대신 `get_naver_channel_progression`(mtd-section-7 매체별 예산 소진 현황이 쓰는 채널 단위
> 원천 도구)을 이번 달/전월 두 번 호출해, 각 채널의 일별 `actual[].{cost,revenue}`를 합산해
> ROAS를 직접 계산한다.

## MCP 도구 호출: `get_naver_channel_progression` (두 번 호출)

```json
// 1) 이번 달 (as_of_date = target_date까지만 합산됨)
{ "brand_name": "...", "month": "이번달 YYYY-MM", "as_of_date": "target_date" }
// 2) 전월 동일 기간
{ "brand_name": "...", "month": "전월 YYYY-MM", "as_of_date": "전월 1일 + (target_date의 일 - 1), 전월 마지막 날로 clamp" }
```

> ⚠️ **MTD 공정 비교를 위해 전월도 `as_of_date`로 동일 일수만큼 자른다** — executive-mtd-
> section-5(카테고리별 요약)와 동일한 전월 구간 규칙을 쓴다. `get_naver_channel_progression`의
> `actual[]`는 항상 해당 월 전체(달력월 전부)를 반환하므로, 이 스킬이 직접 `date <= as_of_date`
> 조건으로 일별 항목을 잘라낸 뒤 합산해야 한다 (도구가 자동으로 잘라주지 않는다).

응답의 `channels[]`(`nvad:BRS`/`nvad:PLINK`/`nvad:NVSHOP`/`nvgfa_ad:`/`nvgfa_dp:`) 각각의
`actual[]`(일별 `{date, cost, revenue}`)을 받는다.

## 데이터 가공 (이 단계만 예외적으로 허용 — 상위 규칙 참고)

각 채널, 각 기간(이번 달 MTD, 전월 동일 기간)에 대해:

1. `actual[]`에서 `date <= as_of_date`(해당 기간의 마지막 날)인 항목만 남겨 `cost`/`revenue`를
   합산한다.
2. ⚠️ **GFA 채널(`nvgfa_ad:`, `nvgfa_dp:`)의 `cost` 합계는 VAT 포함가이므로 `/ 1.1`로 VAT를
   제거한다** (nvad 채널 3개는 이미 VAT 제외 금액). Monthly report 개발 시 실제 데이터로 이미
   검증된 규칙이다 (raw 합계 ÷ 1.1 = 실제 리포트 수치와 소수점까지 일치).
3. `roas = revenue_sum / cost_sum × 100` (`cost_sum`이 0이면 `roas`는 `null`, 표에서 제외).
4. `roas_change_pp = curr_roas - prev_roas` (퍼센트포인트 단위, 예: 823.5 - 1003.3 = -179.8).
5. **네이버 GFA 디스플레이(`nvgfa_dp:`) 채널은 이 표에서 제외한다** — 순수 브랜딩/디스플레이
   목적 채널로 매출 기여가 낮고 ROAS 변동성이 커서, 성과형 채널(BRS/PLINK/NVSHOP/GFA
   애드부스트)과 같은 기준으로 비교하면 오해를 줄 수 있다 (3번 스크린샷도 4개 채널만 보여줌).
6. 위 계산은 전부 기계적 합산·나눗셈이며 값을 임의로 보정하지 않으므로 상위 "데이터 처리
   원칙"과 충돌하지 않는다.

## 채널 라벨 매핑 (mtd-section-7과 동일, GFA 디스플레이만 제외)

| 채널 키 | 표시 라벨 |
|---|---|
| `nvad:BRS` | 네이버 브랜드검색 |
| `nvad:PLINK` | 네이버 파워링크 |
| `nvad:NVSHOP` | 네이버 쇼핑검색 |
| `nvgfa_ad:` | 네이버 GFA 애드부스트 |

## 응답 데이터 구조 (가공 후, 렌더링에 쓰는 최종 형태)

```json
{
  "media_roas_comparison": {
    "prev_period_label": "2월",
    "curr_period_label": "3월",
    "rows": [
      { "channel_label": "네이버 GFA 애드부스트", "prev_roas": 1003.3, "curr_roas": 823.5, "change_pp": -179.7 },
      { "channel_label": "네이버 브랜드검색",     "prev_roas": 723.8,  "curr_roas": 610.6, "change_pp": -113.2 },
      { "channel_label": "네이버 파워링크",       "prev_roas": 905.9,  "curr_roas": 971.5, "change_pp": 65.6 },
      { "channel_label": "네이버 쇼핑검색",       "prev_roas": 342.8,  "curr_roas": 361.9, "change_pp": 19.2 }
    ]
  }
}
```

## PPT 섹션

```json
{
  "type": "table",
  "heading": "매체별 성과 비교",
  "headers": ["채널", "{prev_period_label} ROAS", "{curr_period_label} ROAS", "변동"],
  "rows": [
    ["{channel_label}", "{prev_roas_fmt}%", "{curr_roas_fmt}%", "{CHANGE_LABEL}"]
  ]
}
```

- `media_roas_comparison.rows` 배열의 각 원소를 위 `rows` 배열의 행 하나로 매핑한다(`change_pp`
  오름차순 정렬 후).
- `CHANGE_LABEL`은 `change_pp > 0`이면 `"+{change_pp}%p"`, `change_pp < 0`이면 `"{change_pp}%p"`
  (마이너스 기호 유지, 예: `-179.7%p`)로 문자열에 미리 부호를 반영해 넣는다 — `table` 섹션은
  `kpi_cards`와 달리 `diff_value` 기반 자동 색상 판정을 지원하지 않으므로(셀 단위 조건부 서식
  없음), 원본 HTML의 `CHANGE_COLOR`(초록/빨강) 강조는 정적 문서에서 표현하지 않고 부호가 담긴
  텍스트만으로 증감 방향을 전달한다.
- `prev_roas`/`curr_roas`는 소수점 첫째자리까지 표시한다 (예: `823.5%`).
- `cost_sum`이 0이라 `roas`가 `null`인 채널은 `rows`에서 해당 행 자체를 제외한다.
- 데이터가 비어있으면 이 섹션 전체를 생략한다(임의로 채우지 않는다).

## 렌더링 규칙
- `rows`는 `change_pp` **오름차순**(가장 나쁜 변화, 즉 가장 큰 음수부터)으로 정렬한다 — 임원이
  가장 먼저 확인해야 할 악화 채널이 표 맨 위에 오도록 한다 (3번 스크린샷과 동일한 정렬).
- `change_pp > 0`이면 `CHANGE_LABEL = "+{change_pp}%p"`; `change_pp < 0`이면
  `CHANGE_LABEL = "{change_pp}%p"` (마이너스 기호 유지, 예: `-179.7%p`).
- `prev_roas`/`curr_roas`는 소수점 첫째자리까지 표시한다 (예: `823.5%`).
- `cost_sum`이 0이라 `roas`가 `null`인 채널은 표에서 해당 행 자체를 제외한다 (0%로 표시하지
  않는다 — 나눗셈 자체가 불가능한 상태이기 때문).
- 데이터가 비어있으면 이 섹션 전체를 생략한다.
