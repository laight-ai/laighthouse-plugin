# MTD Section 9: 매체 별 예산 소진 현황

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_channel_budget_progress`

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). 채널 라벨 매핑
  (`nvad:BRS`→네이버 브랜드검색 등), `budget_goal`/`daily_budget`/`spent`/`daily_spent_avg`/
  `spent_rate` 계산, `total` 합계 행까지 **서버에서 이미 끝낸 상태**로 반환한다.
- 응답 `items[]`가 곧 `media_budget_progress.rows`, `total`이 곧 `media_budget_progress.total`이다
  (필드명은 `media`↔`channel`만 다르므로 그대로 매핑해 렌더링).

## 필요 데이터 (MCP)
- `media_budget_progress.channel_group`: 채널 그룹 레이블 (예: 'SA / DA')
- `media_budget_progress.rows`: 매체별 배열
  ```json
  [
    { "channel": "네이버 브랜드검색", "spent_rate": 55.9, "budget_goal": 19099909, "spent": 9237537, "daily_budget": 10669754, "daily_spent_avg": 8421155 },
    { "channel": "네이버 파워링크", "spent_rate": 50.4, "budget_goal": 4909091, "spent": 2375367, "daily_budget": 2473472, "daily_spent_avg": 2435419 }
  ]
  ```
- `media_budget_progress.total`: 합계 행 (동일 필드 구조, `media` 없음)

## HTML

```html
<!-- MTD SECTION 9: 매체 별 예산 소진 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매체 별 예산 소진 현황</div>
  <div style="font-size:12px; color:#64748b; font-weight:600; margin-bottom:10px;">{media_budget_progress.channel_group}</div>

  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th>매체</th>
          <th style="min-width:160px;">예산 소진율</th>
          <th style="text-align:right;">목표 소진</th>
          <th style="text-align:right;">예산 소진</th>
          <th style="text-align:right;">일 소진예산</th>
          <th style="text-align:right;">일 평균 소진액</th>
        </tr>
      </thead>
      <tbody>
        <!-- media_budget_progress.rows 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{channel}</td>
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="flex:1; height:8px; background:#e2e8f0; border-radius:4px; overflow:hidden;">
                <div style="height:100%; width:{spent_rate}%; background:#3b82f6;"></div>
              </div>
              <span style="font-size:12px; font-weight:600; color:#1e293b; width:44px; text-align:right;">{spent_rate}%</span>
            </div>
          </td>
          <td style="text-align:right;">{budget_goal_fmt}</td>
          <td style="text-align:right;">{spent_fmt}</td>
          <td style="text-align:right;">{daily_budget_fmt}</td>
          <td style="text-align:right;">{daily_spent_avg_fmt}</td>
        </tr>
        <!-- 반복 끝 -->

        <!-- 합계 행 -->
        <tr style="background:#f8fafc; font-weight:700;">
          <td>합계</td>
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="flex:1; height:8px; background:#e2e8f0; border-radius:4px; overflow:hidden;">
                <div style="height:100%; width:{total.spent_rate}%; background:#1e293b;"></div>
              </div>
              <span style="font-size:12px; width:44px; text-align:right;">{total.spent_rate}%</span>
            </div>
          </td>
          <td style="text-align:right;">{total.budget_goal_fmt}</td>
          <td style="text-align:right;">{total.spent_fmt}</td>
          <td style="text-align:right;">{total.daily_budget_fmt}</td>
          <td style="text-align:right;">{total.daily_spent_avg_fmt}</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

## Script
없음 (정적 테이블, 진행바는 CSS width만으로 렌더링)

## 렌더링 규칙
- 금액 필드는 `toLocaleString()`으로 천 단위 콤마 포맷 (원 단위)
- `spent_rate`가 90% 이상이면 진행바 색상을 `#dc2626`(빨강)으로 강조, 70~90%는 `#f59e0b`(주황),
  70% 미만은 `#3b82f6`(파랑) 유지
- 매체 개수는 MCP 데이터에 따라 가변
