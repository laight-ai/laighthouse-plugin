---
name: render-chart
description: >
  This skill should be used when the user asks to "차트로 보여줘", "그래프로 그려줘",
  "시각화해줘", "render as chart", "show as graph", "bar chart", "line chart",
  "pie chart", or wants MCP data displayed as a visual chart or graph.
  Use whenever laighthouse MCP tool results need to be presented as a data visualization.
metadata:
  version: "0.1.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 도구 호출 결과를 **인터랙티브 차트**로 렌더링한다. Chart.js를 사용하여 데이터를 시각화한다.

## 실행 순서

1. 사용자가 요청한 MCP 도구(`mcp__laighthouse__*`)를 호출하여 데이터를 가져온다.
2. 데이터 구조와 사용자 의도를 파악하여 가장 적합한 차트 유형을 선택한다.
3. `mcp__visualize__show_widget`으로 Chart.js 기반 HTML 차트를 렌더링한다.

## 차트 유형 선택 기준

| 상황 | 권장 차트 |
|------|-----------|
| 채널/카테고리 간 비교 | 막대 차트 (Bar) |
| 시계열 추이 | 선 차트 (Line) |
| 비율/구성 | 도넛 차트 (Doughnut) |
| 이번 주 vs 지난 주 | 그룹형 막대 차트 |
| 다중 지표 동시 비교 | 레이더 차트 (Radar) |

## Chart.js 템플릿

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
</head>
<body>
<div style="font-family: -apple-system, sans-serif; padding: 16px; max-width: 800px;">
  <h2 style="font-size: 18px; margin-bottom: 4px;">{제목}</h2>
  <p style="color: #666; font-size: 13px; margin-bottom: 16px;">{설명}</p>

  <!-- 차트 유형 토글 버튼 (선택 사항) -->
  <div style="display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;">
    <button onclick="switchChart('bar')" style="padding: 6px 14px; border-radius: 6px; border: 1px solid #e2e8f0; cursor: pointer; background: #3b82f6; color: white;">막대</button>
    <button onclick="switchChart('line')" style="padding: 6px 14px; border-radius: 6px; border: 1px solid #e2e8f0; cursor: pointer;">선</button>
  </div>

  <div style="position: relative; height: 360px;">
    <canvas id="mainChart"></canvas>
  </div>
</div>

<script>
const data = { /* MCP 데이터 삽입 */ };

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

let chart = new Chart(document.getElementById('mainChart'), {
  type: 'bar',
  data: {
    labels: data.labels,
    datasets: data.datasets.map((d, i) => ({
      label: d.label,
      data: d.values,
      backgroundColor: colors[i % colors.length] + 'cc',
      borderColor: colors[i % colors.length],
      borderWidth: 1,
      borderRadius: 4,
    }))
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString()}`
        }
      }
    },
    scales: {
      y: { beginAtZero: false, grid: { color: '#f1f5f9' } },
      x: { grid: { display: false } }
    }
  }
});

function switchChart(type) {
  chart.config.type = type;
  chart.update();
}
</script>
</body>
</html>
```

## 데이터 변환 규칙

- **숫자 파싱**: 한국어 단위(만원, 억원, %)를 숫자로 변환하여 차트에 사용
  - `7,558만원` → `75580000`
  - `341.32%` → `341.32`
- **레이블**: 원본 포맷(만원, %)을 tooltip에 유지
- **색상**: 채널별 고정 색상 사용 (Meta=파랑, Google=초록, TikTok=주황)
- **WoW 데이터**: 이번 주/지난 주를 그룹형 막대로 나란히 표시

## 추가 안내

렌더링 후, 사용자에게 "표로 보시겠어요?" 또는 "보고서 형식으로 변환하시겠어요?"를 제안한다.
