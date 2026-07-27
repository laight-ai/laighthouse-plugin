# MTD-type-b Section 1: 목표 달성 현황

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 분기 A(naver 기반 브랜드)는
`sections/mtd/`를 쓴다. 모든 "매출"은 Airbridge 매출(`airbridge_revenue`), 광고 채널은 airbridge
응답 `channel` ∈ {`Google Ads`, `Meta Ads`, `Naver Ads`} 행이다 (SKILL.md 분기 B 공통 규칙 참고).

---

## MCP 도구 호출: `get_target_progress_v2` × 3 (media만 바꿔 반복)

```json
{ "brand_name": "브리즘", "month": "YYYY-MM", "media": "google", "as_of_date": "target_date" }
{ "brand_name": "브리즘", "month": "YYYY-MM", "media": "meta", "as_of_date": "target_date" }
{ "brand_name": "브리즘", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. 해당 매체 예산(media_mix)이
> 없으면 예외 대신 `"No {media} budget/target available for {month}."` 메시지 한 줄이 반환된다 —
> **type-b 브랜드는 현재 media_mix 데이터가 없어 세 매체 모두 이 메시지가 오는 것이 기대 상태다. 오류로
> 취급하지 않는다.**

이 세 응답은 섹션 6(Channel별 예산 소진 현황)이 그대로 재사용한다 — 별도 재호출 없음.

## 목표가 있는 경우 (하나 이상의 매체가 표를 반환)

표를 반환한 매체들의 값을 합산한다:
- `목표 예산` = 각 응답 cost 행 target 합 / `소진액` = cost 행 actual 합
- `목표 매출` = revenue 행 target 합 / `기간 매출` = revenue 행 actual 합
- `소진율` = 소진액 ÷ 목표 예산 × 100
- `매출 달성률` = 기간 매출 ÷ 목표 매출 × 100
- `목표 ROAS` = 목표 매출 ÷ 목표 예산 × 100
- `실제 ROAS` = 기간 매출 ÷ 소진액 × 100
- 일부 매체만 예산이 있으면 있는 매체 합으로 계산하고, 예산 없는 매체를 카드 아래 각주로 명시한다.

## 목표가 없는 경우 (세 매체 모두 no-budget 메시지)

목표 관련 값(`목표 예산`/`목표 매출`/`소진율`/`매출 달성률`/`목표 ROAS`)은 전부 **N/A**로 표시하고,
실적만 `get_ad_performance_daily_table`(MTD: `start_date`=월초, `end_date`=target_date)에서 가져온다:
- `소진액` = `media="google"`/`"meta"`/`"naver"` 각 1회(`group_by: "total"`)의 cost 합
- `기간 매출` = `media="airbridge"`, `group_by: "media"` 응답에서 광고 채널
  (`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `실제 ROAS` = 기간 매출 ÷ 소진액 × 100

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.

---

## HTML

```html
<!-- MTD-TYPE-B SECTION 1: 목표 달성 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">목표 달성 현황 (MTD)</div>
  <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 예산대비 소진율</div>
      <div style="font-size:28px; font-weight:700; color:#3b82f6; margin-bottom:12px;">{소진율}</div>
      <div style="display:flex; justify-content:center; gap:16px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표 예산</div><div style="font-weight:600;">{목표_예산}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">소진액</div><div style="font-weight:600;">{소진액}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">기간 목표 매출 대비 달성률</div>
      <div style="font-size:28px; font-weight:700; color:#16a34a; margin-bottom:12px;">{매출_달성률}</div>
      <div style="display:flex; justify-content:center; gap:16px; font-size:12px;">
        <div><div style="color:#94a3b8;">목표 매출</div><div style="font-weight:600;">{목표_매출}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">기간 매출</div><div style="font-weight:600;">{기간_매출}</div></div>
      </div>
    </div>

    <div style="padding:20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">목표 ROAS</div>
      <div style="font-size:28px; font-weight:700; color:#64748b; margin-bottom:12px;">{목표_ROAS}</div>
    </div>

    <div style="padding:20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">실제 ROAS</div>
      <div style="font-size:28px; font-weight:700; color:#7c3aed; margin-bottom:12px;">{실제_ROAS}</div>
    </div>

  </div>
</div>
```

## Script
없음 (정적 카드)

## 렌더링 규칙
- 값 표기: 비율/ROAS는 % 소수점 1자리, 금액은 천 단위 콤마 원화. N/A인 값은 문자 그대로 `N/A`.
- no-budget 메시지는 오류가 아니다 — "데이터 준비 중" 카드로 대체하지 않고 N/A 규칙대로 렌더링한다.
- airbridge 응답의 실제 `channel` 값이 상수(`Google Ads`/`Meta Ads`/`Naver Ads`)와 다르면 조용히
  0을 만들지 말고 카드 아래에 불일치를 명시한다.
