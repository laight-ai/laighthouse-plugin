# MTD Section 14: 일별 광고기여 매출 분석

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_daily_attributed_sales`

```json
{ "brand_name": "...", "start_date": "월초", "end_date": "target_date(MTD 마지막 날)" }
```

> ⚠️ **`get_ad_performance_daily_table`을 여기 쓰지 않는다 (2026-07-11 확인된 문제 — `group_by`가
> 서버에 `null`로 도착하는 호출 오류가 있었다).** `get_naver_daily_attributed_sales`는
> `get_daily_ad_performance`를 `media=naver, group_by=total, campaign_type=None` 고정으로 감싼
> naver 전용 MCP 도구다 — 이 세 파라미터를 아예 노출하지 않으므로(내부에서 고정) 그 파라미터 전달
> 오류 자체가 발생할 수 없다. `laighthouse-prism/src/mcp_server/tools_naver.py`에 정의돼 있다.
> (report-backend `default/_mtd_components.py::build_daily_contribution`은 이 endpoint의 cost
> 필드 대신 SA+GFA 채널 데이터로 광고비를 다시 계산하는데, 이건 하루 최대 2원 수준의 VAT 반올림
> 오차를 없애기 위한 것 — 이 보고서 규모에서는 무의미해서 이 도구는 그 재계산을 하지 않고
> endpoint의 `cost` 필드를 그대로 쓴다.)
> `start_date`/`end_date`는 31일 이내여야 한다 (MTD 범위는 항상 이 조건을 만족한다).

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
<!-- MTD SECTION 14: 일별 광고기여 매출 분석 -->
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
