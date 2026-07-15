---
name: render-table
description: >
  This skill should be used when the user asks to "표로 보여줘", "테이블로 정리해줘",
  "표 형식으로 출력해줘", "render as table", "show as table", or wants MCP data
  displayed in a formatted table. Use whenever laighthouse MCP tool results
  need to be presented in a structured, scannable tabular layout.
metadata:
  version: "0.1.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 도구 호출 결과를 **HTML 테이블**로 렌더링한다. 데이터를 시각적으로 정리하여 비교·분석이 쉽도록 표 형식으로 출력한다.

## 실행 순서

1. 사용자가 요청한 MCP 도구(`mcp__laighthouse__*`)를 호출하여 데이터를 가져온다.
2. 결과 데이터의 구조를 파악한다 (배열인지, 객체인지, 중첩 구조인지).
3. `mcp__visualize__show_widget`을 사용하여 HTML 테이블로 렌더링한다.

## 테이블 렌더링 규칙

- **헤더 행**: 컬럼명은 굵게, 배경색을 적용한다.
- **데이터 행**: 짝수/홀수 행에 교차 배경색(zebra striping)을 적용한다.
- **숫자 정렬**: 숫자 컬럼은 오른쪽 정렬한다.
- **증감 표시**: 양수는 초록색(`▲`), 음수는 빨간색(`▼`)으로 표시한다.
- **반응형**: `overflow-x: auto` 래퍼를 적용하여 가로 스크롤을 지원한다.
- **합계/평균 행**: 별도 스타일로 강조한다.

## HTML 테이블 템플릿

```html
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 16px;">
  <h2 style="margin-bottom: 8px; font-size: 18px; color: var(--text-color);">{제목}</h2>
  <p style="color: var(--text-secondary, #666); font-size: 13px; margin-bottom: 16px;">{설명}</p>
  <div style="overflow-x: auto;">
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
      <thead>
        <tr style="background: var(--accent-color, #3b82f6); color: white;">
          <th style="padding: 10px 12px; text-align: left; white-space: nowrap;">{컬럼1}</th>
          ...
        </tr>
      </thead>
      <tbody>
        <!-- 짝수 행: background: var(--bg-secondary, #f8fafc) -->
        <!-- 홀수 행: background: transparent -->
        <!-- 합계 행: font-weight: bold; border-top: 2px solid -->
      </tbody>
    </table>
  </div>
</div>
```

## 데이터 타입별 처리

- **배열(Array)**: 각 요소를 행으로, 키를 열로 렌더링
- **단일 객체**: 키-값 두 컬럼으로 렌더링
- **중첩 구조**: 최상위 레벨로 평탄화(flatten)하거나 그룹 헤더 행으로 처리
- **빈 데이터**: "데이터가 없습니다" 메시지를 테이블 내에 표시

## 추가 안내

렌더링 후, 사용자에게 "차트로 보시겠어요?" 또는 "보고서 형식으로 변환하시겠어요?"를 제안한다.
