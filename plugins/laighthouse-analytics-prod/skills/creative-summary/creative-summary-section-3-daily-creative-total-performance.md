# Breezm Executive Creative Section 3: 최근 7일 전체 소재 CTR 및 ROAS

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
**메타(Meta Ads)만 대상**이다. `creative`에는 없는 신규 섹션이다. section-4/5(광고비 상위
5개 소재만 다룸)와 달리, **모든 소재를 날짜별로 합산**해서 전체 CTR·전체 ROAS의 7일 추이를
보여준다. ⚠️ **두 지표를 하나의 듀얼 Y축 차트로 합치지 않는다** — CTR(1%대)과 ROAS(150~
200%대)는 스케일이 완전히 달라서, 한 차트에 억지로 겹치면 두 선이 교차하는 지점이 마치
의미 있는 관계처럼 보이는 착시가 생긴다(실제로는 스케일이 달라 교차 자체에 의미가 없다).
대신 **CTR 카드와 ROAS 카드를 별도로** 만들어, 각자 자기 스케일에 맞는 축 하나만 쓴다.

## MCP 도구 호출: 신규 호출 없음 — section-3/4/5가 공유하는 daily_table 응답을 그대로 재사용

⚠️ 2026-08-09 (4)부터 section-1은 `get_ad_performance_range_table`(구간 전체를 소재당 1행으로
합산해 돌려주는 도구)로 바뀌어서, 더 이상 이 섹션이 필요한 **날짜별** 행을 주지 않는다 —
이 섹션은 여전히 날짜별 CTR/ROAS 추이가 목적이므로 range_table로는 대체할 수 없다. 대신
SKILL.md 실행 순서 2단계(2-b)에서 section-3/4/5용으로 별도 호출하는
`get_ad_performance_daily_table`(`media="meta"`/`media="airbridge"` 각 1회, `group_by: "ad"`,
최근 7일)을 section-4/5가 걸러낸 `media === "meta"`/`media === "airbridge"` 행 그대로
재사용한다 — **이 섹션에서 다시 호출하지 않는다**:

```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```
```json
{ "brand_name": "breezm", "media": "airbridge", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

(참고: section-4/5는 이 응답의 `meta` 행에서 "광고비 상위 5개 소재"만 뽑아 썼지만(그 상위
5개 소재의 식별에는 이제 section-1의 range_table 응답을 쓴다 — section-4 파일 참고), 이
섹션은 **`meta` 행에 들어있는 모든 소재 행**(=`creative-detailed`의 section-5 표에 나열되는
소재 전체와 동일한 집합)을 날짜별로 합산한다는 점이 다르다 — 같은 원본 데이터를 다른
방식으로 가공하는 것이다. ⚠️ 단, **매출(airbridge_revenue)만은 무조건 전부 합산하지 않는다**
— 아래 "필요 데이터"의 조인 규칙을 반드시 따른다. `group_by:"ad"` 응답에는 소재(광고) 단위로
성과를 측정하지 않는 캠페인·매체(예: 검색광고)의 행이 애초에 나타나지 않지만, 이는
광고비/노출/클릭에만 해당하는 이야기이고 매출 집계에는 별도의 조인 필터링이 필요하다.)

⚠️ **이 섹션은 section-4/5와 달리 여전히 전체 소재에 대한 완전한 집계가 필요하다** — "상위
5개"로 좁힐 수 없고(전체 CTR/ROAS 추이가 목적) 날짜별로 **모든** 소재 행을 합산해야 하므로,
SKILL.md의 Bash 집계 필수 규칙이 이 섹션에는 그대로 전체 범위로 적용된다(section-4/5처럼 5개
키로 좁혀지는 예외에 해당하지 않는다).

## 계산: `assets/creative_daily_series.py` 호출 (필수)

이 섹션이 필요로 하는 "모든 소재를 날짜별로 합산 → CTR/ROAS" 계산은 미리 검증된 asset
스크립트 `assets/creative_daily_series.py`로 옮겨져 있다. ⚠️ **`get_ad_performance_daily_table`은
JSON 행 배열이 아니라 마크다운 표(파이프 `|` 텍스트) 문자열을 반환한다** — 그 원본을 손으로
JSON으로 옮겨 적거나(전사 실수·행 선별 위험) 파싱용 스크립트를 새로 만들지 않는다. 위에서 받은
`media="meta"`/`media="airbridge"` 두 응답 문자열을 **가공 없이 원본 그대로**
`meta_markdown`/`airbridge_markdown`에 넣어 stdin으로 넘기면, 스크립트가 직접 파싱하고
`overall.ctr_series`/`overall.roas_series`(날짜별, 아래 "필요 데이터"의 조인·null 규칙이 이미
반영된 값)를 돌려준다. 손으로 조인·합산하거나 즉석 Bash로 다시 계산하지 않는다 — 이 스크립트를
호출하는 것 자체가 SKILL.md § 실행 방식 절대 지침의 "이미 존재하는 검증된 asset 스크립트 호출은
파일 생성 금지의 예외"에 해당한다.

```bash
python3 <스킬 폴더>/assets/creative_daily_series.py <<'EOF'
{"meta_markdown": "<media=\"meta\" 응답 원본 문자열>", "airbridge_markdown": "<media=\"airbridge\" 응답 원본 문자열>",
 "dates": ["기준일 6일 전", ..., "target_date"]}
EOF
```

⚠️ **응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽어서 스크립트를 실행하지 않는다** — 위처럼
따옴표 있는 heredoc(`<<'EOF'`) 하나로 응답을 받은 바로 그 Bash 호출 안에서 한 번에 끝낸다.
`echo '...'`는 크고 줄바꿈·따옴표가 많은 마크다운 응답에서 셸 이스케이프가 깨지기 쉬워서 쓰지
않는다.

출력의 `dates`/`overall.ctr_series`/`overall.roas_series`를 그대로
`{CREATIVE_7DAY_LABELS_WITH_WEEKDAY}`(날짜에 요일을 붙여 표기만 변환)·`{OVERALL_CTR_SERIES}`·
`{OVERALL_ROAS_SERIES}` 자리에 쓴다. section-4/5가 필요로 하는 `top5` 시리즈는 이 섹션에서는
`top5_keys`를 넘기지 않아도 되므로(이 섹션은 전체 소재만 필요) 생략 가능하다 — 단, 한 번의
호출로 section-3/4/5를 모두 처리하고 싶다면 `top5_keys`(section-4 파일이 정하는 상위 5개
키)를 함께 넘겨 한 번에 받아도 된다.

## 필요 데이터 (계산 명세 — 위 스크립트가 이미 구현한 로직의 참고용 스펙, 날짜별·모든 소재 합산)

각 날짜(7일 전체)에 대해:
- `전체 광고비` = 그 날짜 `meta` 응답의 **모든 소재 행** `cost` 합
- `전체 노출` = 그 날짜 `meta` 응답의 **모든 소재 행** `impression` 합
- `전체 클릭` = 그 날짜 `meta` 응답의 **모든 소재 행** `click` 합
- `전체 매출` = 그 날짜 `meta` 응답에 존재하는 소재(`campaign_name`+`asset_group`+`ad_name`)와
  **같은 소재의 같은 날짜 행만 골라서**, 그 날짜 `airbridge` 응답의 `airbridge_revenue`를
  합산한다.
  ⚠️ **airbridge 응답의 행을 무조건 전부 합산하지 않는다** — 그 날짜 `meta` 응답에 없는
  소재(= 매체 쪽에서 측정되지 않는 소재)의 airbridge 매출은 이 합계에서 **제외**한다. 이렇게
  해야 "전체 매출"이 가리키는 소재 집합이 `creative-detailed`의 section-5(최근 7일 소재 단위
  누적 성과) 표에 포함되는 소재 집합과 정확히 일치한다 — section-5도 airbridge 쪽에만 있고
  매체 쪽에 없는 소재는 표에서 아예 제외하는 동일한 원칙을 이미 쓰고 있다(위 "조인" 규칙
  참고).
  - 조인 기준은 다른 섹션과 동일하게 `campaign_name`+`asset_group`+`ad_name` **세 필드
    모두 정확히 일치**해야 같은 소재로 본다.

**파생 지표** (날짜별로 각각 계산):
- `전체 CTR` = 전체 클릭 ÷ 전체 노출 × 100 (노출 합이 0이면 그 날짜는 `null`)
- `전체 ROAS` = 전체 매출 ÷ 전체 광고비 × 100 (광고비 합이 0이면 그 날짜는 `null`)

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다(section-4/5에서 이미 호출했으므로 여기서는
해당 사항 없음 — 재사용만 확인).

## HTML

```html
<!-- BREEZM EXECUTIVE CREATIVE SECTION 3-1: 최근 7일 전체 소재 CTR -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title" style="text-align:left;">최근 7일 전체 소재 CTR</div>
  <div style="position:relative; height:260px;">
    <canvas id="overallCtrChart"></canvas>
  </div>
  <p style="font-size:11px; color:#64748b; margin-top:14px; line-height:1.5;">
    * 위 차트에 포함된 CTR는 개별 소재 성과의 합계입니다. 이미지나 비디오 소재 단위에서
    성과를 측정하지 않는 매체나 캠페인의 성과는 포함하지 않습니다. (예: 검색광고)
  </p>
</div>

<!-- BREEZM EXECUTIVE CREATIVE SECTION 3-2: 최근 7일 전체 소재 ROAS -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title" style="text-align:left;">최근 7일 전체 소재 ROAS</div>
  <div style="position:relative; height:260px;">
    <canvas id="overallRoasChart"></canvas>
  </div>
  <p style="font-size:11px; color:#64748b; margin-top:14px; line-height:1.5;">
    * 위 차트에 포함된 ROAS는 개별 소재 성과의 합계입니다. 이미지나 비디오 소재 단위에서
    성과를 측정하지 않는 매체나 캠페인의 성과는 포함하지 않습니다. (예: 검색광고)
  </p>
</div>
```

## Script

```javascript
// Breezm Executive Creative Section 3: 전체 CTR / 전체 ROAS — 별도 단일축 라인차트 2개
(function(){
  const labels = {CREATIVE_7DAY_LABELS_WITH_WEEKDAY}; // 예: ["7/19(일)","7/20(월)",...,"7/25(토)"] — 날짜+요일 한 줄 문자열
  const ctrSeries = {OVERALL_CTR_SERIES}; // 7개 값(또는 null), %
  const roasSeries = {OVERALL_ROAS_SERIES}; // 7개 값(또는 null), %

  // 값이 좁게 몰려 있어도(예: 1.51~1.60%) Y축이 최소 폭(minSpan)을 갖도록 min/max를
  // 계산한다 — 그대로 자동 계산에 맡기면 눈금이 2개뿐인 부자연스러운 축이 나올 수 있다.
  function calcPaddedRange(values, minSpan, step) {
    const valid = values.filter(v => v !== null && v !== undefined);
    const dataMin = Math.min(...valid);
    const dataMax = Math.max(...valid);
    let min = dataMin - minSpan * 0.375;
    let max = dataMax + minSpan * 0.375;
    if (max - min < minSpan) {
      const mid = (min + max) / 2;
      min = mid - minSpan / 2;
      max = mid + minSpan / 2;
    }
    min = Math.floor(min / step) * step;
    max = Math.ceil(max / step) * step;
    return { min, max };
  }

  // CTR 차트
  const ctrCtx = document.getElementById('overallCtrChart');
  if (ctrCtx) {
    const range = calcPaddedRange(ctrSeries, 0.8, 0.1);
    new Chart(ctrCtx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: '전체 CTR', data: ctrSeries,
          borderColor: '#3b82f6', backgroundColor: 'transparent',
          pointBackgroundColor: '#3b82f6', tension: 0.3, spanGaps: false
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => `전체 CTR: ${Number(c.parsed.y).toFixed(1)}%` } }
        },
        scales: {
          y: { min: range.min, max: range.max,
               ticks: { stepSize: 0.1, callback: v => Number(v).toFixed(1) + '%' } },
          x: { ticks: { maxRotation: 0, minRotation: 0 } }
        }
      }
    });
  }

  // ROAS 차트
  const roasCtx = document.getElementById('overallRoasChart');
  if (roasCtx) {
    new Chart(roasCtx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: '전체 ROAS', data: roasSeries,
          borderColor: '#ef4444', backgroundColor: 'transparent',
          pointBackgroundColor: '#ef4444', tension: 0.3, spanGaps: false
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => `전체 ROAS: ${Number(c.parsed.y).toFixed(1)}%` } }
        },
        scales: {
          y: { ticks: { callback: v => Number(v).toFixed(1) + '%' } },
          x: { ticks: { maxRotation: 0, minRotation: 0 } }
        }
      }
    });
  }
})();
```

## 렌더링 규칙
- **CTR과 ROAS는 별도의 카드 + 별도의 차트로 나눈다** — 하나의 차트에 듀얼 Y축으로 합치지
  않는다 — 스케일이 달라 두 선의 교차가 착시를 줄 수 있다. 카드 순서는
  CTR → ROAS 순으로 고정한다.
- 각 차트는 **범례를 별도로 두지 않는다** — 카드 제목("최근 7일 전체 소재 CTR" 등) 자체가
  그 차트가 무슨 지표인지 알려주므로, Chart.js 기본 legend도 숨긴다
  (`plugins.legend.display:false`).
- **CTR 차트의 Y축은 값이 좁게 몰려 있어도 최소 폭(0.8%p)을 보장**하고 `stepSize:0.1`로
  0.1% 단위 눈금을 쓴다 — 데이터가 예를 들어 1.51~1.60%처럼 아주 좁은 범위에 몰려 있으면
  자동 계산 축은 눈금이 1~2개뿐인 부자연스러운 그래프가 될 수 있다. 위 Script의
  `calcPaddedRange` 함수를 그대로 쓴다. 정확한 수치 확인이 아니라 추이 확인이 목적이므로
  위아래 여백이 남는 것은 허용한다.
- **ROAS 차트는 자체 스케일 그대로 자동 계산에 맡긴다** — ROAS는 보통 값 범위가 CTR보다
  넓어서(수십~수백 %) 별도의 최소 폭 보정이 필요 없다.
- **Y축·tooltip 수치는 소수점 첫째 자리로 고정 표기한다**(`Number(v).toFixed(1)+'%'`) —
  부동소수점 연산 오차로 `1.800000000000003%`처럼 표시될 수 있다. 원본
  숫자를 그대로 이어붙이지 않는다.
- **X축에는 "day" 같은 축 제목을 넣지 않는다.** 대신 각 라벨을 `M/D(요일)` 한 줄 형식(예:
  `7/19(일)`)으로 표기한다 — 날짜와 요일을 두 줄로 나누지 않고 한 줄에 합쳐 쓴다(다른
  섹션들의 `[날짜, 요일]` 2줄 배열 방식과 다르다는 점에 유의). 두 차트 모두 같은 라벨
  배열을 쓴다.
- 특정 날짜에 노출 합 또는 광고비 합이 0이면 그 지점을 이어붙이지 않는다(`spanGaps:false`)
  — 값을 추정해서 이어 그리지 않는다.
- **각주는 두 카드 모두에 각각 넣는다** — "위 차트에 포함된 {CTR 또는 ROAS}는 개별 소재
  성과의 합계입니다..." 형식으로, 지표명만 그 카드에 맞게 바꿔서 각각 표시한다(공통 각주를
  한쪽 카드에만 몰아넣지 않는다).
- ROAS 차트에는 선 아래 음영(area fill)을 넣지 않는다 — 두 차트 모두 단순 선 차트로 통일한다.
- 데이터가 비어있으면(7일 내 유효한 소재가 하나도 없음) "데이터 준비 중" 카드로 대체하고
  임의로 채우지 않는다.