# Breezm Executive Creative Section 4: 최근 7일 일별 CTR (광고비 상위 5개 소재)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상
포함). `creative`의 section-3과 **완전히 동일한 내용**이다. **메타(Meta Ads)만 대상**이다.
기준일(target_date)을 포함한 **최근 7일** 동안 **광고비(7일 합산)가 가장 큰 소재 5개**를
뽑아, 그 5개의 일별 CTR을 라인 차트로 보여준다.

## MCP 도구 호출: 신규 호출 없음 — section-1과 section-3/4/5 공유 daily_table 응답을 재사용

⚠️ 2026-08-09 (4)부터 이 섹션이 참조하는 응답이 **두 갈래**로 나뉘었다:

1. **소재 선정(광고비 상위 5개)용**: section-1이 이미 호출한 `get_ad_performance_range_table`
   응답(`media="meta"`, `group_by:"ad"`, 최근 7일 — 구간 전체가 소재당 1행으로 이미 합산되어
   있음)을 그대로 재사용한다. 이 응답에는 소재별 7일 합산 `cost`가 이미 들어있으므로,
   재집계 없이 그 값으로 바로 내림차순 정렬해 상위 5개를 뽑는다(아래 "필요 데이터" 참고).
2. **일별 CTR 시리즈용**: SKILL.md 실행 순서 2단계(2-b)에서 section-3/4/5용으로 별도 호출하는
   `get_ad_performance_daily_table` 응답(`media="meta"`, `group_by:"ad"`, 같은 7일 — 날짜별
   행) 중 `media === "meta"`인 행만 걸러서 쓴다. 이 응답은 section-3도 공유한다.

```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```
```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

(위 두 JSON은 파라미터가 같아 보이지만 **서로 다른 도구**를 가리킨다 — 1번은
`get_ad_performance_range_table`, 2번은 `get_ad_performance_daily_table`이다. 이미 다른
섹션이 호출해서 얻은 응답을 재사용하는 것뿐이지, 이 섹션이 새로 2회 호출하는 게 아니다.)

- 이 섹션이 걸러낸 daily meta 행은 **section-5(일별 ROAS)도 그대로 재사용한다** — section-5는
  별도로 다시 걸러내지 않는다.
- daily meta 행에는 날짜별·소재(`campaign_name`+`asset_group`+`ad_name`)별 `cost`/`impression`/
  `click`/`ctr`이 들어있다. `ctr` 필드가 이미 계산되어 있으므로 그대로 쓴다(직접 계산하지
  않아도 된다 — 단, 값이 비율(0.021 등)로 오는지 %(2.1 등)로 오는지 실제 응답을 확인해서
  일관되게 ×100 처리 여부를 판단한다).
- ⚠️ `campaign-type` 금지(section-1과 SKILL.md 2단계에서 이미 호출했으므로 여기서는 해당
  사항 없음 — 재사용만 확인). ⚠️ `group_by`는 문자열 `"ad"` 그대로다.

## 필요 데이터

**소재 선정** (7일 전체 합산 기준):
1. section-1의 range_table 응답(소재당 1행, 이미 7일 합산된 `cost` 포함)에서 소재
   (`campaign_name`+`asset_group`+`ad_name`)별 `cost` 값을 그대로 읽는다 — **daily 응답에서
   다시 합산하지 않는다**(2026-08-09 (4) 이전에는 daily 응답의 날짜별 행을 직접 더해야 했지만,
   이제 같은 값이 range_table 응답에 이미 합산되어 있다).
2. 그 `cost` 내림차순으로 상위 5개 소재를 뽑는다. **이 5개 목록은 section-5에서도 동일하게
   재사용한다** — section-4와 section-5의 라인 색상·범례 순서가 일치해야 한다.
3. **표시 이름 결정**: 선정된 5개 소재 중 `ad_name`이 서로 같은 소재가 있으면(광고그룹이 달라
   같은 소재명을 재사용한 경우), 그 소재들의 표시 이름만 `{ad_name} ({asset_group})` 형식으로
   바꿔 괄호 안에 광고그룹 이름을 추가해 구분한다. `ad_name`이 5개 중 유일하면 그대로 `ad_name`만
   표시한다(불필요하게 모든 이름에 괄호를 붙이지 않는다). 이 표시 이름을 범례·tooltip에 그대로
   쓴다.
4. 위에서 뽑은 5개 소재의 정확한 키(`campaign_name`+`asset_group`+`ad_name`)를 daily meta
   응답에서 **exact-match로 걸러낸다** — 전체 소재를 열어서 다시 랭킹을 매기는 게 아니라,
   이미 알고 있는 5개 키와 정확히 일치하는 행만 뽑는 닫힌 추출이다(최대 5×7=35행). 이 5개
   키에 해당하는 날짜별 행이 "일별 시리즈"의 원본이 된다.

**일별 시리즈** (선정된 5개 소재 각각에 대해):
- 날짜별 `CTR` = 그 날짜 행의 `ctr` 필드(또는 `click`÷`impression`×100). 그 날짜에 노출이
  0이면 해당 포인트는 `null`로 둔다(0으로 채우지 않는다 — 차트에서 끊긴 구간으로 표시됨).
- 7일 중 특정 날짜에 해당 소재의 행 자체가 없으면(그 날 광고가 게재되지 않음) 그 날짜도
  `null`로 둔다.

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM EXECUTIVE CREATIVE SECTION 4: 최근 7일 일별 CTR (광고비 상위 5개 소재) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title" style="text-align:left;">최근 7일 일별 CTR (광고비 상위 5개 소재)</div>
  <div style="position:relative; height:300px;">
    <canvas id="creativeCtrLineChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Breezm Executive Creative Section 4: 일별 CTR 라인차트
(function(){
  const ctx = document.getElementById('creativeCtrLineChart');
  if(!ctx) return;
  const labels = {CREATIVE_7DAY_LABELS}; // 예: ["7/9","7/10",...,"7/15"] — [날짜,요일] 배열이 아니라 단순 M/D 문자열
  const names = {CREATIVE_TOP5_NAMES}; // 상위 5개 소재의 표시 이름 배열 (광고비 내림차순) — ad_name 중복 시 "ad_name (asset_group)", 유일하면 ad_name만
  const series = {CREATIVE_CTR_SERIES}; // names와 같은 순서의 2차원 배열, 각 행이 7개 값(또는 null)

  const palette = ['#3b82f6','#16a34a','#ef4444','#f59e0b','#8b5cf6'];

  new Chart(ctx, {
    type:'line',
    data:{
      labels: labels,
      datasets: series.map((d,i)=>({
        label: names[i], data:d,
        borderColor: palette[i], backgroundColor:'transparent',
        pointBackgroundColor: palette[i], tension:0.3, spanGaps:false
      }))
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{ display:true, position:'bottom', labels:{ boxWidth:10, font:{size:11} } },
        tooltip:{ callbacks:{ label: c => `${c.dataset.label}: ${c.parsed.y}%` } }
      },
      scales:{
        y:{ ticks:{ callback: v => v+'%' } },
        x:{ title:{ display:true, text:'day' } }
      }
    }
  });
})();
```

## 렌더링 규칙
- 라인 5개, 색상은 `palette` 순서 고정(`#3b82f6`/`#16a34a`/`#ef4444`/`#f59e0b`/`#8b5cf6`).
  범례는 차트 하단, Chart.js 기본 legend를 그대로 쓴다(다른 섹션들의 커스텀 legend와 달리
  이 섹션은 라인이 5개라 기본 legend로 충분하다).
- Y축은 `%` 접미사, X축 제목은 `day`.
- 특정 날짜에 데이터가 없는 소재는 그 지점을 이어붙이지 않는다(`spanGaps:false`) — 값을
  추정해서 이어 그리지 않는다.
- 데이터가 비어있으면(7일 내 유효한 소재가 하나도 없음) "데이터 준비 중" 카드로 대체하고
  임의로 채우지 않는다.