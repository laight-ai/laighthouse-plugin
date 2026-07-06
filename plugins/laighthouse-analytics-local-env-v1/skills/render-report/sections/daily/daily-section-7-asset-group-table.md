# Daily Section 7: Performance by Asset group

**report_type:** `daily`
**MCP 도구:** `get_sales_by_asset_group_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

## 필요 데이터
- `sales_by_asset_group`: 에셋그룹 배열
  ```json
  [
    {
      "media": "Google Ads",
      "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "asset_group": "CITRUS Kiwi overlay pack assets",
      "impression": 509,
      "click": 15,
      "ctr": 2.95,
      "cost": 10,
      "revenue": 0
    }
  ]
  ```
  ※ ROAS 컬럼 없음 (이미지 참조)

## HTML

```html
<!-- DAILY SECTION 7: Performance by Asset group -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div style="font-size:15px; font-weight:700; color:#1e293b;">Performance by Asset group</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input id="assetSearch" type="text" placeholder="검색" oninput="filterTable('assetTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select id="assetPageSize" onchange="changePageSize('assetTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option>
        <option value="20">20개</option>
        <option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="assetTable" style="width:100%; border-collapse:collapse; font-size:13px;">
      <thead>
        <tr style="border-bottom:1px solid #e2e8f0;">
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Media</th>
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Campaign</th>
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Asset Group</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Impression</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Click</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">CTR (%)</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Cost ($)</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Revenue ($)</th>
        </tr>
      </thead>
      <tbody id="assetTableBody">
        <!-- {sales_by_asset_group} 배열을 순회하며 아래 행 반복 -->
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:10px 12px; color:#3b82f6; font-weight:500;">{media}</td>
          <td style="padding:10px 12px; color:#3b82f6; max-width:240px;">{campaign}</td>
          <td style="padding:10px 12px; color:#3b82f6;">{asset_group}</td>
          <td style="padding:10px 12px; text-align:right;">{impression}</td>
          <td style="padding:10px 12px; text-align:right;">{click}</td>
          <td style="padding:10px 12px; text-align:right;">{ctr}</td>
          <td style="padding:10px 12px; text-align:right;">{cost}</td>
          <td style="padding:10px 12px; text-align:right;">{revenue}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- 페이지네이션 -->
  <div id="assetPagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;">
  </div>
</div>
```

## Script

```javascript
// Asset group 테이블 초기화 (공통 유틸은 section-5에서 정의됨)
window.initTable('assetTable');
```
