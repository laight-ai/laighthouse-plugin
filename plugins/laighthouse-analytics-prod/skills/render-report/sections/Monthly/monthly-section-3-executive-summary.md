# Monthly Section 3: Executive Summary

**report_type:** `monthly` (항상 포함) — naver 기반 default generator 브랜드 전용(남양유업 등).

mtd(MK)의 `mtd-section-3-executive-summary.md`와 HTML 골격은 동일하지만, **톤과 분석 대상이
다르다**:
- mtd는 "월 초부터 현재까지"의 MTD 페이싱(예산 소진 속도, 매출 발생 추이)에 초점을 맞춘
  실무적·구체적 톤이다.
- monthly는 **월이 이미 끝난 뒤의 회고(full month)**이므로, 페이싱 언급 대신 "이번 달 목표
  달성 여부", "전월 대비 트렌드", "다음 달을 위한 시사점" 위주의 **하이레벨(high-level)** 톤으로
  쓴다. 문장 수는 mtd보다 적게 유지하고, 세부 수치 나열보다 해석·시사점에 무게를 둔다.

---

## 텍스트 생성: 아래 사항을 모두 준수하여, AI가 직접 작성 (`df_dify` MCP 호출 안 함)

⚠️ **`df_dify` MCP 서버는 현재 호출하지 않는다** (연결 불안정으로 타임아웃 시 빈 응답이 돌아옴).

```
작성 순서:
1. 수치 데이터 수집 — 모두 별도 재호출 없이 이미 다른 섹션에서 받은 응답을 재사용한다:
   - monthly-section-2(목표 달성 현황)의 get_naver_target_progress 응답
   - monthly-section-4(월별 광고 성과 차트)의 get_naver_monthly_ad_performance 응답 (최근 6개월 추이)
   - monthly-section-6(카테고리별 월간 매출액 비교)의 가공된 상위 5개+기타 비교 데이터
   - monthly-section-8(매체별 성과 비교)의 채널별 이번달/전월 비교 데이터
2. dify 호출 없이, 1의 수치 데이터를 근거로 AI가 executive_summary 텍스트를 직접 작성한다.
   단, 아래 <분석 항목>을 반드시 포함하되, mtd보다 짧고 하이레벨하게 쓴다 (각 항목 1문장,
   전체 5~7문장 이내).

<분석 항목>:
1. 이번 달 ROAS가 목표를 상회·근접·하회했는지 핵심 수치와 함께 총평한다. monthly-section-2(목표 달성 현황)의 지표를 그대로 읽지 않는다. 대신, 전월과 비교하여 얼마나 개선/악화되었는지를 간결하게 기술한다.
2. 최근 6개월(monthly-section-4) 추이에서 이번 달이 어떤 국면(상승/하락/정체)에 있는지 한 문장으로 짚는다.
3. monthly-section-6(카테고리별 비교)에서 가장 눈에 띄는 카테고리 트렌드(급성장 또는 둔화) 하나를 기술한다.
4. monthly-section-8(매체별 비교)에서 채널 효율(ROAS) 변화 중 눈에 띄는 하나를 기술한다.
5. (선택) 다음 달 운영 방향에 대한 간단한 제언 한 문장 — 새로운 수치를 지어내지 않고, 위에서 언급한 트렌드에 근거한 방향성만 제시한다. (예: "예산 재조정을 검토할 필요가 있다" 등) 단, truism으로 느껴지지 않도록 구체적인 지표를 근거로 들어 설명한다.  
```

---

## 응답 데이터 구조

```json
{
  "executive_summary": "이번 파트너 마케팅 성과는 전반적으로 견조했습니다. 광고비를 목표 수준인 약..."
}
```

- `executive_summary` 값이 문자열이면 그대로 `<p>`로 렌더링
- 줄바꿈(`\n`) 기준으로 분리하여 각 줄을 `<li>`로 렌더링

---

## HTML

```html
<!-- MONTHLY SECTION 3: Executive Summary -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Executive Summary</div>
  <ul style="padding-left:20px; line-height:1.9; font-size:13px; color:#374151;">
    <!-- executive_summary를 줄바꿈 기준으로 분리하여 <li>로 렌더링 -->
    {EXECUTIVE_SUMMARY_ITEMS}
  </ul>
</div>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- `executive_summary` 문자열을 `\n` 기준으로 split → 각 줄을 `<li>` 태그로 변환
- 빈 줄은 건너뜀
- `⚠`로 시작하는 항목(주의/관찰 사항)은 `color:#d97706` (주황) 처리
- 강조 수치는 `<strong>` 태그 사용
- mtd와 달리 "MTD 페이싱", "월 초부터 현재까지" 같은 부분월 표현을 쓰지 않는다 — monthly는
  항상 완결된 한 달을 다룬다.