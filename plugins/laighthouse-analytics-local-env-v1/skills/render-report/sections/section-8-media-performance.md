# Section 8: 매체별 성과 비교

**트리거 키워드:** `매체별 성과`

## 필요 데이터 (MCP)
- `media_performance`: 매체별 배열
  ```json
  [
    {
      "name": "네이버 브랜드검색",
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
