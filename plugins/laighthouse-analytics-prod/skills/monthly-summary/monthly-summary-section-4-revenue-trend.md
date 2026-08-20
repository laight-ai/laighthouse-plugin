# Breezm Executive Monthly Section 4: 매출 추이 (Revenue Trend)

**report_type:** `monthly-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
최근 6개월(당월 포함) 라인 차트. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ⚠️ **ELT 이관 후 알려진 제약**: 이 차트의 `total_revenue`(오거닉 포함 전체 매출)는 현재
> 데이터 소스(ELT 광고 성과 — 광고 귀속 지표만 제공)에서 얻을 수 없다. 광고 매출을 전체
> 매출로 지어 넣지 말고, **`s4` 키를 빌더 입력에서 빼서 "데이터 준비 중" 카드로 렌더링한다.**
> 서버가 전체 매출 지표를 다시 제공하면 아래 규칙을 복원한다.

> ℹ️ 차트 HTML/Script/각주 3줄(MTD 문구, '전체 매출' 정의 고정 문구, zero-fill 고정 문구)/
> 라벨은 전부 템플릿+빌더가 처리한다 — 모델은 **6개월치 배열 2개**만 빌더 입력 JSON의 `s4`에
> 넣는다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

`monthly-summary-section-3-monthly-ad-performance.md`가 1회 호출한 `get_ad_performance`
(`media` 생략, `time_grain:"month"`, `group_by:["media"]`, 5개월 전~당월,
`day_offset`=target_date.day) 응답에서 월별 `매출_AB` 합(= 광고 매출)을 얻을 수 있다.

## 빌더 `s4` 필드 — 현재는 사용하지 않는다 (위 제약 참고)

빌더 스키마는 `ad_revenue`/`total_revenue`(각 6개)/`labels`지만, `total_revenue` 소스가 없는
동안은 **`s4` 키 자체를 넣지 않는다** → "데이터 준비 중" 카드. `ad_revenue`만으로 차트를
채우거나 `total_revenue`에 광고 매출을 복사해 넣는 것은 금지다(전체 매출 정의 왜곡).
