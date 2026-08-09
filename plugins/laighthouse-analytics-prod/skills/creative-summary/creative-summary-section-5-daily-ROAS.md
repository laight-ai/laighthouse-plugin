# Breezm Executive Creative Section 5: 최근 7일 일별 ROAS (광고비 상위 5개 소재)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상
포함). `creative`의 section-4와 **완전히 동일한 내용**이다. **메타(Meta Ads)만 대상**이다.
**section-4와 동일한 상위 5개 소재**(7일 합산 광고비 기준)의 일별 ROAS를 라인 차트로
보여준다 — 소재 선정과 매체 쪽 데이터는 section-4의 결과를 그대로 재사용하고, 이 섹션은
airbridge 매출만 추가로 조회한다.

## MCP 도구 호출: 신규 호출 없음 — section-3/4/5 공유 daily_table 응답을 그대로 재사용

⚠️ 2026-08-09 (4)부터 이 응답은 section-1이 아니라 SKILL.md 실행 순서 2단계(2-b)에서
section-3/4/5용으로 별도 호출하는 `get_ad_performance_daily_table`에서 나온다(section-1은
이제 `get_ad_performance_range_table`을 쓰고, 그 응답은 소재당 1행으로 날짜가 무너져 있어
이 섹션의 "일별 ROAS"에는 쓸 수 없다). 이 섹션은 그 2-b 응답 중 `media="airbridge"` 응답을
그대로 재사용한다 — **다시 호출하지 않는다**:

```json
{ "brand_name": "breezm", "media": "airbridge", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

- 이 응답에서 `media === "airbridge"`인 행만 걸러서 쓴다.
- **`media === "meta"` 쪽 행(section-4가 이미 걸러낸 것)도 재사용한다** — 이 섹션에서 다시
  걸러내지 않는다. 두 필터링 모두 SKILL.md 2단계(2-b)에서 받은 같은 daily_table 원본 응답에서
  나온다.
- 기간은 section-4와 정확히 동일한 7일이다.
- airbridge 행에는 날짜별·소재(`campaign_name`+`asset_group`+`ad_name`)별
  `airbridge_revenue`가 들어있다 — **소재(ad) 단위까지 매출이 정상 귀속됨을 확인했다**
  (2026-08-03).
- ⚠️ `campaign-type` 금지(SKILL.md 2단계에서 이미 호출했으므로 여기서는 해당 사항 없음 —
  재사용만 확인). ⚠️ `group_by`는 문자열 `"ad"` 그대로다.

## 필요 데이터

**소재 선정**: section-4에서 이미 뽑은 **7일 합산 광고비 상위 5개 소재**(section-1의
range_table 응답에서 뽑은 것, section-4 파일 참고)를 그대로 쓴다 — 다시 계산하지 않는다.
라인 색상·범례 순서도 section-4와 동일하게 맞춘다. **표시 이름**(ad_name 중복 시
`ad_name (asset_group)`으로 구분한 이름)도 section-4에서 이미 정한 것을 그대로 재사용한다 —
다시 판단하지 않는다.

**일별 시리즈** (선정된 5개 소재 각각에 대해, 이미 알고 있는 정확한 키로 daily 응답에서
exact-match 필터링 — 전체 소재를 다시 랭킹 매기지 않는 닫힌 추출):
- **조인**: `campaign_name`+`asset_group`+`ad_name` 세 필드가 정확히 일치하는 날짜의
  airbridge 행을 찾아 `airbridge_revenue`를 가져온다. section-4에서 쓴 같은 소재의 같은
  날짜 `cost`(메타 쪽)를 분모로 쓴다.
- 날짜별 `ROAS` = 그 날짜 `airbridge_revenue` ÷ 그 날짜 `cost` × 100.
- 그 날짜에 매체 쪽 `cost`가 0이거나 없으면, 또는 airbridge 쪽에 그 날짜·그 소재의 매출 행이
  없으면(조인 실패) 그 날짜의 ROAS는 **`0`으로 채운다**(끊긴 구간으로 남기지 않는다 —
  차트에서 선이 끊기지 않고 0%까지 내려갔다가 다시 이어지는 형태로 보이게 한다).

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM EXECUTIVE CREATIVE SECTION 5: 최근 7일 일별 ROAS (광고비 상위 5개 소재) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title" style="text-align:left;">최근 7일 일별 ROAS (광고비 상위 5개 소재)</div>
  <div style="position:relative; height:300px;">
    <canvas id="creativeRoasLineChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Breezm Executive Creative Section 5: 일별 ROAS 라인차트
(function(){
  const ctx = document.getElementById('creativeRoasLineChart');
  if(!ctx) return;
  const labels = {CREATIVE_7DAY_LABELS}; // section-4와 동일한 배열, 예: ["7/9",...,"7/15"]
  const names = {CREATIVE_TOP5_NAMES}; // section-4와 동일한 5개 소재의 표시 이름(같은 순서, ad_name 중복 시 "ad_name (asset_group)" 포함)
  const series = {CREATIVE_ROAS_SERIES}; // names와 같은 순서의 2차원 배열, 각 행이 7개 값(매출 매칭 실패/광고비 0인 날짜는 0으로 채움)

  const palette = ['#3b82f6','#16a34a','#ef4444','#f59e0b','#8b5cf6'];

  new Chart(ctx, {
    type:'line',
    data:{
      labels: labels,
      datasets: series.map((d,i)=>({
        label: names[i], data:d,
        borderColor: palette[i], backgroundColor:'transparent',
        pointBackgroundColor: palette[i], tension:0.3
      }))
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{ display:true, position:'bottom', labels:{ boxWidth:10, font:{size:11} } },
        tooltip:{ callbacks:{ label: c => `${c.dataset.label}: ${c.parsed.y}%` } }
      },
      scales:{
        y:{ min:0, ticks:{ callback: v => v+'%' } },
        x:{ title:{ display:true, text:'day' } }
      }
    }
  });
})();
```

## 렌더링 규칙
- 라인 5개, **색상·범례 순서는 section-4와 정확히 동일하게** 맞춘다(같은 `palette` 순서,
  같은 소재 순서) — 두 차트를 나란히 볼 때 같은 색이 같은 소재를 가리켜야 한다.
- Y축은 `%` 접미사, X축 제목은 `day`. Y축 최소값은 `0`으로 고정한다(`min:0`).
- 매출 매칭이 안 되거나 광고비가 0인 날짜는 **`0`으로 채운다** — 끊긴 구간으로 남기지
  않는다. 선이 0%까지 내려갔다가 다시 이어지는 형태로 자연스럽게 보이게 한다.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 소재명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — `campaign_name`+`asset_group`+
  `ad_name` 세 필드 정확 일치만 쓴다.