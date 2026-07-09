# Section 8: 매체별 성과 비교

**트리거 키워드:** `매체별 성과`

## MCP 도구 호출: `get_ad_performance_monthly_table`

```json
{ "brand_name": "...", "start_month": "전월", "end_month": "당월", "group_by": "media", "media": null }
```
- `group_by="media"`, `media` 미지정 → media(google/meta/tiktok/naver)별 월 1행 × 2개월 = 매체 수 × 2행
- naver 브랜드는 `media="naver"` 한 행으로만 나온다 — 예시의 "네이버 브랜드검색"/"네이버 파워링크"처럼
  naver 내부 채널(BRS/PLINK/NVSHOP) 단위로는 쪼개지지 않는다 (그 세분화는 naver 전용 endpoint에서만
  가능하며, **naver 전용 MCP 도구를 새로 만들지 않기로 했으므로 이 레벨의 분리는 지원하지 않는다**).
- naver 내부에서 branding(BRS)/sales(PLINK+NVSHOP)만이라도 나누고 싶다면, 같은 도구를
  `campaign_type="branding"`과 `campaign_type="sales"`로 각각 2회 더 호출해 보조적으로 사용할 수 있다
  (이 경우도 media enum 자체를 늘리지 않는, 기존 generic 파라미터만 사용).
- 반환은 마크다운 표 문자열 — 파싱해 아래 배열로 재구성 (media별 그룹핑, 전월/당월 페어링)

## 필요 데이터 (MCP)
- `media_performance`: 매체별 배열 (매체 = media enum 값: google/meta/tiktok/naver)
  ```json
  [
    {
      "name": "naver",
      "prev_label": "2026년 3월",
      "curr_label": "2026년 4월",
      "prev": { "ad_cost": 18735215, "revenue": 121032463, "roas": 646.02 },
      "curr": { "ad_cost": 18252208, "revenue": 134092127, "roas": 734.66 }
    },
    ...
  ]
  ```

## HTML

```html
<!-- SECTION 8: 매체별 성과 비교 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매체별 성과 비교</div>

  <!-- media_performance 배열을 순회하며 매체별 블록 반복 -->
  <!-- 예시: 매체 1개 블록 -->
  <div style="margin-bottom:24px;">
    <div style="font-size:14px; font-weight:700; color:#1e293b; margin-bottom:8px;">{media.name}</div>
    <table>
      <thead>
        <tr>
          <th style="width:120px;">월</th>
          <th style="text-align:right;">광고비 (USD)</th>
          <th style="text-align:right;">매출 (USD)</th>
          <th style="text-align:right;">ROAS</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{media.prev_label}</td>
          <td style="text-align:right;">{media.prev.ad_cost_fmt}</td>
          <td style="text-align:right;">{media.prev.revenue_fmt}</td>
          <td style="text-align:right;">{media.prev.roas}%</td>
        </tr>
        <tr style="background:#f8fafc; font-weight:600;">
          <td>{media.curr_label}</td>
          <td style="text-align:right;">{media.curr.ad_cost_fmt}</td>
          <td style="text-align:right;">{media.curr.revenue_fmt}</td>
          <td style="text-align:right;">{media.curr.roas}%</td>
        </tr>
      </tbody>
    </table>
  </div>
  <!-- 매체 블록 반복 끝 -->

</div>
```

## Script
없음 (정적 테이블)

## 렌더링 규칙
- 광고비/매출 수치는 `toLocaleString()`으로 천 단위 콤마 포맷
- 당월 행은 `background:#f8fafc; font-weight:600` 강조
- 매체 개수는 MCP 데이터에 따라 가변
