# Breezm Executive Creative Section 1: 최우수 소재 (ROAS / CTR, 최근 7일 기준)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
`creative`의 section-1과 **완전히 동일한 내용**이다. **메타
(Meta Ads)만 대상**이다 — google/naver는 다루지 않는다. 기준일(target_date)을 포함한 **최근
7일**을 통째로 합산해서, 그 기간 소재(개별 광고) 단위 **ROAS 1·2위**와 **CTR 1·2위**를 각각
카드로 보여준다. 날짜별 비교가 아니라 **7일 전체를 하나로 합친 누적 값** 기준이다.

## MCP 도구 호출: `get_ad_performance_range_table` × 2 (`media="meta"` / `media="airbridge"`, `group_by: "ad"`, 최근 7일)

```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```
```json
{ "brand_name": "breezm", "media": "airbridge", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

> ⚡ **2026-08-09 (4)에 `get_ad_performance_daily_table`에서 `get_ad_performance_range_table`로
> 전환했다** — 이 도구는 `start_date`~`end_date` **전체 구간을 소재 단위로 이미 합산해 한
> 행씩** 돌려준다(날짜별 행이 아니다). 이 섹션이 필요한 건 처음부터 "7일 전체를 합친 소재별
> 누적 값"뿐이었으므로, 이 응답은 별도 집계 없이 그 자체가 최종 데이터다 — 아래 "필요
> 데이터"에서 하던 소재별 7일 합산을 이 호출이 대신 해준다. `is_active`는 이 도구에서는 항상
> 비어 있는데(구간 내 상태 변화 가능성 때문), 이 섹션은 애초에 `is_active`를 쓰지 않으므로
> 영향 없음. 기간은 92일까지 지원되며 이 섹션의 7일은 그 안에 넉넉히 들어간다.

- ⚠️ **`media`를 생략하지 않고 `meta`/`airbridge` 각각 명시해서 2회 호출한다** — 이 도구도
  `group_by:"ad"`에서 `media`를 생략하면 다른 매체 행까지 한 응답에 섞여 들어온다(위험 자체는
  `get_ad_performance_daily_table` 때와 동일한 구조). 다만 이 응답은 애초에 날짜별이 아니라
  소재별 1행이라 응답 크기 자체가 daily 대비 훨씬 작다.
- **이 2회 호출 응답은 section-3/4/5와 더 이상 공유되지 않는다** — section-3/4/5는 여전히
  날짜별(일별) 데이터가 필요해서 `get_ad_performance_daily_table`을 별도로 호출한다(SKILL.md
  실행 순서 2단계, section-3/4/5 각 파일의 "MCP 도구 호출" 참고). 단, section-4는 소재 선정
  (광고비 상위 5개)에 필요한 "소재별 7일 합산 cost"를 이 섹션의 range_table 응답에서 그대로
  가져다 쓴다(재계산 불필요) — 자세한 내용은 section-4 파일 참고.
- **랭킹(ROAS/CTR 1·2위 선정)에 더 이상 Bash 집계가 필요 없다** — 응답이 이미 소재당 1행,
  7일 합산 값으로 오므로, ROAS/CTR을 내림차순으로 정렬해 1·2위를 뽑는 것은 그냥 단순 정렬이다
  (아래 "선정 로직" 참고). SKILL.md의 "Bash 집계는 필수 단계다" 규칙은 여전히 유효하지만,
  그건 `get_ad_performance_daily_table`처럼 날짜별로 여러 행이 오는 응답(=section-3/4/5가
  쓰는 응답)에 대한 이야기이고, 이 섹션이 받는 range_table 응답에는 적용할 대상 자체가 없다
  (합칠 날짜별 행이 없다 — 이미 합쳐져서 온다).
- 기간은 기준일을 포함해 정확히 7일이다.
- `media === "meta"` 행에는 소재(`campaign_name`+`asset_group`+`ad_name`)별 **7일 합산**
  `cost`/`impression`/`click`과, 소재 이미지 조회에 필요한 `creative_id`/`platform_account_id`가
  들어있다(소재당 1행이므로 그 행의 값을 그대로 쓴다 — "아무 날짜의 값이나 고른다"는 절차가
  더 이상 필요 없다).
- `media === "airbridge"` 행에는 소재별 **7일 합산** `airbridge_revenue`/`reservation`이
  들어있다. **실제로 소재(ad) 단위까지 매출/예약이 정상 귀속됨을 확인했다**(2026-08-03) —
  캠페인 값을 공유하는 게 아니라 진짜 소재별 값이다.
- ⚠️ `campaign-type` 금지. ⚠️ `group_by`는 문자열 `"ad"` 그대로 보낸다.

## MCP 도구 호출: `get_ad_creative_info` × 1 (최종 선정된 소재만)

```json
{ "brand_name": "breezm", "meta": [ { "account_id": "{platform_account_id}", "creative_id": "{creative_id}" }, ... ] }
```

- **아래 "선정 로직"으로 ROAS 1·2위, CTR 1·2위를 먼저 정하고, 그 소재들의
  `account_id`(=`platform_account_id`)/`creative_id` 쌍만 모아 이 호출 한 번으로 이미지를
  가져온다** — 전체 소재를 다 조회하지 않는다(최대 4개, 중복되는 소재가 있으면 유니크하게
  묶어서 호출).
- 이 호출 결과의 `thumbnail_image_url`만 쓴다. `thumbnail_image_data_url`(base64)은 **쓰지
  않는다** — 사용자가 보고서를 다운로드해서 열 때는 네트워크가 항상 연결되어 있다고 가정하므로
  파일에 이미지를 인라인으로 심어둘 필요가 없다.

## 필요 데이터 (소재별, 최근 7일 합산)

> ℹ️ **`get_ad_performance_range_table` 응답은 이미 소재당 1행으로 7일 합산되어 온다** — 아래
> "합산" 표현은 "여러 날짜 행을 직접 더한다"는 뜻이 아니라 "그 응답 행의 값을 그대로 쓴다"는
> 뜻이다. 별도로 더하거나 집계할 필요가 없다.

**매체 지표** (`meta` 응답의 소재(`campaign_name`+`asset_group`+`ad_name`)별 1행 값):
- `광고비` = `cost` / `노출` = `impression` / `클릭` = `click`
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 이 소재는 CTR 랭킹에서 제외)
- `creative_id`/`platform_account_id`도 그 행의 값을 그대로 쓴다.

**airbridge 지표** (`airbridge` 응답의 같은 소재 단위 1행 값):
- `매출` = `airbridge_revenue` / `예약 완료` = `reservation`

**조인**: `campaign_name`+`asset_group`+`ad_name` **세 필드 모두 정확히 일치**해야 같은
소재로 본다.
- 매체 쪽에만 있는 소재(airbridge 매칭 실패) → 매출 없음 → ROAS 랭킹에서 제외(CTR 랭킹에는
  포함 가능 — CTR은 매출과 무관하다).
- airbridge 쪽에만 있는(매체 쪽에 없는) 소재 → 광고비/CTR을 알 수 없으므로 이 섹션 전체에서
  제외한다.

**파생 지표**:
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 이 소재는 ROAS 랭킹에서 제외)

## 선정 로직

- **ROAS 최우수 소재**: 위에서 구한 소재별 ROAS를 내림차순 정렬해 1·2위를 뽑는다(광고비 0이거나
  매출 매칭이 안 된 소재는 후보에서 제외한다 — 위 규칙 참고).
- **CTR 최우수 소재**: 소재별 CTR을 내림차순 정렬해 1·2위를 뽑는다(노출 0인 소재는 제외).
- 두 랭킹은 서로 독립적이다 — 같은 소재가 ROAS 1위이면서 CTR 1위일 수도 있고, 그래도 그대로
  둔다(임의로 다른 소재로 바꾸지 않는다).
- 유효한 후보가 2개 미만이면(예: ROAS 계산 가능한 소재가 1개뿐) 2위 자리는 `-`로 비워두고
  이미지 셀도 표시하지 않는다.

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM EXECUTIVE CREATIVE SECTION 1: 최우수 소재 (ROAS / CTR, 최근 7일 기준) -->
<div style="display:flex; gap:16px; align-items:stretch;">
  <div class="card" style="flex:1; display:flex; flex-direction:column;">
    <div class="section-title" style="text-align:center;">ROAS 최우수 소재 (최근 7일 기준)</div>
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
      <tr>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;"><strong>{roas_1위_소재명}</strong></td>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;"><strong>{roas_2위_소재명}</strong></td>
      </tr>
      <tr>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;">ROAS: {roas_1위_값}%</td>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;">ROAS: {roas_2위_값}%</td>
      </tr>
      <tr>
        <td style="border:1px solid #e2e8f0; padding:12px; text-align:center;">
          <img style="width:100%; max-width:220px; height:180px; border-radius:8px; object-fit:cover; display:block; margin:0 auto;"
               src="{roas_1위_thumbnail_url}" alt="{roas_1위_소재명} 썸네일"
               onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
          <a href="{roas_1위_thumbnail_url}" target="_blank" style="display:none; color:#2563eb; text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>
        </td>
        <td style="border:1px solid #e2e8f0; padding:12px; text-align:center;">
          <img style="width:100%; max-width:220px; height:180px; border-radius:8px; object-fit:cover; display:block; margin:0 auto;"
               src="{roas_2위_thumbnail_url}" alt="{roas_2위_소재명} 썸네일"
               onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
          <a href="{roas_2위_thumbnail_url}" target="_blank" style="display:none; color:#2563eb; text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>
        </td>
      </tr>
    </table>
    <p style="font-size:11px; color:#64748b; margin-top:12px; line-height:1.5;">*'매출/광고비'로 계산되며, 높을수록 소재에서 매출이 효율적으로 발생하고 있음을 의미합니다.</p>
  </div>

  <div class="card" style="flex:1; display:flex; flex-direction:column;">
    <div class="section-title" style="text-align:center;">CTR 최우수 소재 (최근 7일 기준)</div>
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
      <tr>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;"><strong>{ctr_1위_소재명}</strong></td>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;"><strong>{ctr_2위_소재명}</strong></td>
      </tr>
      <tr>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;">CTR: {ctr_1위_값}%</td>
        <td style="border:1px solid #e2e8f0; padding:10px 12px; text-align:center; vertical-align:middle;">CTR: {ctr_2위_값}%</td>
      </tr>
      <tr>
        <td style="border:1px solid #e2e8f0; padding:12px; text-align:center;">
          <img style="width:100%; max-width:220px; height:180px; border-radius:8px; object-fit:cover; display:block; margin:0 auto;"
               src="{ctr_1위_thumbnail_url}" alt="{ctr_1위_소재명} 썸네일"
               onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
          <a href="{ctr_1위_thumbnail_url}" target="_blank" style="display:none; color:#2563eb; text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>
        </td>
        <td style="border:1px solid #e2e8f0; padding:12px; text-align:center;">
          <img style="width:100%; max-width:220px; height:180px; border-radius:8px; object-fit:cover; display:block; margin:0 auto;"
               src="{ctr_2위_thumbnail_url}" alt="{ctr_2위_소재명} 썸네일"
               onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
          <a href="{ctr_2위_thumbnail_url}" target="_blank" style="display:none; color:#2563eb; text-decoration:underline; font-size:12.5px;">소재 미리보기 →</a>
        </td>
      </tr>
    </table>
    <p style="font-size:11px; color:#64748b; margin-top:12px; line-height:1.5;">*'클릭/노출수'로 계산되며, 높을수록 고객이 광고에 매력을 느껴 클릭하는 경우가 많았음을 의미합니다. 단, CTR이 높아도 구매 전환율은 낮을 수 있으므로 주의가 필요합니다.</p>
  </div>
</div>
```

## Script
없음 (정적 카드 — 이미지 fallback은 순수 HTML `onerror` 속성으로 처리하며 별도 JS가 필요
없다.)

## 렌더링 규칙
- 두 카드는 **가로로 나란히**(`display:flex; gap:16px; align-items:stretch;`) 배치한다.
- **표는 3행 구조로 고정한다**: 1행(소재 이름) → 2행(`{ROAS 또는 CTR}: {값}%`) → 3행(이미지).
  "이름: 값%"처럼 이름과 지표를 한 셀에 합쳐 쓰지 않는다. ⚠️ **1행에는 소재(광고) 이름만
  표시한다** — 그 소재가 속한 캠페인명이나 광고그룹명을 이름 아래에 작은 글씨로 추가로
  붙이지 않는다 — 캠페인명이 회색 작은 글씨로 함께 표시될 수 있다. 이 카드가
  보여주는 건 소재 랭킹이므로, 소재 이름 하나만 깔끔하게 보여준다. **1행·2행 모두 상하
  대칭 패딩(`padding:10px 12px;`)을 쓰고, `vertical-align:middle;`도 명시한다** — 상하를
  비대칭으로 주면(예: 1행 `padding:12px 12px 4px`, 2행 `padding:0 12px 12px`), 셀에 여유
  공간이 없을 때 `vertical-align:middle`을 줘도 비대칭 패딩을 상쇄하지 못해 2행(ROAS/CTR 값)의
  텍스트가 셀 위쪽에 붙어 보일 수 있다. 대칭 패딩으로 바꾸면 두 행 사이 간격이 약간 늘어나지만,
  "정확한 상하 중앙 정렬"이 항상 더 우선한다.
- **각주는 표 바로 아래 고정 여백(`margin-top:12px`)에서 시작한다** — 카드 맨 아래에
  고정(`margin-top:auto`)하지 않는다. 두 표(ROAS/CTR)가 위 3행 구조로 동일하므로 표 높이가
  같아지고, 그 결과 두 카드의 **각주가 시작되는 높이**가 자연히 일치한다. 각주 길이가
  서로 달라(CTR 쪽이 더 길다) 카드 전체 높이는 달라질 수 있으며, 이는 허용한다 — 맞춰야
  하는 것은 "각주 시작 높이"이지 "카드 전체 높이"가 아니다.
- 이미지는 `<img src="{thumbnail_image_url}" onerror="...">` + 바로 뒤에 `style="display:none;"`
  로 숨겨둔 `<a href="{thumbnail_image_url}" target="_blank">소재 미리보기 →</a>`를 짝으로
  둔다. 이미지 로드에 성공하면 이미지가, 실패하면(클로드 렌더링 환경처럼 매체사가 접근을
  차단하는 경우) `onerror`가 이미지를 숨기고 바로 뒤 링크를 보이게 한다 — 이 전환은 순수
  HTML 속성만으로 이루어지며 별도 JS 로직이 필요 없다.
- **이미지 크기는 셀의 좌우 폭에 맞춰 크게 렌더링한다** — `width:56px; height:56px` 같은
  작은 고정 크기를 쓰지 않는다. `width:100%; max-width:220px; height:180px; object-fit:cover;`
  처럼 셀 안에서 최대한 크게 보이도록 하고, 표 행의 상하 크기도 이미지에 맞춰 자연스럽게
  늘어나게 둔다(이미지 셀에 별도 고정 높이를 주지 않아 내용에 맞춰 자동으로 커지도록 한다).
- 2위 후보가 없으면(유효한 소재가 1개뿐) 해당 칸을 `-`로 표시하고 이미지/링크도 렌더링하지
  않는다.
- 비율(ROAS/CTR)은 % 소수점 1자리로 표기한다.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 소재명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — `campaign_name`+`asset_group`+
  `ad_name` 세 필드 정확 일치만 쓴다.