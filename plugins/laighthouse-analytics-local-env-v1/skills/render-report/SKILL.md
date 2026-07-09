---
name: render-report
description: >
  This skill should be used when the user asks to "보고서로 만들어줘", "레포트 형식으로 보여줘",
  "Daily 보고서", "Monthly 보고서", "월간 보고서", "라이트하우스 보고서", "주간 성과 보고서",
  "WoW 보고서", "render as report", "성과 분석 보고서", or wants MCP data formatted as a
  structured monthly/weekly performance report matching the Laighthouse style.
metadata:
  version: "0.6.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 데이터를 받아 **라이트하우스 스타일 월간/주간 성과 보고서**로 렌더링하는 오케스트레이터.
각 섹션의 HTML/JS 구현은 `sections/` 디렉터리의 개별 스킬 파일에서 import한다.

---

## 입력 파라미터

사용자 프롬프트에서 아래 항목을 파싱한다:

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| 보고서 제목 | 보고서 상단 타이틀 | 아쿠아글로우 월간보고서 |
| brand_id | MCP 호출용 브랜드 ID | ab51210d-... |
| account_id | MCP 호출용 계정 ID | mock-account-001 |
| 기준 일자 / 기간 | 보고서 기준 날짜 또는 월 | 2026-04 |
| 포함 섹션 | 렌더링할 섹션 목록 | 월 목표, 목표 달성, ... |
| 토큰 | MCP 인증 토큰 | 202ccf9c-... |

---

## 실행 순서

1. 파라미터를 파싱한다.
2. `mcp__lighthouse__target_progress` 도구(laighthouse-prism이 노출하는 실제 tool명 `target_progress`;
   `.mcp.json` 서버 키는 `lighthouse`)를 호출한다. 이 도구는 `report_type`/`data_type` 인자를 받지 않고
   `campaign_type`(`"sales"` | `"branding"` | 미지정=전체)만 지원하므로, sales/branding을 각각 보고 싶으면
   campaign_type을 바꿔 두 번 호출한다:
   - ⚠️ **`monthly_roas` 항목(`items[metric=monthly_roas]`)의 수치는 소수(예: 2.2, 0.87)로 반환되므로
     반드시 × 100 후 표시**한다 (2.2 → 220%, 0.87 → 87%)
   - `daily` → `{ "campaign_type": "sales" }` 1회
   - `weekly` / `mtd` / `monthly` → `{ "campaign_type": "sales" }` + `{ "campaign_type": "branding" }` 2회
   - 세부 계산·데이터 갭(브랜딩 impression/CPM 목표 없음)은 `sections/section-2-achievement.md` 참고
3. 나머지 `mcp__lighthouse__*` 도구를 호출해 각 섹션 수치 데이터를 가져온다 (각 섹션 파일에 명시된
   정확한 tool명 참고). 두 종류가 있다:
   - **generic 도구** (`get_ad_performance_daily_table` / `get_ad_performance_monthly_table` /
     `get_ad_performance_weekly_table` / `get_sku_sales_daily` / `get_sku_sales_monthly` 등) — 여러
     매체(google/meta/tiktok/naver)를 `media` 파라미터로 다루며, naver는 채널(BRS/PLINK/NVSHOP/GFA)
     구분 없이 하나로 통합된다.
   - **naver 전용 도구** (`get_naver_sa_performance_daily` / `get_naver_item_sales_daily` /
     `get_naver_channel_progression`, `laighthouse-prism/src/mcp_server/tools_naver.py`) — naver
     채널 구분(캠페인별 성과의 "네이버 광고 채널명"), 카테고리별 매출/할인율/환불율, 채널별 예산
     목표처럼 generic 도구로는 낼 수 없는 데이터를 제공한다. report-backend의
     `report_generator/default/mtd`가 실제로 의존하는 3개 endpoint만 wrapping했으므로, 이 3개
     외의 naver 전용 필요가 생기면 먼저 그 생성기가 실제로 그 데이터를 쓰는지 확인한다.
4. **포함 섹션에 `Executive Summary`가 포함된 경우** (daily는 항상 포함), 수집한 수치 데이터를
   `mcp__df_dify__<workflow-tool-name>` 도구(`.mcp.json` 서버 키는 `df_dify`; 실제 tool명은 브랜드에
   연결된 Dify 워크플로에 맞게 확인)에 전달하여 분석 텍스트를 가져온다.
   - dify 응답은 `executive_summary` key로 반환됨
   - dify 응답 실패 시 수치 기반으로 AI가 직접 생성 (단, 근거 수치 자체가 데이터 갭이면 생성하지 않음)
   - **`report_type`이 `mtd`인 경우**, 동일한 `mcp__df_dify__*` 호출(또는 동일 페이로드의 추가 호출)에서
     `performance_overview`, `analysis_of_ad_performance`, `analysis_by_ad_group` 3개 key도 함께 가져온다.
     각각 mtd-section-1/3/6에서 사용하며, 실패 시 해당 섹션 수치 기반으로 AI가 직접 생성한다.
5. **포함 섹션** 목록을 확인하고 해당하는 섹션 스킬만 import하여 HTML을 조합한다.
6. 아래 **보고서 골격**에 섹션들을 삽입해 `mcp__visualize__show_widget`으로 렌더링한다.

---

## 섹션 Import 목록

`report_type`에 따라 사용하는 섹션 파일이 다르다.

### report_type: `daily`

| 섹션 | Import 경로 | 항상 포함 |
|------|------------|---------|
| 월 목표 카드 | `@import sections/daily/daily-section-1-kpi-goals.md` | ✅ |
| Overview: Sales Campaign Performance | `@import sections/daily/daily-section-2-overview.md` | ✅ |
| Executive Summary | `@import sections/daily/daily-section-3-executive-summary.md` | ✅ |
| Sales campaign: Daily performance in the last 7 days | `@import sections/daily/daily-section-4-sales-daily-chart.md` | ✅ |
| Daily Revenue in DTC | `@import sections/daily/daily-section-5-dtc-revenue.md` | ✅ |
| Performance by Campaign | `@import sections/daily/daily-section-6-campaign-table.md` | ✅ |
| Performance by Asset group | `@import sections/daily/daily-section-7-asset-group-table.md` | ✅ |

> 파일 번호는 daily 보고서 내 실제 렌더링 순서(1~7)와 1:1로 맞춰져 있다.
> `daily-section-3-executive-summary.md`는 로직을 이중 관리하지 않기 위해 내부적으로
> 공용 `sections/section-4-executive-summary.md`(dify 호출 포함)를 `@import`하는 얇은 래퍼다.

Daily report는 포함 섹션 조건 없이 전체 섹션을 항상 렌더링한다 (렌더링 순서: 월 목표 카드 → Overview
→ Executive Summary → 최근 7일 일별 차트 → Daily Revenue in DTC → Performance by Campaign →
Performance by Asset group).

Executive Summary는 weekly/mtd/monthly와 동일하게 `sections/section-4-executive-summary.md`를
공용으로 사용하며, `mcp__df_dify__<workflow-tool-name>` 호출 로직도 동일하게 적용한다 (dify 응답
실패 시 daily 수치 기반으로 AI가 직접 생성하는 방식으로 폴백).

### report_type: `weekly` / `mtd` / `monthly`

포함 섹션 키워드에 해당할 때만 해당 파일을 import한다.

| 키워드 | Import 경로 |
|--------|------------|
| `월 목표` | `@import sections/section-1-kpi-goals.md` |
| `목표 달성` | `@import sections/section-2-achievement.md` |
| `월별 광고 성과` | `@import sections/section-3-monthly-chart.md` |
| `Executive Summary` | `@import sections/section-4-executive-summary.md` |
| `카테고리별 매출액` | `@import sections/section-5-category-sales.md` |
| `일일 카테고리별` | `@import sections/section-6-daily-chart.md` |
| `제품 판매 트렌드` | `@import sections/section-7-trend-analysis.md` |
| `매체별 성과` | `@import sections/section-8-media-performance.md` |

> `제품 판매 트렌드`는 mtd-section-3(제품 판매 성과의 심층 분석)이 더 상세한 대체 콘텐츠를 항상
> 제공하므로, mtd 보고서에서는 함께 지정하지 않는 것을 권장한다 (강제 제외는 아님).

#### report_type: `mtd` 전용 추가 섹션 (키워드 조건 없이 항상 포함)

`report_type`이 `mtd`일 때는 위 공용 섹션 외에 아래 9개 섹션을 **daily처럼 항상** 렌더링한다.
파일 번호는 mtd 보고서 내 실제 렌더링 순서와 1:1로 맞춰져 있다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 4-b | 성과에 대한 개괄 | `@import sections/mtd/mtd-section-1-performance-overview.md` |
| 5-b | 상품별 누적 판매액 | `@import sections/mtd/mtd-section-2-product-cumulative-sales.md` |
| 7-b | 제품 판매 성과의 심층 분석 | `@import sections/mtd/mtd-section-3-product-deep-dive.md` |
| 8 | 매체별 예산 소진 현황 | `@import sections/mtd/mtd-section-4-media-budget-progress.md` |
| 9 | 캠페인별 성과 | `@import sections/mtd/mtd-section-5-campaign-performance.md` |
| 10 | 광고 그룹별 심층 분석 | `@import sections/mtd/mtd-section-6-ad-group-deep-dive.md` |
| 11 | 그룹별 성과 | `@import sections/mtd/mtd-section-7-group-performance.md` |
| 12 | 키워드별 성과 | `@import sections/mtd/mtd-section-8-keyword-performance.md` |
| 13 | 일별 광고기여 매출 분석 | `@import sections/mtd/mtd-section-9-daily-attributed-sales.md` |

mtd 보고서의 전체 렌더링 순서(공용 섹션 + mtd 전용 섹션 인터리빙):

1. 월 목표 카드 (`월 목표` 키워드 시 section-1)
2. 목표 달성 현황 (`목표 달성` 키워드 시 section-2, sales + branding 보조)
3. Executive Summary (`Executive Summary` 키워드 시 section-4)
4. **성과에 대한 개괄** (mtd-section-1)
5. 월별 광고 성과 차트 (`월별 광고 성과` 키워드 시 section-3)
6. **상품별 누적 판매액** (mtd-section-2)
7. 일일 카테고리별 매출 현황 차트 (`일일 카테고리별` 키워드 시 section-6)
8. **제품 판매 성과의 심층 분석** (mtd-section-3)
9. **매체별 예산 소진 현황** (mtd-section-4)
10. **캠페인별 성과** (mtd-section-5)
11. **광고 그룹별 심층 분석** (mtd-section-6)
12. **그룹별 성과** (mtd-section-7)
13. **키워드별 성과** (mtd-section-8)
14. **일별 광고기여 매출 분석** (mtd-section-9)

---

## 보고서 골격 (Scaffold)

각 섹션 HTML을 `{SECTIONS}` 자리에 순서대로 삽입한다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
         background: #f8fafc; color: #1e293b; padding: 24px; }
  .report-wrap { max-width: 960px; margin: 0 auto; }
  .card { background: white; border: 1px solid #e2e8f0; border-radius: 12px;
          padding: 20px; margin-bottom: 16px; }
  .section-title { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #f1f5f9; color: #475569; font-weight: 600; padding: 8px 12px;
       text-align: left; border-bottom: 1px solid #e2e8f0; }
  td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; color: #374151; }
  @media print {
    body { background: white; padding: 0; }
    button { display: none !important; }
    .card { box-shadow: none; border: 1px solid #e2e8f0; break-inside: avoid; }
    canvas { max-width: 100%; }
    @page { margin: 15mm; size: A4; }
  }
</style>
</head>
<body>
<div class="report-wrap" id="report-content">

  <!-- 헤더: 항상 포함 -->
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
    <div>
      <h1 style="font-size:20px; font-weight:700;">{보고서_제목}</h1>
      <span style="font-size:13px; color:#64748b; margin-top:4px; display:block;">📅 {기간}</span>
    </div>
    <div style="display:flex; gap:8px;">
      <!-- 구글 드라이브 저장 (비활성) -->
      <button disabled
        style="padding:8px 14px; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:8px; font-size:13px; color:#94a3b8; cursor:not-allowed; display:flex; align-items:center; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="#94a3b8"><path d="M6.5 20q-2.275 0-3.888-1.575Q1 16.85 1 14.575q0-1.95 1.175-3.475Q3.35 9.575 5.25 9.15q.625-2.3 2.5-3.725T12 4q2.925 0 4.963 2.037Q19 8.075 19 11q1.725.2 2.863 1.487Q23 13.775 23 15.5q0 1.875-1.312 3.188Q20.375 20 18.5 20Z"/></svg>
        Google Drive
      </button>
      <!-- 메일 보내기 (HTML 클립보드 복사 → 붙여넣기) -->
      <button onclick="sendMail()"
        style="padding:8px 14px; background:white; border:1px solid #e2e8f0; border-radius:8px; font-size:13px; color:#374151; cursor:pointer; display:flex; align-items:center; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#374151" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
        메일 보내기
      </button>
      <!-- PDF 저장 -->
      <button onclick="downloadReport()"
        style="padding:8px 14px; background:#3b82f6; border:none; border-radius:8px; font-size:13px; color:white; cursor:pointer; display:flex; align-items:center; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
        PDF 저장
      </button>
    </div>
  </div>

  <!-- 포함 섹션 HTML 삽입 위치 -->
  {SECTIONS}

  <!-- 푸터: 항상 포함 -->
  <div style="text-align:center; font-size:12px; color:#94a3b8; padding:16px 0;">
    Engineered by Laighthouse AI
  </div>

</div>

<script>
/* ── 공통 유틸 ── */
function changeColor(v){ return v>0?'#16a34a':v<0?'#dc2626':'#6b7280'; }
function changeLabel(v,s='%'){ return v>0?`▲ +${v.toFixed(1)}${s}`:v<0?`▼ ${v.toFixed(1)}${s}`:'-'; }
function fmtUSD(v){ return '$'+Number(v).toLocaleString(); }

/* ── 버튼 핸들러 ── */
/* ── 메일 보내기 (보고서 HTML → 클립보드 복사 → 메일 본문 붙여넣기) ── */
function sendMail(){
  const reportEl = document.getElementById('report-content');
  if(!reportEl) return;

  // 버튼 임시 숨김 후 HTML 추출
  const btns = reportEl.querySelectorAll('button');
  btns.forEach(b => b.style.display = 'none');
  const html = reportEl.innerHTML;
  btns.forEach(b => b.style.display = '');

  // ClipboardItem으로 HTML 서식 복사 (Gmail/Outlook에서 붙여넣기 시 서식 유지)
  if(navigator.clipboard && window.ClipboardItem){
    const blob = new Blob([html], { type: 'text/html' });
    navigator.clipboard.write([new ClipboardItem({ 'text/html': blob })])
      .then(() => alert('보고서가 클립보드에 복사되었습니다.\nGmail / Outlook 메일 본문에 Ctrl+V로 붙여넣기 하세요.'))
      .catch(() => _fallbackCopy(html));
  } else {
    _fallbackCopy(html);
  }
}

function _fallbackCopy(html){
  const el = document.createElement('div');
  el.innerHTML = html;
  el.style.cssText = 'position:fixed;left:-9999px;top:0;';
  document.body.appendChild(el);
  const range = document.createRange();
  range.selectNodeContents(el);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  try {
    document.execCommand('copy');
    alert('보고서가 클립보드에 복사되었습니다.\nGmail / Outlook 메일 본문에 Ctrl+V로 붙여넣기 하세요.');
  } catch(e) {
    alert('복사 실패: 브라우저 권한을 확인해주세요.');
  }
  sel.removeAllRanges();
  document.body.removeChild(el);
}

/* ── PDF 저장 (차트 렌더링 완료 후 인쇄) ── */
function downloadReport(){
  // Chart.js 캔버스를 정적 이미지로 교체 후 인쇄 → 원복
  const canvases = document.querySelectorAll('canvas');
  const replacements = [];

  canvases.forEach(canvas => {
    const img = document.createElement('img');
    img.src = canvas.toDataURL('image/png');
    img.style.width = canvas.style.width || canvas.offsetWidth + 'px';
    img.style.height = canvas.style.height || canvas.offsetHeight + 'px';
    img.style.maxWidth = '100%';
    canvas.parentNode.insertBefore(img, canvas);
    canvas.style.display = 'none';
    replacements.push({ canvas, img });
  });

  setTimeout(() => {
    window.print();
    // 인쇄 대화상자 닫힌 후 원복
    setTimeout(() => {
      replacements.forEach(({ canvas, img }) => {
        canvas.style.display = '';
        img.remove();
      });
    }, 1000);
  }, 300);
}

/* ── 각 섹션 차트 초기화 스크립트 삽입 위치 ── */
{SECTION_SCRIPTS}
</script>
</body></html>
```

---

## 데이터 부족 시

- 해당 섹션은 `<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>` 로 대체
- 포함 섹션에 없는 섹션은 HTML에서 완전 생략
