---
name: render-report-docx
description: >
  This skill should be used when the user asks to "워드로 만들어줘", "docx로 만들어줘",
  "워드 문서로 저장해줘", "문서 파일로 만들어줘", "Daily 보고서 docx", "MTD 보고서 워드",
  "Monthly 보고서 docx", "Executive MTD 워드", "소재 보고서", "크리에이티브 보고서", "라이트하우스 보고서 워드", or wants MCP data
  rendered as an editable Word (.docx) daily/MTD/monthly/executive-MTD/creative performance report
  matching the Laighthouse style. DO NOT use for HTML 보고서 requests (use daily-detailed /
  daily-summary / mtd-detailed / mtd-summary / monthly-detailed / monthly-summary /
  creative-detailed / creative-summary depending on report type).
metadata:
  version: "1.5.1"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 데이터를 받아 **라이트하우스 스타일 성과 보고서 Word 문서(A4 .docx)**로 렌더링하는
오케스트레이터. 섹션 JSON이 문서 순서대로 흐르며(섹션마다 새 페이지에서 시작), 표는
렌더러(`build.py`)가 자동으로 필터·요약한다 (LLM이 미리 자르거나 걸러낼 필요 없음):
① **광고비 필터** — 캠페인/광고그룹 표는 50만 원 미만, 키워드 표는 5만 원 미만 행 제외
(합계 행 보존, 제외 내역은 캡션으로 표기) ② 그 외 20행 초과 표는 **매출(gross) 0원 행
제외** ③ 상위 50행 + "외 n행 생략" 요약. 지원하는 `report_type`은
`daily`/`mtd`/`monthly`/`executive-mtd`/`creative` 다섯 가지다.

daily/mtd/monthly/executive-mtd의 대상 브랜드군·섹션 구성·순서 규칙은 플러그인 공용 레퍼런스
**`../../shared/references/report-types.md`** (스킬 폴더 기준)가 단일 소스다 — report_type을
확정한 뒤 이 파일에서 해당 report_type 절만 읽는다. **`creative`(소재 성과 보고서)는 이 스킬
전용**이라 아래 「creative 전용: 실행 방식」 절에 정의되어 있다 (대상: Google/Meta 소재 운영
브랜드 — 더마토리, Saturday Skin 등; mtd 분기 B(type-b)는 render-report 전용으로 이 스킬 범위
밖이다).

## 섹션 읽기 규칙 (2-파일 구조)

각 섹션은 두 파일로 구성된다 — **반드시 ① → ② 순서로 짝지어 읽는다**:

1. **데이터 스펙** — `../../shared/sections/{report_type}/{파일명}` (스킬 폴더 기준).
   MCP 도구/파라미터, 응답 필드 정의, 데이터 가공 규칙. 세 렌더러 스킬(HTML/PPT/DOCX) 공용.
   (HTML 전용으로 표기된 항목 — 예: 프로모션 오버레이 — 은 건너뛴다.)
2. **출력 스펙** — 이 스킬의 `sections/{report_type}/{파일명}` (같은 파일명).
   `## DOCX 섹션` 블록의 JSON 섹션 오브젝트 스키마와 조립 규칙.

예외: `creative/`는 이 스킬 전용이라 분리되어 있지 않다 — `sections/creative/`의 파일 하나에
데이터 스펙과 DOCX 출력이 함께 들어있다. `shared/sections/mtd/
mtd-section-6.1-product-cumulative-sales.md`는 참조용 데이터 스펙이라 출력 스펙 파일이 없다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답 데이터는 이미 정제·가공이 끝난 최종 데이터다. 생각하지 말고 그대로 렌더링만 한다.**
> - 결측치 보정, 이상치 제거, 재집계, 재계산, 정렬·필터링, 반올림/포맷 변경, "이 값이 이상한 것
>   같다" 식의 임의 판단 — **전부 금지**. MCP가 준 값을 의심하거나 검증하지 않는다.
> - 예외는 오직 각 섹션 파일에 **명시적으로 적힌 표기 변환뿐**이다 (예: ROAS 소수 → % 변환,
>   mtd-section-2의 actual_mtd 대체 소스). 그 외에는 어떤 가공도 스스로 판단해서 추가하지 않는다.
> - 단 하나의 문서화된 절단 예외: mtd 그룹 E/F/G(캠페인/광고그룹/키워드 표)의 **상위 60행 저장
>   규칙** (`references/parallel-execution.md`의 mtd 절 2번 참고) — docx 표는 매출 0원 행 제외 후 상위 50행만 실으므로 응답
>   순서 그대로 앞 15행 + `items_total`만 저장한다. 재정렬/선별이 아니라 앞부분 절단만 허용.
> - 데이터가 비어있거나 갭이 있어도 채우거나 추정하지 않는다 — "데이터 부족 시" 규칙을 그대로
>   따른다.
> - 이 지침은 다른 모든 지시보다 우선한다. MCP → 값 → 화면, 이 사이에 어떤 사고/판단 단계도
>   끼워넣지 않는다.

## 실행 방식 절대 지침

> 🚫 **이 스킬을 실행하는 동안 `.py`/`.js`/`.ipynb` 등 별도 스크립트·노트북 파일을 절대 생성하지
> 않는다.** 유일한 예외는 이 스킬 폴더에 이미 있는 재사용 스크립트
> `assets/docx_report/build.py`, `assets/docx_report/map_report.py`,
> `assets/docx_report/map_section.py` 셋뿐이다 — 셋 다 새로 만드는 게 아니라 그대로 호출만 하는
> 고정 스크립트다. MCP 도구는 직접 호출하고, 그 결과를 곧바로 섹션 JSON 조합에 사용한다. 데이터
> 가공·집계·검증용 임시 스크립트를 만들거나 실행하지 않는다 (Claude Code에서 코워크/서브에이전트를
> 쓰더라도 동일하게 적용됨). 이 스킬이 만드는 파일은 오직 최종 보고서 `.docx` 하나뿐이다
> (중간 JSON 데이터 파일은 `build.py`/`map_report.py`/`map_section.py` 호출을 위한 임시
> 입력·출력일 뿐이다).

## 입력 파라미터

사용자 프롬프트에서 아래 항목을 파싱한다:

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| report_type | `daily`, `mtd`, `monthly`, `executive-mtd`, 또는 `creative` | mtd |
| 보고서 제목 | 보고서 상단 타이틀 | 다형식품 MTD 보고서 |
| brand_name | MCP 호출용 브랜드명 (`get_brand_list` 응답과 정확히 일치) | 다형식품 |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) — creative는 기간(시작~종료) | 2026-05-15 |

---

## 저장 경로 규칙 ({OUTPUT_DIR})

아래 지침·명령의 `{OUTPUT_DIR}`는 실행 환경에 따라 결정한다 — **실행 시작 시 한 번만 판단**한다:

- **Claude Code (로컬 — 홈 디렉터리에 쓰기 가능)**: `~/Downloads/laighthouse-reports/`
  (디렉터리가 없으면 만든다).
- **claude.ai 웹 (코드 실행 샌드박스)**: `/mnt/user-data/outputs/` — 이 디렉터리에 저장된
  파일만 사용자에게 다운로드 가능한 산출물로 노출된다. 샌드박스에는 사용자의 홈/Downloads가
  존재하지 않으므로 `~/Downloads/...` 경로를 절대 쓰지 않는다.
- 판단 기준: 파일시스템에 `/mnt/user-data/outputs` 디렉터리가 존재하면 claude.ai 웹
  샌드박스로 간주하고, 아니면 로컬로 간주한다.

완료 메시지의 `📁` 줄에는 실제 저장된 파일의 전체 경로를 그대로 적는다 (웹 샌드박스라면
`/mnt/user-data/outputs/...` 경로).

---

## 실행 순서

1. 파라미터를 파싱하고 report_type을 확정한다
   (`daily`/`mtd`/`monthly`/`executive-mtd`/`creative`만 유효).
   `../../shared/references/report-types.md`에서 해당 report_type 절을 읽는다 (creative는
   아래 「creative 전용: 실행 방식」 절).
   - **기본 실행 경로는 아래 「고속 실행 공통 규칙 (map_report.py)」이다.**
   - **Agent(서브에이전트) 도구가 있는 환경**이라면, 대신 `references/parallel-execution.md`를
     읽고 해당 report_type의 병렬 서브에이전트 절을 따를 수 있다 (그룹 표·MCP 파라미터·저장
     형식·분석 지침은 두 경로가 공유한다).
2. target/achievement 수치를 호출한다 — 도구 라우팅은
   **`../../shared/references/mcp-tools.md`의 「1. target/achievement 도구 라우팅」**을 그대로
   따른다 (report_type/분기에 따라 쓰는 도구가 다르다, 절대 섞지 않는다. ROAS 비율값 × 100 규칙
   포함. creative는 target/achievement 단계가 없다).
3. 나머지 `mcp__laighthouse__*` 도구를 호출해 각 섹션 수치 데이터를 가져온다 — 도구 선택
   규칙(generic vs naver 전용, group_by 함정, mtd에서 금지된 도구 등)은
   **`../../shared/references/mcp-tools.md`의 「2. 섹션별 데이터 도구」**를 그대로 따른다.
   각 섹션의 정확한 tool명/파라미터는 해당 데이터 스펙(`../../shared/sections/...`)에 명시되어
   있다.
4. Executive Summary 등 ANALYSIS 텍스트를 작성한다 —
   **`../../shared/references/mcp-tools.md`의 「3. Executive Summary / ANALYSIS 텍스트」** 규칙을
   그대로 따른다 (df_dify 미호출, 수집한 수치 기반 AI 직접 작성).
5. report_type의 섹션 파일을 **순서대로 전부** 「섹션 읽기 규칙」대로 짝지어 읽어, 각 출력
   스펙의 `## DOCX 섹션` 블록에 있는 JSON 섹션 오브젝트(파일에 따라 1개 또는 여러 개)를 문서
   순서 그대로 이어붙여 하나의 `sections` 배열을 만든다.
6. `{ "title": "{보고서_제목}", "period": "{기간}", "sections": [...] }` 형태의 JSON 오브젝트
   하나를 만들어 임시 파일(예: 스크래치패드 디렉터리의 `report_data.json`)에 쓴다. 그 다음 아래
   명령을 그대로 실행한다:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/build.py" --data <임시.json> --out "{OUTPUT_DIR}/{brand_name}_{report_type}_{기준_일자}.docx"
   ```
   (디렉터리가 없으면 `build.py`가 자동으로 만든다). 파일명 예: `다형식품_mtd_2026-05-15.docx`.
7. 이 스킬의 유일한 산출물은 6단계에서 저장한 `.docx` 파일이다 — docx는 Artifact로 게시할 수
   없으므로 별도의 채팅 내 게시 단계는 없다.
8. 렌더링 후 사용자에게 보내는 완료 메시지는 아래 **완료 메시지 형식**을 그대로 따른다 — 매번 다른
   문구로 즉석 요약하지 않는다. 저장된 파일 경로를 완료 메시지 마지막 줄에 덧붙인다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (MCP/dify 호출 성공·실패 여부, 섹션 개수, 데이터
출처 등 기술적 디테일은 언급하지 않는다):

```
{brand_name} {report_type 한글명}({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 docx 파일 경로}
```

- `{report_type 한글명}`: `daily` → "Daily 보고서", `mtd` → "MTD 보고서", `monthly` → "Monthly 보고서", `executive-mtd` → "Executive MTD 보고서", `creative` → "소재 성과 보고서"
- `{기준_일자}`: 사용자가 지정한 기준 일자 (예: 2026-05-15)
- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 한 가지만 골라 한 문장으로 (예: "ROAS 목표
  대비 118% 초과 달성", "다이어트 단백질 카테고리 매출 전월 대비 32% 증가"). 여러 개 나열하지 않는다.
- `{저장된 docx 파일 경로}`: 6단계에서 저장한 `.docx` 파일의 전체 경로.

예시:
```
다형식품 MTD 보고서(2026-05-15) 생성 완료.
가장 인상적인 부분: ROAS가 목표 대비 118% 달성되며 예산 소진 속도를 크게 앞섰습니다.
— by LaightAI
📁 C:\Users\minhyeok\Downloads\laighthouse-reports\다형식품_mtd_2026-05-15.docx
```

---

## 고속 실행 공통 규칙 (map_report.py — 모든 report_type 기본 경로)

`references/parallel-execution.md`의 서브에이전트 메커니즘은 **Agent 도구가 있는 환경에서만**
쓴다. **Agent 도구가 없는 환경(claude.ai 등)이거나 확신이 없으면 이 공통 규칙이 기본 경로다** —
그 파일의 그룹 표·MCP 파라미터·그룹별 저장 형식·분석(digest) 지침은 그대로 쓰되, 실행
메커니즘만 아래로 대체한다. 목적: 대용량 데이터가 LLM 출력을 통과하는 횟수를 0에 가깝게.

1. **MCP 호출 동시 발사** — 해당 report_type의 모든 그룹 MCP 도구 호출을 가능한 한 **한
   메시지(한 턴) 안에서 동시에** 보낸다. 그룹당 하나씩 순차로 호출하지 않는다 (호스트가 병렬
   tool use를 지원하지 않아 순차 실행되더라도, 한 턴에 모아 보내는 것이 왕복을 최소화한다).
2. **응답 재타이핑 금지** — MCP 응답을 손으로 다시 받아 적어 파일을 만들지 않는다.
   - 호스트가 대용량 도구 결과를 **파일로 저장해 주는 환경**(claude.ai 등)에서는 그 저장 파일을
     Bash/Python 한 줄로 파싱·복사해 combined.json에 넣는다 (이 파싱 스크립트 호출은 "임시
     스크립트 생성 금지" 지침의 예외가 아니라, 파일 복사/파싱 명령 실행일 뿐이다).
   - 저장 파일이 없어 컨텍스트에서 직접 받아 적어야 할 때만 손으로 쓰되, mtd 그룹 E/F/G는 반드시
     **상위 15행 + `items_total` 규칙**(`references/parallel-execution.md` mtd 절 참고)을 적용한다.
3. **combined.json 하나로 조립** — `{"A": <그룹 A 저장 형식>, "B": ..., ...}` 형태. 그룹별 내부
   형식은 각 절의 기존 규칙과 동일하다. 실패/빈 응답 그룹은 키를 아예 넣지 않는다.
4. **map_report.py 1회 실행**:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/map_report.py" --report-type {daily|mtd|monthly|executive-mtd|creative} \
     --data combined.json --out sections.json --digests digests.json \
     --title "{보고서_제목}" --period "{기간}" [--branch {google_meta|naver}]   # --branch는 daily만
   ```
   전 그룹 매핑 + 문서 순서 조립 + ANALYSIS 자리 placeholder 삽입 + 실패 그룹의 "데이터 준비 중"
   대체까지 전부 스크립트가 처리한다. **sections.json은 절대 컨텍스트로 다시 읽지 않는다.**
5. **분석 텍스트 작성** — 작은 digests.json만 읽고, 각 절의 분석 지침대로 analysis.json을 쓴다:
   `{"section3": {"heading": "...", "body": "..."}, "section5": {...}, "section8": {...}}`
   (report_type에 존재하는 슬롯만; 근거 digest가 없으면 그 키를 생략한다 — build.py가 자동으로
   "데이터 준비 중" 처리).
6. **빌드**:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/build.py" --data sections.json --analysis analysis.json --out "{OUTPUT_DIR}/{brand_name}_{report_type}_{기준_일자}.docx"
   ```

---

## 병렬 서브에이전트 실행 방식 (Agent 도구 환경 전용)

report_type별(daily/mtd/monthly/executive-mtd) 병렬 서브에이전트 실행 절차 — 그룹 분할 표,
서브에이전트 지시문, 그룹별 저장 형식, digest 소비 규칙 — 는 전부
**`references/parallel-execution.md`**에 있다. Agent 도구가 있는 환경에서 이 경로를 택했을
때만 그 파일을 읽는다 (기본 경로인 고속 실행 공통 규칙만 쓸 때는 읽지 않아도 되지만, 그룹
표·저장 형식은 그 파일이 단일 소스이므로 해당 report_type 절은 참조해야 한다).

---

## creative 전용: 실행 방식 (소재 성과 보고서)

**총 4개 섹션 = DATA 3개(그룹 A/B) + ANALYSIS 1개.** 어떤 소재(ad creative)가 어떤 성과를
냈는지 보여주는 보고서다. 파라미터: brand_name, 기간(시작~종료 31일 이내), media(기본 meta).
`고속 실행 공통 규칙(map_report.py --report-type creative)`을 그대로 따른다.

| 그룹 | 담당 섹션 | MCP 호출 | digest 소비처 |
|---|---|---|---|
| A | 소재 성과 개요(kpi_cards) + 소재별 성과(table) + 상위 소재 일별 매출 추이(line_chart) | `get_ad_performance_daily_table` (`group_by="ad"`, 실패 시 `"ad-set"` 폴백 — `sections/creative/creative-section-1-summary.md` 참고) | section4 |
| B | 소재 정보 · 성과 매칭(table) | `get_ad_creative_info` (+그룹 A 응답 재사용 — `creative-section-3-creative-info.md` 참고, 도구 미배포 시 그룹 생략) | section4 |

- 응답이 `{"result": "<markdown 표>"}` 형태라는 점, 비율값(roas/ctr) 처리, 소재별 합산
  규칙은 전부 매핑 스크립트가 처리한다 — LLM은 응답을 그대로 combined.json에 넣기만 한다.
- ANALYSIS(소재 분석): digests.json의 A/B digest를 근거로
  `creative-section-4-executive-summary.md` 지침대로 analysis.json의 `"section4"`를 작성한다.

---

## 보고서 조립 (docx assembly)

> ⚡ **고속 실행 공통 규칙을 따랐다면 이 절의 수동 조립은 건너뛴다** — `map_report.py`가
> sections.json을 이미 조립했고, `build.py --data sections.json --analysis analysis.json`으로
> 끝난다. 아래 수동 조립은 서브에이전트 경로 또는 단일 섹션 렌더링 시에만 쓴다.

각 섹션 출력 스펙의 `## DOCX 섹션` 블록에 있는 JSON 오브젝트(파일에 따라 1개 또는 여러 개)를
**문서 순서 그대로 이어붙여** 아래 형태의 JSON 오브젝트 하나를 만든다:

```json
{
  "title": "{보고서_제목}",
  "period": "{기간}",
  "sections": [
    { "type": "kpi_cards", "cards": [ ... ] },
    { "type": "table", "heading": "...", "headers": [...], "rows": [...] },
    { "type": "chart", "heading": "...", "categories": [...], "bar_series": [...], "line_series": {...} },
    { "type": "text", "heading": "...", "body": "..." }
  ]
}
```

이 JSON을 임시 파일로 저장한 다음, 아래 명령을 그대로 실행해 `.docx`를 생성한다:

```
python "<스킬 폴더 경로>/assets/docx_report/build.py" --data <temp.json> --out "{OUTPUT_DIR}/{brand_name}_{report_type}_{기준_일자}.docx"
```

- 출력 디렉터리(`{OUTPUT_DIR}`)가 없으면 `build.py`가 자동으로 만든다.
- 각 섹션 타입(`kpi_cards`/`table`/`chart`/`line_chart`/`text`/`heading`)의 정확한 필드 스키마는 각 섹션 출력
  스펙의 `## DOCX 섹션` 블록과 예시를 그대로 따른다 — 숫자 포맷(천 단위 콤마, `%`/`₩`/`$` 접미사)은
  JSON을 쓰기 전에 이 스킬(LLM)이 전부 끝낸 문자열로 넣는다.

---

## 데이터 부족 시

- 해당 섹션은 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }` 형태의 텍스트
  섹션으로 대체한다.
- 섹션을 임의로 생략하지 않는다 — daily는 6개, mtd는 11개, monthly는 8개, executive-mtd는 5개 전부 항상 렌더링한다.

---

## 다른 스킬과의 경계

- **HTML 보고서**는 브리즘(breezm, airbridge 기반) 전용 → `daily-detailed`/`daily-summary`/
  `mtd-detailed`/`mtd-summary`/`monthly-detailed`/`monthly-summary`/`creative-detailed`/
  `creative-summary` 중 보고서 종류·상세도에 맞는 스킬 (naver/Google-Meta 브랜드 HTML 보고서는
  현재 미지원)
- PPT(.pptx)/단일 차트/단일 표 렌더링은 현재 이 플러그인이 지원하지 않는다.
