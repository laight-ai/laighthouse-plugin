---
name: render-report
description: >
  This skill should be used when the user asks to "보고서로 만들어줘", "레포트 형식으로 보여줘",
  "Daily 보고서", "MTD 보고서", "라이트하우스 보고서", "성과 분석 보고서", or wants MCP data
  formatted as a structured daily/MTD performance report matching the Laighthouse style.
metadata:
  version: "0.7.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 데이터를 받아 **라이트하우스 스타일 성과 보고서**로 렌더링하는 오케스트레이터. 지원하는
`report_type`은 `daily`와 `mtd` 두 가지뿐이다. 각각 완전히 독립된 폴더(`sections/daily/`,
`sections/mtd/`)에서 자기 완결적으로 섹션을 가져온다 — 폴더 간 import는 없다.

| report_type | 대상 브랜드군 | report-backend generator | 폴더 |
|---|---|---|---|
| `daily` | Meta/Google 브랜드 (Aqua Glow, Saturday Skin) | `saturdayskin` | `sections/daily/` |
| `mtd` | naver 기반 브랜드 (다형식품 등) | `default` | `sections/mtd/` |

`monthly`/`weekly`는 이 스킬의 범위 밖이다 (monthly는 현재 제작 계획이 없고, weekly는
`report-backend`의 `domain/report.py::ReportType`에 대응 값 자체가 없다 — `ABTEST`/`MTD`/`DAILY`/
`MONTHLY`/`CALENDAR`/`DASHBOARD`만 존재). 사용자가 monthly/weekly 보고서를 요청하면, 아직 지원하지
않는다고 알리고 daily/mtd 중 무엇을 원하는지 확인한다.

---

## 데이터 처리 원칙

> ⚠️ **MCP가 반환하는 수치 데이터는 이미 정제·가공이 끝난 데이터**다. 결측치 보정, 이상치 제거,
> 재집계, 재계산, 반올림/포맷 변경 등 **추가적인 정제·클리닝을 절대 하지 않는다.**
> MCP 응답 값을 그대로 받아 표시에만 사용한다 (단, 각 섹션 파일에 **명시적으로** 표기 변환이 지정된
> 경우—예: ROAS 소수 → % 변환, mtd-section-2의 actual_mtd 대체 소스—만 예외로 적용한다).
> 데이터가 비어있거나 갭이 있는 경우에도 임의로 채우거나 추정하지 말고 "데이터 부족 시" 규칙을 따른다.

## 입력 파라미터

사용자 프롬프트에서 아래 항목을 파싱한다:

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| report_type | `daily` 또는 `mtd` | mtd |
| 보고서 제목 | 보고서 상단 타이틀 | 다형식품 MTD 보고서 |
| brand_name | MCP 호출용 브랜드명 (`get_brand_list` 응답과 정확히 일치) | 다형식품 |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

daily/mtd 둘 다 **섹션 구성은 report_type이 전부 결정**하며 사용자가 섹션을 골라 지정하는 개념이
없다 — 아래 두 표에 있는 파일을 항상 전부 렌더링한다.

---

## 실행 순서

1. 파라미터를 파싱하고 report_type을 확정한다 (`daily` 또는 `mtd`만 유효).
2. target/achievement 수치를 호출한다 — **report_type에 따라 쓰는 도구가 다르다, 절대 섞지 않는다**:
   - `daily` (Meta/Google 브랜드) → `mcp__laighthouse__target_progress`(범용 v1 도구)에
     `{ "campaign_type": "sales" }` 1회. `saturdayskin/_components.py`가 `metric.actual_mtd`를 그대로
     신뢰하므로 응답을 그대로 사용한다.
   - `mtd` (naver 브랜드) → `mcp__laighthouse__get_naver_target_progress`(v2 전용 도구)에
     `{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }` 1회.
     ⚠️ **범용 `target_progress`를 mtd에 쓰면 안 된다** — v1은 `aw_compiled`/`fb_compiled`(Google/Meta)
     실적 테이블만 보므로 naver 전용 브랜드는 매출/ROAS 목표·실적이 전부 0으로 나온다 (2026-07-10
     확인, `laighthouse-prism`에 `get_naver_target_progress` 툴을 새로 등록해 해결함). 이 도구는
     target(`target_cost`/`target_revenue`/`target_roas`)과 actual(`actual_cost`/`actual_revenue`/
     `actual_roas`)을 한 번에 반환하므로 별도 합산이 필요 없다 — `sections/mtd/
     mtd-section-2-achievement.md` 참고.
   - ⚠️ ROAS 관련 수치(`target_roas`/`actual_roas`, v1의 `monthly_roas.target_full_month` 등)는
     비율값(예: 0.87, 5.06)으로 반환되므로 반드시 × 100 후 표시한다 (0.87 → 87%, 5.06 → 506%).
3. 나머지 `mcp__laighthouse__*` 도구를 호출해 각 섹션 수치 데이터를 가져온다 (각 섹션 파일에 명시된
   정확한 tool명 참고). 두 종류가 있다:
   - **generic 도구** (`get_ad_performance_daily_table` / `get_ad_performance_monthly_table` /
     `get_sales_performance_daily` / `get_sku_sales_daily` 등) — 여러 매체(google/meta/tiktok/naver)를
     `media` 파라미터로 다루며, naver는 채널(BRS/PLINK/NVSHOP/GFA) 구분 없이 하나로 통합된다.
   - **naver 전용 도구** (`get_naver_sa_performance_daily` / `get_naver_item_sales_daily` /
     `get_naver_channel_progression` / `get_naver_target_progress`, `laighthouse-prism/src/
     mcp_server/tools_naver.py`) — mtd 보고서에서만 쓴다. naver 채널 구분, 카테고리별 매출/할인율/
     환불율, 채널별 예산 목표, naver 전용 target/achievement(2단계에서 이미 호출)처럼 generic
     도구로는 낼 수 없는 데이터를 제공한다.
4. Executive Summary는 daily/mtd 둘 다 항상 포함된다. 수집한 수치 데이터를
   `mcp__df_dify__<workflow-tool-name>` 도구(`.mcp.json` 서버 키는 `df_dify`; 실제 tool명은 브랜드에
   연결된 Dify 워크플로에 맞게 확인)에 전달하여 분석 텍스트를 가져온다.
   - dify 응답은 `executive_summary` key로 반환됨
   - dify 응답 실패 시 수치 기반으로 AI가 직접 생성 (단, 근거 수치 자체가 데이터 갭이면 생성하지 않음)
   - **`mtd`인 경우**, 동일한 `mcp__df_dify__*` 호출(또는 동일 페이로드의 추가 호출)에서
     `performance_overview`, `analysis_of_ad_performance`, `analysis_by_ad_group` 3개 key도 함께 가져온다.
     각각 mtd-section-5/8/11에서 사용하며, 실패 시 해당 섹션 수치 기반으로 AI가 직접 생성한다.
5. `report_type`에 대응하는 아래 표의 파일을 **순서대로 전부** import해 HTML을 조합한다.
6. 이 스킬 폴더의 `assets/chart.umd.min.js` 파일을 읽어 그 내용 전체를 `{CHART_JS_INLINE}` 자리에
   그대로 삽입한다 (CDN `<script src>` 절대 사용 금지 — 아래 보고서 골격의 경고 참고).
7. 아래 **보고서 골격**에 섹션들을 삽입해 렌더링한다 — Claude Code(Artifact)에서 실행 중이면 Artifact
   도구로 게시하고, `mcp__visualize__show_widget`이 있는 호스트에서는 그걸 쓴다.

---

## 섹션 Import 목록

### report_type: `daily` (Aqua Glow / Saturday Skin 전용, 항상 포함)

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 월 목표 카드 | `@import sections/daily/daily-section-1-kpi-goals.md` |
| 2 | Overview: Sales Campaign Performance | `@import sections/daily/daily-section-2-overview.md` |
| 3 | Executive Summary | `@import sections/daily/daily-section-3-executive-summary.md` |
| 4 | Sales campaign: Daily performance in the last 7 days | `@import sections/daily/daily-section-4-sales-daily-chart.md` |
| 5 | Daily Revenue in DTC | `@import sections/daily/daily-section-5-dtc-revenue.md` |
| 6 | Performance by Campaign | `@import sections/daily/daily-section-6-campaign-table.md` |
| 7 | Performance by Asset group | `@import sections/daily/daily-section-7-asset-group-table.md` |

`sections/daily/` 폴더의 파일은 전부 Meta/Google 브랜드(`target_progress(campaign_type="sales")`)
기준으로 작성되어 있고, 다른 폴더를 import하지 않는다.

### report_type: `mtd` (naver 기반 default 브랜드 전용 — 다형식품 등, 항상 포함)

**총 14개 섹션.** report-backend `default/_report_mtd.py::organize_report_artifacts`의
`ordered_names`(12개 데이터 컴포넌트) + "목표 달성 현황" 컴포넌트가 프론트엔드에서 2개 시각 블록
(월 목표 카드 + 목표 달성 현황 카드)으로 렌더링되는 것 = 14개 카드. 2026-05-15 다형식품 실제 MTD
PDF와 대조해 순서/구성을 확정했다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 월 목표 카드 | `@import sections/mtd/mtd-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 | `@import sections/mtd/mtd-section-2-achievement.md` |
| 3 | Executive Summary | `@import sections/mtd/mtd-section-3-executive-summary.md` |
| 4 | 월별 광고 성과 | `@import sections/mtd/mtd-section-4-monthly-chart.md` |
| 5 | 성과에 대한 개괄 | `@import sections/mtd/mtd-section-5-performance-overview.md` |
| 6 | 상품별 누적 판매액 | `@import sections/mtd/mtd-section-6-product-cumulative-sales.md` |
| 7 | 일일 카테고리별 매출 현황 | `@import sections/mtd/mtd-section-7-daily-category-chart.md` |
| 8 | 제품 판매 성과의 심층 분석 | `@import sections/mtd/mtd-section-8-product-deep-dive.md` |
| 9 | 매체별 예산 소진 현황 | `@import sections/mtd/mtd-section-9-media-budget-progress.md` |
| 10 | 캠페인별 성과 | `@import sections/mtd/mtd-section-10-campaign-performance.md` |
| 11 | 광고 그룹별 심층 분석 | `@import sections/mtd/mtd-section-11-ad-group-deep-dive.md` |
| 12 | 그룹별 성과 | `@import sections/mtd/mtd-section-12-group-performance.md` |
| 13 | 키워드별 성과 | `@import sections/mtd/mtd-section-13-keyword-performance.md` |
| 14 | 일별 광고기여 매출 분석 | `@import sections/mtd/mtd-section-14-daily-attributed-sales.md` |

순서 1(월 목표 카드)과 2(목표 달성 현황)는 **항상 붙어서** 렌더링한다 — 둘 다 같은 `target_progress`
응답을 재사용하며, 별도 재호출 없음 (`sections/mtd/mtd-section-1-kpi-goals.md` 참고).

`sections/mtd/` 폴더의 파일은 전부 naver 기반 default generator 브랜드 기준으로 작성되어 있고,
다른 폴더를 import하지 않는다.

---

## 보고서 골격 (Scaffold)

각 섹션 HTML을 `{SECTIONS}` 자리에 순서대로 삽입한다.

> ⚠️ **Chart.js는 CDN `<script src>`로 절대 불러오지 않는다.** Artifact(claude.ai 아티팩트)의 CSP는
> 외부 호스트로 나가는 스크립트 요청을 전부 차단하므로, `<script src="https://cdn.jsdelivr.net/...">`
> 로 로드하면 스크립트 자체가 실행되지 않아 모든 차트가 빈 캔버스로 남는다 (실제로 발생했던 버그).
> 대신 이 스킬 폴더의 `assets/chart.umd.min.js`(Chart.js v4 UMD 빌드, MIT license, 오프라인 자산)를
> 읽어서 **그 파일 내용 전체를 `<script>...</script>` 태그 안에 그대로 붙여넣는다** (src 속성 없이,
> 인라인 텍스트로). `{CHART_JS_INLINE}` 자리표시자가 그 자리다 — 절대 CDN URL로 되돌리지 않는다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<script>
{CHART_JS_INLINE}
</script>
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

  <!-- 섹션 HTML 삽입 위치 -->
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
- 섹션을 임의로 생략하지 않는다 — daily는 7개, mtd는 14개 전부 항상 렌더링한다.
