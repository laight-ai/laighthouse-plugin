# MTD Section 4: 매체별 예산 소진 현황

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_channel_progression`

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). report-backend의
  `_prism_components.py::build_source_progression`이 쓰는 것과 동일한 `/v2/naver/channel-progression`
  래퍼이며, report_generator/default/mtd가 실제로 의존하는 naver 데이터만 노출한다.
- 응답 `channels[]`의 `channel` 키(`nvad:BRS`/`nvad:PLINK`/`nvad:NVSHOP`/`nvgfa_ad:`/`nvgfa_dp:`)를
  아래 라벨로 매핑한다 (report-backend `CHANNEL_SPECS`와 동일):
  - `nvad:BRS` → 네이버 브랜드검색
  - `nvad:PLINK` → 네이버 파워링크
  - `nvad:NVSHOP` → 네이버 쇼핑검색
  - `nvgfa_ad:` → 네이버 GFA 애드부스트
  - `nvgfa_dp:` → 네이버 GFA 디스플레이
- 채널별 필드 매핑:
  - `budget_goal` ← `budget.series`에서 `date == 월말`인 항목의 `cost_cumsum` (월 전체 목표)
  - `daily_budget` ← `budget.series`에서 `date == as_of_date`인 항목의 `cost_cumsum` (오늘까지의 목표)
  - `spent` ← `actual[]`에서 `date <= as_of_date`인 항목들의 `cost` 합
  - `daily_spent` ← `spent / (as_of_date의 일수)` (일 평균 소진액)
  - `spent_rate` ← `spent / budget_goal * 100` (0으로 나누면 0)
- `total` 합계 행은 5개 채널의 위 필드를 그대로 합산해 재계산한다 (MCP가 total을 별도로 주지 않음).

## 필요 데이터 (MCP)
- `media_budget_progress.channel_group`: 채널 그룹 레이블 (예: 'SA / DA')
- `media_budget_progress.rows`: 매체별 배열
  ```json
  [
    { "media": "네이버 브랜드검색", "spent_rate": 55.9, "budget_goal": 19099909, "spent": 9237537, "daily_budget": 10669754, "daily_spent": 8421155 },
    { "media": "네이버 파워링크", "spent_rate": 50.4, "budget_goal": 4909091, "spent": 2375367, "daily_budget": 2473472, "daily_spent": 2435419 }
  ]
  ```
- `media_budget_progress.total`: 합계 행 (동일 필드 구조, `media` 없음)

## HTML

```html
<!-- MTD SECTION 4: 매체별 예산 소진 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매체별 예산 소진 현황</div>
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
          <th style="text-align:right;">일 소진액과</th>
        </tr>
      </thead>
      <tbody>
        <!-- media_budget_progress.rows 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{media}</td>
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
          <td style="text-align:right;">{daily_spent_fmt}</td>
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
          <td style="text-align:right;">{total.daily_spent_fmt}</td>
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
