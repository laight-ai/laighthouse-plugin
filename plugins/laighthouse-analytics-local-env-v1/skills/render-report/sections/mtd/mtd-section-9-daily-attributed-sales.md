# MTD Section 9: 일별 광고기여 매출 분석

**report_type:** `mtd` (항상 포함)

## 필요 데이터 (MCP)
- `daily_attributed_sales`: 날짜별 배열
  ```json
  [
    { "date": "2026-05-01", "ad_cost": 3957831, "clicks": 4376, "purchases": 564, "revenue": 22699384 },
    { "date": "2026-05-02", "ad_cost": 3460840, "clicks": 3515, "purchases": 740, "revenue": 34569257 }
  ]
  ```

## HTML

```html
<!-- MTD SECTION 9: 일별 광고기여 매출 분석 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">일별 광고기여 매출 분석</div>
  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th>날짜</th>
          <th style="text-align:right;">광고비</th>
          <th style="text-align:right;">클릭</th>
          <th style="text-align:right;">구매</th>
          <th style="text-align:right;">매출</th>
        </tr>
      </thead>
      <tbody>
        <!-- daily_attributed_sales 배열을 순회하며 아래 행 반복 (날짜순, 페이지네이션 없음) -->
        <tr>
          <td>{date}</td>
          <td style="text-align:right;">{ad_cost_fmt}</td>
          <td style="text-align:right;">{clicks_fmt}</td>
          <td style="text-align:right;">{purchases}</td>
          <td style="text-align:right;">{revenue_fmt}</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

## Script
없음 (정적 테이블, MTD 기간 내 최대 31행이라 페이지네이션 불필요)

## 렌더링 규칙
- 금액/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷
- `date`는 MCP에서 받은 `YYYY-MM-DD` 형식 그대로 표시
