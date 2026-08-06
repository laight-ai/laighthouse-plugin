# Monthly Section 8: 매체별 성과 비교

**report_type:** `monthly` (항상 포함) — mtd(MK)에는 없는 신규 섹션.

이번 달과 전월의 매체(채널)별 광고비/매출/ROAS를 채널 그룹별로 나란히 비교하는 표다. 채널 그룹
5개(네이버 브랜드검색 / 네이버 파워링크 / 네이버 쇼핑검색 / 네이버 GFA 애드부스트 / 네이버 GFA
디스플레이) 각각에 대해, "전월" 행과 "이번달" 행 두 줄을 보여준다.

---

## 도구 선정 근거 (중요 — 반드시 읽고 넘어갈 것)

> ⚠️ **`get_naver_monthly_ad_performance`는 참고했지만 이 표를 직접 만들 수는 없다.** 이 도구는
> report-backend의 "월별 광고 성과" 차트(monthly-section-4)를 위한 것으로, **5개 채널을 이미
> 합산한 브랜드 전체 총계** 한 줄만 월별로 반환한다 (`items[].{month,cost,purchase_amount,roas}`
> — 채널 구분 없음, 2026-07-22 실제 호출로 확인). 이 섹션처럼 **채널별로 쪼개서** 보여줘야 하는
> 표에는 쓸 수 없다.
> 대신 `get_naver_channel_progression`(mtd-section-7 매체별 예산 소진 현황이 쓰는 채널 단위
> 원천 도구)을 이번 달/전월 두 번 호출해, 각 채널의 일별 `actual[].{cost,revenue}`를 월 전체로
> 합산한다 — `get_naver_monthly_ad_performance`가 내부적으로 각 채널을 리듀스하기 전 단계의
> 데이터를 채널 단위로 유지한 것과 동일한 소스다.

## MCP 도구 호출: `get_naver_channel_progression` (두 번 호출)

```json
// 1) 이번 달
{ "brand_name": "...", "month": "이번달 YYYY-MM", "as_of_date": "이번달 말일" }
// 2) 전월
{ "brand_name": "...", "month": "전월 YYYY-MM", "as_of_date": "전월 말일" }
```

응답의 `channels[]`(5개: `nvad:BRS`/`nvad:PLINK`/`nvad:NVSHOP`/`nvgfa_ad:`/`nvgfa_dp:`) 각각의
`actual[]`(일별 `{date, cost, revenue}`) 배열을 그대로 받는다.

## 데이터 가공 (이 단계만 예외적으로 허용 — 상위 규칙 참고)

각 채널, 각 월에 대해:

1. `cost_sum` = 그 채널의 `actual[].cost`를 월 전체에 대해 합산.
   ⚠️ **GFA 채널(`nvgfa_ad:`, `nvgfa_dp:`)의 `cost`는 VAT 포함가다 — 반드시 `/ 1.1`로 VAT를
   제거한 값을 써야 실제 리포트 수치와 일치한다** (nvad 채널 3개는 이미 VAT 제외 금액이므로
   그대로 합산). 이 VAT 규칙은 mtd-section-7(매체별 예산 소진 현황)이 이미 문서화한 것과 동일
   하며, 2026-07-22 실제 데이터로 재검증했다 (GFA 애드부스트 채널: raw 합계 ÷ 1.1 = 실제 리포트
   수치와 소수점까지 일치).
2. `revenue_sum` = 그 채널의 `actual[].revenue`를 월 전체에 대해 합산 (VAT 조정 없음 — revenue
   필드는 채널 종류와 상관없이 그대로 합산해도 실제 수치와 일치함, 2026-07-22 검증).
3. `roas` = `revenue_sum / cost_sum × 100` (cost_sum이 0이면 `roas`는 `null`).
4. 위 세 단계는 전부 기계적 합산·나눗셈이며 값을 임의로 보정하지 않으므로 상위 "데이터 처리
   원칙"과 충돌하지 않는다.

## 채널 라벨 매핑 (mtd-section-7과 동일)

| 채널 키 | 표시 라벨 |
|---|---|
| `nvad:BRS` | 네이버 브랜드검색 |
| `nvad:PLINK` | 네이버 파워링크 |
| `nvad:NVSHOP` | 네이버 쇼핑검색 |
| `nvgfa_ad:` | 네이버 GFA 애드부스트 |
| `nvgfa_dp:` | 네이버 GFA 디스플레이 |

## 응답 데이터 구조 (가공 후, 렌더링에 쓰는 최종 형태)

```json
{
  "media_monthly_comparison": [
    {
      "channel_label": "네이버 브랜드검색",
      "rows": [
        { "month_label": "2026년 2월", "cost": 13625164, "revenue": 98613900, "roas": 723.76 },
        { "month_label": "2026년 3월", "cost": 15128305, "revenue": 92365460, "roas": 610.55 }
      ]
    },
    {
      "channel_label": "네이버 파워링크",
      "rows": [
        { "month_label": "2026년 2월", "cost": 3287540, "revenue": 29780150, "roas": 905.85 },
        { "month_label": "2026년 3월", "cost": 3546758, "revenue": 34455750, "roas": 971.47 }
      ]
    }
  ]
}
```
