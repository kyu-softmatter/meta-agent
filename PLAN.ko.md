# meta-agent 계획서

버전 v0.3.1 · 2026-10-29 · 상태: **구축 전 초안, 사람 승인 대기**
부제: Meta-Agents for Scientific Agent Development and Self-Improvement

---

## 변경 이력

### v0.3.1 변경 요약 (v0.3 → v0.3.1)

자료 투입구 하나만 손봤다. v0.3은 자리와 형식을 정했지만, 사람이 날짜 폴더를 만들고 `MATERIAL.json`의 일곱 필드를 직접 써야 했다. v0.3.1은 **사람은 링크 한 줄이나 파일 하나만 넣고, 나머지는 Meta-Agent가 채워 사람이 확정하도록** 바꾼다(사용자 지시: "추후 사용자가 해당 링크를 넣을 수 있도록 디자인").

| 변경 | 내용 | 출처 |
|---|---|---|
| 투입의 최소 단위 (§0, §5.0) | 사람이 하는 일은 둘 중 하나: `inbox/materials/LINKS.md`에 링크 한 줄, 또는 `inbox/materials/drop/`에 파일 하나. 폴더 생성과 `MATERIAL.json` 작성은 Meta-Agent가 한다(`added_by: human`, 메타데이터는 `inferred`, 확정은 사람) | 사용자 지시 |
| 들어오는 길 다섯 (§5.0, §5.7) | LINKS.md · drop 폴더 · 마법사 질문 0의 답 · (M2 이후) `add-material` 명령 · (M9, 선택) GUI의 "Add material". 어느 길로 와도 같은 `material` 카드가 된다 | 이 문서 |
| 접수와 재진입 (§5.0) | 접수(Meta-Agent가 메타데이터를 채움) → 사람 확정 → F1 증류 → S0 발견 단계를 그 항목에 대해서만 재실행 → `v<N>_lab_profile`·레지스트리·`tool_profile` 개정 **제안**. 진행 중인 요청에는 `superseded` 알림만, 자동 교체 없음 | 이 문서 |
| 링크의 기록 규칙 (§5.0, §9) | URL은 내용이 바뀌므로 `retrieved_at`과 `content_hash`를 반드시 적고, 원문 사본은 `may_quote`·라이선스가 허락할 때만. 자격 증명이 필요한 링크는 접근하지 않고 `held` | REA(증거 출처 보존), 이 문서 |
| `material` 상태기계 (§6.5) | `queued → registered → distilled / declined / held` | 이 문서 |
| 체크 17 (§8) | `location`은 `url`과 `path` 중 정확히 하나; 메타데이터는 세 상태 어휘; `distilled`인 URL 자료에 스냅샷 없으면 FAIL; `may_quote`가 `true`가 아니면 원문 사본 금지; `held`·`declined`에 사유 | 이 문서 |
| 레이아웃·M0·M2 (§7, §12, §15) | `inbox/materials/{README.md, LINKS.md, drop/}`가 M0에 생긴다(README는 "A link on one line is enough"로 시작). 접수 로직과 `add-material` 명령은 M2 | 이 문서 |
| §14-18 | 질문이 아니라 **자리**로 고쳐 쓴다. 2026-10-29 현재 자료 없음, 나중에 투입 예정 | 사용자 지시 |

### v0.3 변경 요약 (v0.2 → v0.3)

| 변경 | 내용 | 출처 |
|---|---|---|
| 온보딩과 적응형 설치 마법사 (신설 §5.0) | Meta-Agent의 첫 진입점을 **Agent Setup Wizard**로 정한다. 순서는 자료 발견 → 적응형 질문 → 구성 제안 → 승인과 생성. **먼저 분석하고 나중에 묻는다.** 이미 파악한 것은 묻지 않고, 정책·권한·공개 범위는 추론으로 채우지 않는다 | 대화 2, 사용자 지시 |
| 세 상태 어휘 | 설정 값마다 `confirmed`(사람이 확정) / `inferred`(코드·문서에서 추론, 근거 필수) / `unknown`. 추론은 추천으로만 쓰인다 | 대화 2 |
| 자료 투입구 (§0, §5.0) | 선호하는 시뮬레이션 엔진·실험 플랫폼의 **PDF와 링크를 언제든 넣을 수 있는 자리** `meta_agent/inbox/materials/`. 마법사가 처음에 묻고, 나중에 들어온 자료는 발견 단계만 다시 돈다 | 사용자 지시 |
| Lab Profile (§5.6) | 연구실의 선호 엔진·장비, 하드웨어, 소프트웨어 환경, 기존 코드, 과학적 관행, GUI 선호, 운영 제약, 협업·정책. 에이전트 생성에 쓰는 환경 정보이지 중앙 관리가 아니다 | 대화 2 |
| Simulation Method Registry (§5.6) | **물리 스케일 → 모델링 방법 → 시뮬레이션 엔진**을 분리하고 방법과 엔진은 다대다. 장비(실험 플랫폼) 레지스트리를 나란히 둔다. 목록이지 순위가 아니다 | 대화 2 |
| GUI, 선택 기능 (§5.7) | Designer 산출물에 `gui_spec`과 GUI 구성요소를 **선택적으로** 더한다. 공통 틀(Project · Parameters · Validation · Execution · Results) + 도메인 편집기 + 도구별 과학 코어·어댑터. GUI는 capability spec에서 유도되고 과학 판단의 원천이 아니다 | 대화 2, HOOMD_GUI |
| 메타 원칙 MP11–MP13 | 발견은 추천이고 확정은 사람의 것 / 연구실의 기존 도구를 존중한다 / GUI는 과학 판단의 원천이 아니다 | 대화 2, HOOMD_GUI |
| 단백질 영역 보강 (§5.3) | 검색 경로(자연 / 설계 / 구조 / 실험 물성 → 교차 검증 → 카드), 연성물질 조건(올리고머화, 결합 부위, 가교, 농도·온도·용액), 구성 정보와 조건 의존 측정값의 분리, 데이터 접근 후보(PDA 처리 코드, Proteinbase 데이터셋, RCSB API) | 대화 2 |
| 멀티스케일 결합 | Meta-Agent가 엔진을 통합하지 않는다. 인터페이스와 변환 조건을 명시하고 브릿지나 결합 도구가 맡는다 (§10, §13) | 대화 2 |
| 검증 체크 15·16·B10 | Lab Profile 상태와 정책 필드 확정, 질문이 `unknown` 필드만 겨냥하는지, GUI 필드의 capability 매핑과 임계값 부재 | 이 문서 |
| 마일스톤 | M1에 마법사 골격, M2에 레지스트리 씨앗, **M9(선택) GUI** 추가 | 이 문서 |
| 열린 질문 16–19 | GUI 범위와 기술, Lab Profile의 범위, **선호 엔진·플랫폼 자료**, 이 연구실의 온보딩 답 | 이 문서 |

### v0.2 변경 요약 (v0.1 → v0.2)

| 변경 | 내용 | 출처 |
|---|---|---|
| 역할 분리 | **Meta-Agent**(다른 에이전트를 구성·운영·개선하는 책임)와 그 안의 **Agent Designer**(새 도구를 위한 에이전트를 설계·생성·검증하는 역할), 그리고 **Scientific Agent**(연구 과제 자체의 계획과 실행)를 구분 | 제안서 §1, §2.3 |
| 두 루프 | **Scientific Research Loop**(연구 조건을 갱신, 주체는 Scientific Agent)와 **System Improvement Loop**(에이전트를 수정, 주체는 Meta-Agent)를 분리하고 각각 따로 평가 | 제안서 §2.4 |
| 두 개선 경로 | **Knowledge-based improvement**(문헌·실행 사례의 재사용)와 **Structural improvement**(메타하네스가 역할·도구 선택·지침·검증 워크플로를 수정)를 분리. 평가는 네 조건(없음 / 구조만 / 지식만 / 둘 다) | 제안서 §2.1, §2.4 |
| Tool Understanding 단계 추가 | Agent Designer의 첫 단계로 매뉴얼·API·스크립트·소스·(권한이 확인된) 바이너리를 분석해 `tool_profile` 카드를 만든다. 모든 주장은 **observed / derived / inferred / unknown** 중 하나로 표시하고 증거와 한계를 함께 싣는다 | 제안서 §2.3, REA |
| 두 검증의 분리 | **Interface validity**(호출·응답·오류 처리·설정 전달)와 **Scientific validity**(물리량·단위·조건·모델 가정·기준 결과)를 별도 게이트로. 인터페이스가 돌아도 과학적 유효성이 없으면 완성이 아니다 | 제안서 §2.3, 대화 1 §3.4 |
| Designer의 산출물 명시 | capability specification · callable tools · steering instructions · validation tasks · deployment configuration. 이것이 번들의 내용이다 | 제안서 §2.3 |
| 하네스 표면의 정의 | 빌드된 에이전트의 편집 가능한 표면을 여덟 구성요소(system prompt, guardrails, memory, tool guidance, skills, subagents, scripts, plugins/hooks)로 정의하고 번들 파일에 대응. 편집 계약은 "생략은 상속", 유효하지 않은 제안은 통째로 폐기, 비용 순서는 skill > script > subagent > hook > 상시 산문 | harness2 |
| 두 수준의 재귀 | 빌드 수준(한 요청 안에서 후보 k개를 같은 검증 과제로 probe하고 compose)과 하네스 수준(도메인별 라이브러리에 채택된 하네스와 교훈을 축적) | harness2 |
| 경험 기록 형식 | 사례 카드에 `cue / lesson / evidence / confidence`, 원인 상태 `observed / suspected / confirmed`. 제안 카드에 `edit_rows[]`와 판정 `helped / hurt / no_observed_effect / confounded` | harness2, 대화 1 §6 |
| 파라미터 출처 어댑터 | NIST ThermoML·Chemistry WebBook·PubChem·CoolProp·chemicals/thermo·NIST potentials·OpenFF·Zenodo·레올로지 공개 데이터셋, 단백질(UniProt·PDB·PDA·Proteinbase·AlphaFold DB·ModelArchive·ProtaBank·InterPro)을 **확인 필요 후보**로 등재. 계층형 검색과 `value_kind` 구분 | 대화 1 (NIST·UniProt 질문) |
| 에러 계약 | 생성된 callable tool은 구조화된 에러(category · retryable · remediation)를 반환해야 한다 | REA `error-contract` |
| fail-closed 통합 | 범위·권한·부작용·검증 질문이 미해결인 기능은 통합하지 않고 `held`로 둔다 | REA `AGENTS.md`, SMA 브릿지의 hold |
| 테스트베드 | A 기존 SMA 에이전트(현미경·HOOMD), B TA Instruments 레오미터, C RheoTool(C++/OpenFOAM), 교차 검증은 브릿지 | 제안서 §2.3 |
| 평가 지표 | 개발 노력, 연구자 개입, 첫 과학적 유효 실행까지의 시간, 과학적 유효성, 네 조건 비교, 운영 효율(비용은 장부에서) | 제안서 §2.4, 대화 1 §11 |
| 마일스톤 | M0–M8로 확장(테스트베드 C·B 추가). 첫 실제 에이전트 권고: **C RheoTool**(소프트웨어만, 비파이썬 인터페이스) 다음 B | 제안서, 이 문서의 판단 |

---

## 0. 이 문서의 위치, 언어, 참고 자료

- 이 문서는 **구축 전 계획서**다. 폴더 외에는 아직 아무것도 만들지 않았고, 승인되면 §15의 순서로 M0를 시작한다.
- 언어 규약: 계획서는 한국어. 실행 코드, 카드, `CLAUDE.md`, `README.md`, 작업 메모(`tasks/`, `failures.jsonl`, `docs/ideas/`)는 영어.
- 설계 기록(`plan.md`)의 언어는 열린 질문 §14-2다. **권고**: 승인 뒤 이 문서를 영어 `plan.md`로 옮겨 기록으로 삼고, 이 한국어 문서는 `docs/origin/PLAN.ko.md`로 동결한다. 참고 레포는 한국어/영어 쌍을 하루 만에 포기했다(SMA plan.md §0).

**참고 자료.** 이 문서에서 다음 이름으로 인용한다.

| 약칭 | 자료 | 가져오는 것 |
|---|---|---|
| **SMA** | https://github.com/kyu-softmatter/soft-matter-agents | 카드·게이트·좌석·작업 큐·실패 기록·메타하네스 규칙(§8.3). 원칙 P0–P16은 인용하고 베끼지 않는다 |
| **제안서** | 「Meta-Agents for Closed-Loop Simulation and Experimentation」(연구 제안서 초안). **AWS 배포·운영·예산 부분(§2.5, §4)은 참고하지 않는다** | 역할 정의, 두 루프, 두 개선 경로, Designer의 산출물, 두 검증, 테스트베드, 평가 설계 |
| **REA** | https://github.com/morluto/rea (Reverse Engineer Anything, MIT) | 소프트웨어·저장소 분석의 규율: 관찰/유도/추론/미지의 구분, 증거 출처 보존, 미지 등록, 에러 계약, fail-closed 통합, 읽기 전용 기본 |
| **harness2** | https://github.com/google-research/harness2 (Apache-2.0) | 하네스 표면의 여덟 구성요소, Propose–Probe–Compose, 두 수준의 재귀, 편집 계약, 비용 순서, 경험 기록 형식, 예산 장부, 기준선 우선 |
| **대화 1** | ChatGPT 공유 대화 「Meta-Agent 계획 수립」 (https://chatgpt.com/share/6ae3747c-b860-83e8-85c2-1e9b1121c126) | 기능 구획과 용어, 평가 지표, 파라미터·단백질 출처 후보 |
| **대화 2** | 같은 제목의 두 번째 공유 대화 (https://chatgpt.com/share/6ae37853-e874-83e8-a21f-ac4f252c5e94) | 단백질 DB 보강, 스케일·방법·엔진의 분리, Lab Profile, GUI, 설치 마법사와 적응형 질문, 세 상태 어휘 |
| **HOOMD_GUI** | https://github.com/kyu-softmatter/HOOMD_GUI (사용자의 저장소, 2026-10-29 README 기준 "idea sketch / concept document") | 입자 기반 시뮬레이션 GUI의 참고 사례: 시각적 모델링, 투명한 코드 생성, 과학 코어의 분리, 재현성 우선, 실행 전 검증 |

**미확인 사실의 표시.** 대화에서 온 데이터베이스·라이브러리·엔진 정보(존재, 접근 방식, 수록 범위, 라이선스)는 **이 문서가 검증하지 않았다**. 그런 항목은 "(확인 필요)"로 표시하고, 확인은 M2/M3의 첫 작업이며 결과는 `knowledge/sources/`의 출처 기록이나 레지스트리 항목으로 남긴다. 확인되지 않은 것을 확인된 것처럼 적지 않는다(SMA P1, 수는 실행에서 읽는다).

**자료 투입구.** 선호하는 시뮬레이션 엔진이나 실험 플랫폼의 매뉴얼·논문·사양서·저장소 링크는 **언제든** 넣을 수 있다. 사람이 하는 일은 `meta_agent/inbox/materials/LINKS.md`에 링크 한 줄을 쓰거나 `inbox/materials/drop/`에 파일 하나를 두는 것뿐이고, 분류·출처 기록·레지스트리 반영은 Meta-Agent가 하고 사람은 확정만 한다(절차와 형식은 §5.0). 계획 단계인 지금은 이 문서의 §14-18이 그 자리다. 지금까지 이 계획이 알고 있는 도구는 다음 넷이고, 각각에 대한 자료는 아직 받지 않았다. 없어도 설계와 M0는 진행된다.

| 도구 | 종류 | 아는 경로 | 기다리는 자료 |
|---|---|---|---|
| HOOMD-blue | 엔진 (MD·BD) | SMA 시뮬레이션 에이전트, HOOMD_GUI | 연구실이 쓰는 버전·스크립트·관행 |
| 현미경 (SMA 현미경 에이전트의 장비) | 장비 | SMA | 제어 소프트웨어 문서, 안전 규칙의 자리 |
| TA Instruments 레오미터 | 장비 | 제안서 | 제어 소프트웨어·API 문서, 분석 권한의 근거 |
| RheoTool / OpenFOAM | 엔진 (CFD, 점탄성) | 제안서 | 사용 버전, 튜토리얼 케이스, 연구실 설정 |

---

## 1. 목적

### 1.1 세 역할, 한 문장

- **Meta-Agent**: 다른 에이전트를 구성·운영·개선하는 책임을 지는 에이전트. 이 레포의 유일한 에이전트다. 스스로는 장비를 만지지 않고 시뮬레이션을 돌리지 않는다.
- **Agent Designer**: Meta-Agent 안의 역할. 새 도구(장비, 시뮬레이션 엔진, 분석 소프트웨어)를 위한 Scientific Agent를 **설계·생성·검증**한다. 산출물은 capability specification, callable tools, steering instructions, validation tasks, deployment configuration, 그리고 선택적으로 GUI specification이다(제안서 §2.3, 대화 2).
- **Scientific Agent**: 연구 과제 자체의 계획과 실행을 맡는 에이전트. SMA의 현미경·시뮬레이션 에이전트가 그 예다. Meta-Agent가 **만드는 대상**이지 Meta-Agent의 일부가 아니다.

**한 문장.** Meta-Agent는 연구실의 환경을 먼저 읽고(Onboarding), 과학 에이전트를 만들고(Agent Designer), 만든 에이전트가 연구에서 겪은 지식과 경험으로 더 나아지게 한다(Self-Improvement). 만드는 것은 번들(디렉터리)이고, 바꾸는 것은 제안 카드이며, 기억하는 것은 사례다.

### 1.2 두 루프

| 루프 | 순환 | 주체 | 목표 |
|---|---|---|---|
| **Scientific Research Loop** | 연구 목표 → 실험·시뮬레이션 계획 → 실행 → 결과 분석 → 다음 조건 | Scientific Agent | 더 나은 과학적 결과 |
| **System Improvement Loop** | 에이전트 실행 → 성공·실패 평가 → 원인 분류 → 지식 또는 구조 개선 → 재검증 | Meta-Agent | 더 나은 에이전트의 성능과 신뢰성 |

두 루프는 실행 결과와 평가 정보로 이어지지만 목적이 다르고, **평가도 따로** 한다(제안서 §2.4). Meta-Agent는 첫 루프를 돌리지 않는다. 그 루프의 결과를 읽을 뿐이다.

### 1.3 두 개선 경로

| 경로 | 무엇을 바꾸는가 | 바꾸지 않는 것 |
|---|---|---|
| **Knowledge-based** | 지식 항목과 사례를 추가·갱신하고 다음 결정이 그것을 인용하게 한다 | 에이전트의 구조(지침, 도구, 검증 흐름) |
| **Structural** | 메타하네스가 역할 분담, 도구 선택, 지침, 스킬, 컨텍스트 관리, 검증 워크플로, 오류 처리를 제안으로 바꾼다 | 지식의 내용 |

두 경로의 효과는 **네 조건**(없음 / 구조만 / 지식만 / 둘 다)에서 비교한다(§11).

### 1.4 기능 (요구 사항 다섯 + 묶는 역할 하나 + 진입점 하나)

| # | 기능 | 영어 식별자 | 산출물 |
|---|---|---|---|
| **F0a** | **Onboarding & Setup Wizard**: 자료 발견 → 적응형 질문 → 구성 제안 → 승인 | `onboarding` | `discovery_report`, `lab_profile`, `onboarding_record`, `agent_goal` 초안 |
| **F0** | **Agent Designer**: 도구 이해 → 명세 → 빌드 → 두 검증 → 인계 | `designer` | `tool_profile`, `agent_spec`, `build`, `validation_report`, (선택) `gui_spec` + 번들 |
| F1 | 논문·기술 자료·실행 기록의 스캔·증류·저장 (Knowledge Engine) | `knowledge` | `knowledge_brief`, 출처 기록, 증류 노트, 항목 |
| F2 | 시뮬레이션·하드웨어 운영을 위한 파라미터 분석 (Parameter Intelligence) | `parameters` | `parameter_sheet`, (특화) `protein` 항목 |
| F3 | 메타하네스를 통한 구조 개선 (Structural Improvement) | `harness` | `incidents.jsonl`, `harness_proposal`, `ledger.jsonl`, `retro/`, `library/` |
| F4 | 실패·성공 메타데이터의 저장과 재참조 (Experience Memory) | `cases` | `case` 항목, 카드 안의 `case_refs` / `case_gaps` |
| F5 | 카드 기반 | `contracts/` | 모든 전달은 디스크 위의 카드(JSON 기록 + MD 사람용) |

### 1.5 성공 기준 (측정 가능한 형태)

1. 빌드된 번들이 **Meta-Agent 없이** 인터페이스 게이트와 과학 게이트를 모두 통과하고, 모의 질문 하나를 끝까지 처리한다 (SMA P11).
2. 지시문 변경이 제안 → 증명(픽스처 + 재생) → 소유 좌석의 착륙으로만 일어나고, 재생에서 거부는 여전히 거부되고 공백은 여전히 이름 붙는다 (SMA §8.3 규칙 7).
3. 새 요청에 관련 사례가 `case_refs`로 붙고, 없으면 `case_gaps`에 **어디를 찾았는지**와 함께 적힌다.
4. 모든 수치가 (value, unit, source, grade) 4-튜플이고, 모델이 만든 값(E6)은 카드와 저장소에 들어가지 않는다.
5. `tool_profile`의 모든 주장이 observed / derived / inferred / unknown 중 하나이고, unknown은 무엇이 있어야 풀리는지를 적는다.
6. 네 조건 비교가 같은 과제 묶음·같은 실행기·같은 시드로 **실행 가능**하고, 기준선이 먼저 판정된다.
7. 첫 과학적 유효 실행까지의 시간과 개입 횟수가 **기록에서** 읽힌다.
8. 마법사가 묻는 질문은 모두 그 시점에 `unknown`이거나 정책 필드다. 자료가 이미 답한 것을 다시 묻지 않고, 정책·권한·공개 범위는 사람이 확정하기 전에 빌드로 가지 않는다 (체크 15·16). 자료 투입도 같은 규율이다: 사람이 쓰는 것은 위치 한 줄이고, 분류·출처 기록은 Meta-Agent가 채워 사람이 확정한다 (체크 17).
9. 위 전부를 실행 결과에서 센다. 문서의 수는 세지 않는다.

### 1.6 실패 징후

- Meta-Agent가 빌드된 에이전트의 디렉터리에 직접 쓴다.
- 모델이 작성자인 안전 값이 `envelope/`에 나타난다.
- 인터페이스 게이트만 통과한 번들이 "완성"으로 인계된다.
- 픽스처 없는 제안이 착륙한다. 채택만으로 "도움이 되었다"고 적힌다.
- `tool_profile`에 추론이 관찰로 적힌다. 권한 기록 없이 바이너리가 분석된다.
- 마법사가 저장소를 읽고도 언어와 엔진을 다시 묻는다. 반대로 공개 저장소를 봤다고 공개 범위를 `confirmed`로 적는다.
- 연구실이 쓰지 않는 엔진의 에이전트가 생긴다.
- GUI 파일 안에 GUI만 아는 임계값이 생긴다. GUI의 검사가 통과했다고 실행이 허용된다.
- 사례 저장소는 커지는데 아무 카드도 인용하지 않는다.
- 지식 저장소가 둘이 되어 같은 양이 다른 값을 갖는다.
- 범용 워크플로 엔진이나 오케스트레이터가 되어 간다 (SMA P10).

---

## 2. 참고 자료에서 가져오는 것, 바꾸는 것, 가져오지 않는 것

### 2.1 SMA

**그대로(인용으로)**: 원칙 P0–P16, 카드 전달 규약 D3, 결정론적 게이트 + 거부 픽스처 + "체크와 픽스처는 같은 커밋" + "픽스처가 실패하는 것을 먼저 본다", 좌석 레지스트리와 경계 검사, `tasks/` 큐, `failures.jsonl`, `docs/ideas/`, 메타하네스 루프와 규칙 1–7(§8.3), 평평한 출력 트리, 다섯 필드 지시 / 10줄 보고, 정리 전 세 가지 디스크 조건.

**바꾸는 것**

| SMA | meta-agent | 이유 |
|---|---|---|
| 네 에이전트 + 브릿지 + 콘솔 | **에이전트 하나** (`meta_agent/`) | 사용자 결정. 필요하면 브릿지가 연결 |
| `questions/<qid>/` | `requests/<rid>/` | 입력이 측정 질문이 아니라 "에이전트를 만들어/고쳐 달라"는 요청 |
| 조건 설계 7축/6축 | 명세 여섯 축 A1–A6 (§5.1) | 설계 대상이 에이전트의 경계·인터페이스·지식·파라미터·안전·검증 |
| 실행 계층 S6 | 없음, Tier 0 | 장비도 엔진도 쥐지 않는다 |
| 사서가 유일한 지식 소유자 | 독립 모드에서는 자체 `knowledge/`가 기록, 연결되면 사서가 권위이고 여기 항목은 후보 | P14와 D5를 함께 지킨다 |
| `contracts/harness/` | `meta_agent/harness/` | 하네스가 이 에이전트의 본업 |

**가져오지 않는 것**: 장비 특정 코드와 안전 규칙의 값, 콘솔, 현미경 실시간 판단 모듈(제안서 §2.2는 SMA의 일).

### 2.2 제안서

**가져오는 것**: §1.1의 세 역할, §1.2의 두 루프, §1.3의 두 경로, Designer의 다섯 산출물, 두 검증의 분리, 테스트베드 A·B·C와 교차 검증, 평가의 네 조건과 지표, "첫 과학적 유효 closed-loop 실행까지의 시간", 재현 가능한 검증 과제와 공유 가능한 성공·실패 예시를 공개 레포에 두는 것.

**가져오지 않는 것**: AWS 배포·운영·예산(§2.5, §4), 웹 서비스와 보급 목표(100개 실험실 등), 다중 에이전트의 상시 중앙 조정(브릿지의 일).

### 2.3 REA

**가져오는 것(규율로)**: 주장을 **관찰 / 유도 / 추론 / 미지**로 구분하고 증거 출처를 보존한다. 미지는 등록하고 **무엇이 있어야 풀리는지**(권한, 환경)를 적는다. 부분 증거에서 "없음"을 결론내지 않는다. 읽기 전용이 기본이고 변경 권한은 명시된다. 설정 변경은 추가적·멱등적이고 적용 전에 계획을 보여 준다. 에러 계약(category, retryable, remediation). **fail-closed**: 범위·권한·부작용·검증 질문이 미해결이면 통합하지 않는다. "소스가 있는 저장소는 일반 도구로, 바이너리·패키지·런타임 동작은 REA로"라는 REA 자신의 사용 경계.

**가져오는 것(도구로)**: 사용·분석 권한이 확인된 장비 제어 소프트웨어·엔진 바이너리의 인터페이스·파라미터·호출 경로 조사(제안서 §2.3). MCP로 연결하며 로컬에서 돈다.

**가져오지 않는 것**: REA의 분석 엔진 자체를 이 레포에 넣는 일. 장비 컴퓨터에서의 런타임 캡처(§5.1 S2의 금지).

### 2.4 harness2

**가져오는 것(설계로)**: 하네스 = 모델 주위의 모든 것(프롬프트, 도구, 메모리, 스킬, 오케스트레이션). 여덟 편집 구성요소와 그 비용(상시 산문은 가장 비싸다). 편집 계약 "생략은 상속", 유효성 검사를 통과 못 한 제안은 통째로 폐기. Propose–Probe–Compose의 **대조적** 증거. 두 수준의 재귀와 도메인별 라이브러리. 경험 기록 `cue / lesson / evidence / confidence`와 `confounded`의 우선. 예산 장부(롤아웃·세션·비용). 기준선을 먼저 판정. 판정·보고는 같은 설정으로. 평가 자료(루브릭)에 실행기가 닿지 못하게 네트워크를 제한.

**바꾸는 것**: 채택을 모델 판정에 맡기지 않는다. 우리 probe는 모의 재생 + 결정론적 검증이고, compose는 모델이 **초안**을 쓰며, 채택은 게이트 + 소유 좌석 + (풀기면) 사람이다 (SMA §8.3 규칙 4, MP5).

**가져오지 않는 것(지금은)**: harness2 패키지를 엔진으로 설치하는 일. 실행기의 네트워크가 무제한이고 Codex 샌드박스가 꺼져 있으므로(harness2 README), 쓴다면 SMA §8.3의 2026-10-19 시험 설계(작업 폴더 밖 클론, 모의 전용, 장비 없는 컴퓨터)로만 (§14-8).

### 2.5 대화 1과 대화 2

**대화 1에서**: 기능 구획과 용어(Agent Designer / Knowledge Engine / Parameter Intelligence / Experience Memory / Meta-Harness), 평가 지표 네 묶음, 로드맵의 단계 구분, 파라미터·단백질 출처 후보와 계층형 검색, 측정값·계산값·문헌값·추정값의 구분, 관측 현상·추정 원인·확인 원인의 구분, 예측 구조 ≠ 실험 구조, 존재·구조 확인 ≠ 기능·물성 확인.

**대화 2에서**: 설치 마법사(발견 → 적응형 질문 → 제안 → 승인)와 "먼저 분석하고 나중에 묻는다", 세 상태(confirmed / inferred / unknown), 정보 충분성 검사, "충분성 판단은 권한을 승인하지 않는다", 시뮬레이션의 스케일·방법·엔진 분리와 다대다 관계, Lab Profile, 연구실의 기존 도구 존중, GUI의 공통 틀과 도메인 편집기의 분리, GUI를 capability spec에서 유도, GUI 입력 검증은 엔진 검증을 대체하지 않음, 단백질 검색 경로와 연성물질 조건, 멀티스케일 결합은 브릿지·결합 도구의 일.

**가져오지 않는 것**: 검증되지 않은 사실 진술(§0의 표시 규칙), 구현 프레임워크·DB·GUI 스택 선택(대화 자신도 확정하지 않았다), 처음부터 완전한 GUI를 자동 생성하는 목표.

### 2.6 HOOMD_GUI

**가져오는 것(원칙으로)**: 시각적 모델링(코드 없이 모델과 조건을 구성), 투명한 코드 생성(GUI 설정이 실행 코드에 어떻게 반영되는지 보인다), **과학 코어의 분리**(물리 모델과 검증 로직을 GUI에서 떼어 CLI·Python·에이전트가 재사용), 재현성 우선, 실행 전 검증, 버전이 있는 프로젝트 문서(JSON), loopback 전용 Local Runner라는 안전한 기본.

**사실 확인(2026-10-29 README 기준)**: 현재 구현은 Pixi 환경 + 2D 입자 편집기(상자·경계·입자·속성, 브라우저 측 검사, JSON 입출력) + Local Runner. 코드 생성과 HOOMD 실행은 **미구현**. 권위 있는 검증을 Python 패키지(`hoomd_gui_core`)로 옮기는 것이 로드맵. 첫 플랫폼은 macOS ARM64. **라이선스 미정**. README의 About과 본문이 "GUI 구현 여부"에서 서로 다르다(About: 미구현, 본문: 편집기 동작).

**가져오지 않는 것**: 코드. 참고 사례로 등록하고(`docs/reference/hoomd_gui.md`), 재사용 여부는 라이선스가 정해진 뒤 §14-16에서 결정한다.

---

## 3. 설계 원칙: 메타 원칙 MP1–MP13

SMA P0–P16은 그대로 구속한다. 다음은 이 레포에만 추가되는 원칙이다.

| # | 원칙 | 왜 | 깨지면 |
|---|---|---|---|
| **MP1** | **Meta-Agent는 만들고 제안한다. 운전하지 않는다.** 장비·엔진 도구, 장비에 닿는 네트워크 경로를 갖지 않는다 (Tier 0). Scientific Research Loop는 돌리지 않는다. | P0. 만드는 자리가 장비에 닿으면 안전 경계가 둘이 된다. | 빌드 중의 실수가 하드웨어에 닿는다. |
| **MP2** | **빌드된 에이전트는 혼자 선다.** 번들은 Meta-Agent 없이 두 게이트를 통과하고 모의 질문을 처리한다. | P11. | Meta-Agent가 단일 실패점이 된다. |
| **MP3** | **템플릿이 구조의 기록이다.** 번들은 버전이 있는 템플릿 + 명세에서 나오고, 차이는 `build` 카드에 diff로 남는다. | 발전을 추적하려면 "무엇에서 무엇으로"가 파일에 있어야 한다. | 어떤 에이전트가 왜 다른지 아무도 모른다. |
| **MP4** | **안전 값은 생성되지 않는다.** `envelope/safety.json` 템플릿은 `null`이고, `author: human`이 아닌 안전 값은 게이트가 거부한다. | P0, SMA §8.3 규칙 2. | 모델이 쓴 한계가 장비로 간다. |
| **MP5** | **제안은 아무것도 착륙시키지 않는다.** 모델은 초안을 쓰고, 픽스처·재생(코드)과 소유 좌석, 필요하면 사람이 결정한다. 채택만으로는 "도움이 되었다"가 되지 않는다. | SMA §8.3 규칙 1·4, harness2의 경험 규칙. | 자기 안전을 자기가 고치는 시스템. |
| **MP6** | **사례는 재정렬하고 삭제하지 않는다.** 반증 조건과 건수를 갖고, 대체된 사례는 `superseded_by`로 남는다. | P16. | 처음 몇 번 통한 구성만 반복한다. |
| **MP7** | **증류된 지식은 출처로 등급이 정해질 때까지 후보다.** 모델 출력(E6)은 "모델"로 표시되어 노트에 남고 항목이 되지 않는다. 측정값·상관식 계산값·예측값·문헌값·추정값은 `value_kind`로 구분한다. | SMA §5.3, 대화 1 §4.3. | 그럴듯한 숫자가 권위가 된다. |
| **MP8** | **기능은 요청이 요구할 때 들어온다.** 벡터 DB, 엔진, UI, 어댑터는 "지금 앞의 요청에 필요한가"를 통과해야 한다. | P10. | 다시 범용 엔진. |
| **MP9** | **주장은 네 가지 중 하나다: observed / derived / inferred / unknown.** 도구 이해와 사례의 원인(observed / suspected / confirmed)에 같은 규율을 적용한다. 부분 증거에서 "없음"을 결론내지 않는다. | REA. SMA의 "침묵에서 불가능을 유도하지 않는다". | 추론이 사양이 되어 장비로 간다. |
| **MP10** | **fail-closed 통합.** 범위·권한·부작용·검증 질문이 하나라도 미해결인 기능은 번들에 들어가지 않고 `held`로 남는다. 사람이 풀어야 열린다. | REA의 통합 규칙, SMA 브릿지의 `undeclared → held`. | 권한 없는 분석이나 부작용 있는 호출이 조용히 들어간다. |
| **MP11** | **발견은 추천이고 확정은 사람의 것이다.** 코드·문서에서 추론한 설정(`inferred`)은 근거와 함께 추천으로 제시된다. 운영 정책, 실행 권한, 공개 범위, 협업 방식은 추론으로 채우지 않는다. 정보 충분성 판단은 권한을 승인하지 않는다. | 대화 2. 코드가 Python이라고 연구실이 Python만 쓰는 것이 아니고, 공개 저장소를 쓴다고 에이전트와 데이터를 공개해도 되는 것이 아니다. | 추론이 정책이 되어 비공개 코드가 밖으로 나간다. |
| **MP12** | **연구실의 기존 도구를 존중한다.** Meta-Agent는 엔진이나 언어를 강요하지 않는다. 레지스트리는 목록이지 순위가 아니고, 추천은 Lab Profile과 방법론에서 나오며 근거를 적는다. | 대화 2. 같은 Brownian dynamics라도 연구실마다 HOOMD-blue, LAMMPS, 자체 코드를 쓴다. | 연구실이 쓰지 않는 엔진의 에이전트가 생겨 아무도 쓰지 않는다. |
| **MP13** | **GUI는 과학 판단의 원천이 아니다.** GUI는 검증 가능한 과학 모델과 실행 시스템을 사람이 제어하는 인터페이스다. GUI의 입력 검증은 과학 코어와 엔진의 검증을 대체하지 않고, GUI는 capability specification에서 유도되며, GUI만 아는 임계값은 없다. | HOOMD_GUI의 과학 코어 분리, 대화 2. | GUI의 검사가 통과했다고 잘못된 조건이 실행으로 간다. |

---

## 4. 시스템 개요

```
 사람 ──(자료: 깃허브·문서·PDF·링크·기존 카드; 언제든 inbox/materials/)──▶ S0 Onboarding (설치 마법사)
            │  Step 0 발견 → discovery_report (inferred, 근거 포함)
            │  Step 1 적응형 질문 (unknown과 정책만) → onboarding_record
            │  Step 2 구성 제안 → lab_profile + agent_goal 초안 + 검증 계획 개요
            │  Step 3 승인 (사람) ──▶ S1 Intake ──▶ agent_goal
                                                      │
       S2 Tool Understanding ◀────────────────────────┤  매뉴얼·API·스크립트·소스 (일반 도구)
            │  tool_profile: observed/derived/inferred/unknown + 증거 + 한계 + 권한 기록
            │                                          │  바이너리·패키지·런타임 (REA, 권한 확인 시)
       S3 Recall / Scan ◀──────────────────────────────┤  cases → case_refs/gaps · knowledge → knowledge_brief
                                                      ▼
       S4 Specify ──▶ agent_spec (A1–A6) ◀── parameter_sheet (F2) · lab_profile · method_registry
                                                      ▼
       S5 Build ──▶ build 카드 + builds/<agent>/<build_id>/ (번들 = 하네스 표면 + 도구 + 검증 과제 + (선택) GUI)
                                                      ▼
       S6 Validate ──▶ validation_report: ① interface gate  ② scientific gate   (둘 다 통과해야 완성)
                                                      ▼
       S7 Hand over ──▶ 사람이 번들을 목적지로 옮긴다 (Meta-Agent는 밖에 쓰지 않는다)
                                                      ▼
   ┌── System Improvement Loop ────────────────────────────────────────────────────────────────┐
   │  Observe(읽기 전용) → incidents → 분류 → knowledge-based(항목·사례 갱신) | structural(제안) │
   │  → 증명(픽스처 + 재생 + 대조) → 게이트 → 소유 좌석 착륙 → 측정 → library에 교훈           │
   └────────────────────────────────────────────────────────────────────────────────────────────┘

   새 엔진·장비·코드·자료가 들어오면 ──▶ S0의 Step 0만 그 항목에 대해 다시 돌고 v<N>_lab_profile
```

- S0는 연구실마다 처음 한 번 전부 돌고, 그 뒤에는 새 자료가 올 때 발견 단계만 다시 돈다.
- S1–S6은 한 요청 폴더 `requests/<rid>/` 안에서 평평하게 끝난다. 개선이 재설계를 요구하면 같은 `rid`의 새 개정 `v<N>_`으로 S4부터 다시 돈다(제안서 §2.3).
- System Improvement Loop는 요청과 무관하게 돈다(일일 회고 또는 사람의 지시).
- 모든 화살표는 카드다.

---

## 5. 기능별 명세

### 5.0 F0a 온보딩과 적응형 설치 마법사 (Agent Setup Wizard)

**무엇인가.** Meta-Agent의 첫 진입점. 일반 설치 마법사와 다른 점은 **먼저 연구실의 자료와 환경을 분석하고, 이미 파악한 것은 묻지 않는다**는 것이다(대화 2). Designer의 첫 단계 Research Environment Discovery & Agent Onboarding이기도 하다.

**네 단계.**

| 단계 | 하는 일 | 산출 |
|---|---|---|
| Step 0 Environment Discovery | 사람이 준 깃허브 저장소, 문서, 매뉴얼, PDF, 링크, 기존 에이전트 카드(SMA의 `contracts/`, 좌석, `failures.jsonl`), 연구실 설정을 읽는다. 소스가 있는 것은 일반 도구로, 바이너리는 권한이 있을 때 REA로 (§5.1 S2와 같은 규율) | `discovery_report`: 필드마다 `{value, state: inferred, evidence[]}` 또는 `unknown` |
| Step 1 Adaptive Questionnaire | 그 시점에 `unknown`인 필드와 **정책 필드**만 묻는다. 앞선 답과 발견된 자료에 따라 순서와 개수가 바뀐다. 한 번에 가장 중요한 하나 또는 소수 | `onboarding_record`: 질문, 답, 건너뛴 질문과 그 이유 |
| Step 2 Configuration Proposal | 연구 환경 요약, 레지스트리에서 고른 엔진·장비 추천(근거 포함), 에이전트 설계 개요, GUI 선택지, 검증 계획 개요, `held[]` | `lab_profile` 초안, `agent_goal` 초안 |
| Step 3 Approval & Generation | 사람이 확정한 것만 `confirmed`가 된다. 승인된 구성으로 S1 이후가 돈다 | `lab_profile` (확정본), `agent_goal` |

**세 상태 어휘** (설정 값마다):

| 상태 | 뜻 | 조건 |
|---|---|---|
| `confirmed` | 사람이 직접 확인했거나 명시적으로 제공 | `confirmed_by: human`, 날짜 |
| `inferred` | 코드·문서에서 추론 | `evidence[]` 필수 (`source_ref` + `locus`), 추천으로만 제시 |
| `unknown` | 근거가 없거나 결정되지 않음 | 질문 대상, 또는 보류한 채 진행 |

`inferred → confirmed`는 사람만 한다. **정책 필드**(작업 방식, 승인 방식, 공개 범위, 실행 권한, 협업 방식, 비공개 코드의 외부 전송)는 빌드 전에 `confirmed`여야 하고, 아니면 `held`다(MP10·MP11). 이 어휘는 `tool_profile`의 주장 종류(MP9)와 같은 규율이다: `inferred`는 추론이고 `confirmed`는 사람의 관찰이다.

**질문 은행** (고정 순서가 아니다; 조건에 따라 생략한다):

| 묶음 | 질문 | 생략·추론 조건 |
|---|---|---|
| 0 자료 | 분석할 깃허브·문서·매뉴얼·기존 에이전트 카드가 있습니까? **선호하는 시뮬레이션 엔진이나 실험 플랫폼의 PDF·링크가 있습니까?** (지금 없어도 언제든 `inbox/materials/LINKS.md`에 한 줄로 넣을 수 있다; 대화에서 답으로 준 링크도 Meta-Agent가 같은 자리에 옮겨 적는다) | 항상 묻는다. 이미 연결된 자료는 재활용 |
| 1 연구실 | 연구실의 첫 에이전트입니까? | 기존 에이전트 카드·저장소가 발견되면 `inferred: no`로 추천 |
| 2 협업 | 기존 에이전트와 협업하게 구성합니까? (→ 브릿지 계획 여부) | 첫 에이전트면 건너뛰거나 뒤로. 기존 에이전트가 발견되면 중요해진다 |
| 3 연구 종류 | 시뮬레이션 / 실험 / 분석 중 무엇을 합니까? **복수 선택** | 자료에서 추론 가능하면 추천 |
| 4 방법론 | 시뮬레이션이면 어떤 방법론입니까? DFT · MD · BD/CG · mesoscale · CFD · FEM · 기타, **복수 선택** (DFT + MD, BD + CFD, 장비 + 시뮬레이션처럼) | 기존 코드·입력 파일에서 추론 가능 |
| 5 도구 선호 | 선호 엔진, 선호 언어, 운영 환경(OS, HPC, GPU, 패키지 관리자) | 저장소에서 추론 가능. "저장소의 개발 환경 = 지금의 실행 환경"은 아니므로 추천으로만 |
| 6 기존 자산 | 쓰고 있는 코드·모델·데이터·검증된 워크플로가 있습니까? 링크 | 깃허브·파일·문서 분석 |
| 7 GUI | GUI가 필요합니까? 없음 / 파라미터 폼 / 도메인 시각 편집기 / 기존 연구실 GUI 재사용 | 연구 종류와 방법론에서 추천 |
| 8 운영 정책 | 작업 방식, 승인 방식, 공개 범위, 실행 권한 | **생략 불가. 추론으로 채우지 않는다** |

**정보 충분성 검사.** 각 단계에서 지금 가진 정보가 설계에 충분한지 본다. 충분하면 다음으로, 부족하면 가장 중요한 질문 하나 또는 소수를 낸다. 부족해도 진행할 수 있으면 보류한 설정을 `held[]`에 적고 초기 구성안을 만든다. 단, 비공개 코드의 외부 전송, 저장소 수정, 실제 장비 제어 같은 권한은 **충분성 판단으로 승인되지 않는다**(MP11).

**이 연구실에 적용하면** (예시; 실제 값은 Step 0가 기록으로 낸다): SMA 저장소가 있으므로 "첫 에이전트"는 `inferred: no`, 엔진 `HOOMD-blue`와 언어 `Python`은 `inferred`, 장비 하나(현미경)와 브릿지의 존재도 `inferred`. 공개 범위, 승인 방식, 추가 방법론, 선호 엔진·플랫폼 자료는 `unknown`이라 묻는다. 그래서 §14-18·19가 이 문서에 있다.

**자료 투입구 (materials inbox).** 설계 원칙은 하나다: **사람은 위치만 주고, 나머지는 Meta-Agent가 채우고, 사람은 확정한다.** 마법사와 같은 규율이다(먼저 분석하고 나중에 묻는다; MP11).

*사람이 하는 일* (둘 중 하나, 설치 전·중·후 언제든):

| 방법 | 하는 일 | 예 |
|---|---|---|
| 링크 | `meta_agent/inbox/materials/LINKS.md`의 표에 한 줄 추가. URL 칸만 필수, 나머지는 비워도 된다 | 아래 LINKS.md 형식 |
| 파일 | `meta_agent/inbox/materials/drop/`에 PDF·문서·압축 파일을 둔다. 이름을 바꿀 필요 없다 | `drop/TA_DHR_API_guide.pdf` |

```
LINKS.md (영어, 표 하나; url 칸만 필수, card 칸은 Meta-Agent가 채운다)

| url | name (optional) | role (optional) | note (optional) | card (filled by Meta-Agent) |
|---|---|---|---|---|
| https://hoomd-blue.readthedocs.io/ | HOOMD-blue | engine | lab uses v4 | |
```

*들어오는 길*은 다섯이지만 모두 같은 `material` 카드가 된다: (a) `LINKS.md`의 줄, (b) `drop/`의 파일, (c) 마법사 질문 0의 답(사람이 대화에서 준 링크를 Meta-Agent가 `LINKS.md`에 옮겨 적는다), (d) M2 이후 `add-material <url|path> [--about <name>]` 명령, (e) M9(선택) GUI의 Project 탭 "Add material". 브릿지를 거쳐 오는 자료는 `inbox/<thread>/`의 observation으로 오고, 사람이 승인하면 (a)나 (b)로 옮긴다(다른 에이전트가 직접 투입하지 않는다).

*Meta-Agent가 하는 일* (접수; `meta-…` 좌석; 읽기 전용):

1. 새 줄·새 파일을 발견하면 `inbox/materials/<YYYYMMDD>-<slug>/`를 만들고, 파일은 그 안으로 옮기며, `MATERIAL.json`을 쓴다. `LINKS.md`의 그 줄에는 카드 id를 적어 준다.
2. `kind`, `about`(이름·역할·방법), `license_note`는 내용에서 **`inferred`로 채우고 근거를 적는다**. 못 채우면 `unknown`으로 두고 질문 목록에 올린다(한 자료에 질문은 하나 또는 소수).
3. URL은 접근해 `retrieved_at`과 `content_hash`를 적는다. 자격 증명이 필요하거나 로그인 벽 뒤면 접근하지 않고 `held`(사유 `permission_required`). 원문 사본은 `may_quote: true`이거나 라이선스가 허락할 때만 `knowledge/sources/raw/`에 두고, 아니면 해시와 위치(`locus`)만 남긴다.
4. 사람에게 한 번 보여 준다: 채운 값과 질문. 사람이 확정하면 `registered`.

*그 다음* (F1·S0·S2): F1이 `registered`인 자료를 `knowledge/sources/`의 출처 기록과 증류 노트로 만들고 `distilled`로 바꾼다. 자료가 새 엔진·장비에 관한 것이면 S0의 Step 0이 **그 항목에 대해서만** 다시 돌아 `discovery_report`에 차이를 적고 `v<N>_lab_profile`과 레지스트리 갱신을 **제안**한다(확정은 사람). 도구의 동작에 관한 자료면 S2가 `tool_profile`의 개정을 제안한다. 진행 중인 요청(`requests/<rid>/`)이 그 도구를 쓰고 있으면 `superseded` 알림만 남기고 자동으로 바꾸지 않는다. 받아들이지 않을 자료(중복, 범위 밖, 라이선스 불가)는 `declined`과 사유로 남긴다. 자료가 없는 동안에도 설계와 빌드는 멈추지 않는다: 그 도구의 `tool_profile`에 `unknown`과 `requires`가 남을 뿐이다.

`MATERIAL.json`의 필드(스키마가 기록이다):

```
id
kind:            manual | paper | spec_sheet | api_doc | repo | dataset | link | unknown
about:           {name, role: engine | instrument | platform | analysis_software | unknown, methods[]}
                 필드마다 {value, state: confirmed | inferred | unknown, evidence[]}
location:        {url} 또는 {path}                       (정확히 하나; 사람이 쓴 유일한 필드)
source_snapshot: {retrieved_at, content_hash, archived: path | null}   (url이면 필수)
added_by, added_at, entry_path: links_md | drop | wizard | cli | gui
license_note:    {value, state, evidence[]}             (확정은 사람)
may_quote:       true | false | unknown                 (사람만 쓴다)
state:           queued | registered | distilled | declined | held
state_reason, questions[]
```

사람이 직접 쓰는 것은 `location`뿐이다(원하면 `about.name`도). 나머지는 Meta-Agent가 쓰고 사람이 확정하며, `may_quote`와 `license_note`의 확정은 사람만 한다(§9).

**산출물의 자리.** `meta_agent/profiles/<lab_id>/{discovery_report, onboarding_record, v<N>_lab_profile}.json`. 요청이 시작되면 `requests/<rid>/agent_goal.json`이 `lab_profile_ref`를 가진다.

### 5.1 F0 Agent Designer

**S1 Intake → `agent_goal`.** S0의 초안을 사람의 한 문단과 함께 모델이 다듬어 쓴다. 모델은 **수치를 만들지 않는다**. 필드: `purpose`, `science_task`, `tool`(이름, 종류 `instrument | engine | analysis_software | none`, 자료의 위치), `methods[]`(레지스트리 id), `executes`, `must_not[]`, `knowledge_needs[]`, `parameter_scope[]`, `destination`, `priorities[]`, `lab_profile_ref`, `gui_choice`, `analysis_permission`(아래). 사람에게 묻는 것은 사람만 답할 수 있는 것에 한해 한 번.

**S2 Tool Understanding → `tool_profile`.** 도구가 무엇을 할 수 있고 무엇이 제한인지를 **증거와 함께** 적는다.

- 입력과 방법:

| 자료 | 방법 | 비고 |
|---|---|---|
| 매뉴얼, 제조사 사양, 논문, `inbox/materials/`의 자료 | 읽기 → 출처 기록 → 증류 노트 (F1과 같은 규율) | 사양은 `vendor_spec`, 그 장비의 실측이 아니다 |
| API·SDK 문서, 설정 파일, 기존 스크립트, 소스 저장소 | 일반 저장소 도구(읽기, 검색, 정적 분석). **REA를 쓰지 않는다** | REA 자신의 경계: 소스가 있으면 일반 도구 |
| 바이너리, 패키지, 런타임 동작 | **REA**(MCP). 결과의 Evidence·limitations·unknowns를 그대로 싣는다 | **권한 확인이 먼저다** |
| 실행 기록(있으면) | `runs/`, 로그, 결과 파일의 형식 분석 | |

- **권한.** 바이너리·런타임 분석은 사람이 확인한 사용·분석 권한 안에서만 한다(제안서 §2.3). `tool_profile.analysis_permission = {granted_by: human, scope, basis(라이선스 조항 또는 docs/ideas 커밋), date}`가 없는 바이너리 분석 주장은 게이트가 거부한다(체크 11). 권한이 없으면 `inaccessible` 공백으로 적고 **문서화된 인터페이스만으로** 설계한다. 런타임 캡처는 장비가 연결되지 않은 복제 환경에서만 하고, 장비 컴퓨터에서는 하지 않는다(P0).
- **주장의 형식.** `claims[]`의 각 항목: `{claim, kind: observed | derived | inferred | unknown, evidence: [{source_ref | rea_evidence_id, locus}], limitations, requires(미지일 때: 어떤 권한·환경·측정이 있어야 풀리는가)}`. 추론을 관찰로 적지 않는다(MP9). 부분 증거에서 "지원하지 않음"을 결론내지 않는다.
- **능력 식별**(대화 1 §3.2): 제공 기능, 실제 실행 가능한 명령, 입출력 형식, 필수 파라미터와 단위, 유효 범위, 하드웨어·수치 제약, 관측·계산 가능한 물리량, 검증되지 않은 기능과 공백. 각각이 `claims[]`의 항목이다.
- **레지스트리와의 관계.** 레지스트리(§5.6)는 "어떤 도구가 있고 어떤 방법을 지원하는가"의 큐레이션 목록이고, `tool_profile`은 **이 요청의 이 도구**에 대한 증거 기반 프로필이다. `tool_profile`이 레지스트리와 다르면 레지스트리 갱신 제안이 된다.
- **산출**: `tool_profile.json` + `.md`, 그리고 F2로 넘길 파라미터 후보 목록.

**S3 Recall / Scan.** `cases`에서 `science_task`, `tool`, `methods`, 파라미터 이름으로 결정론적 매칭 → `case_refs` / `case_gaps`. `knowledge`에서 `knowledge_brief`. `v2_agent_goal.json`에 붙는다.

**S4 Specify → `agent_spec`, 여섯 축.** 각 축은 `spec_a<N>.json`으로 병렬 작성 가능.

| 축 | 내용 | 수치의 출처 |
|---|---|---|
| A1 Boundary | 디렉터리, 쓰는/읽는/금지 경로, 좌석 이름, Tier | 없음 |
| A2 Interface | 읽고 쓰는 카드, inbox/outbox, **callable tools의 목록과 각 도구의 입출력·에러 계약**(§5.1 S5), (선택) GUI가 제어하는 필드 | `tool_profile` |
| A3 Knowledge | 봉투에 복사할 항목(`kb_version` 핀), 남은 공백 | `knowledge_brief` |
| A4 Parameters | `parameter_sheet` 중 이 에이전트가 다루는 행 | `parameter_sheet` |
| A5 Safety | 안전 관련 행과 **빈 값**, 결정론적 규칙의 자리(어느 코드가 어느 값을 읽어 멈추는가), 사람만 하는 행위 | 사람 (`null`) |
| A6 Validation | **인터페이스 검증 과제**(호출·응답·오류·설정 전달)와 **과학 검증 과제**(기준 결과가 있는 과제), 완료·거부 조건 | A3/A4의 refs; 기준 결과는 항목 또는 출처를 가진다 |

`synthesis.json`이 축 사이의 충돌을 적고, 양보 방향은 `agent_goal.priorities`와 `lab_profile`의 관행이 정한다. **fail-closed**(MP10): 범위·권한·부작용·검증이 미해결인 기능은 `held[]`에 들어가고 번들에는 들어가지 않는다.

**S5 Build → `build` 카드 + 번들.** Designer의 산출물이 번들의 어디에 가는지:

| 산출물 | 번들 안의 자리 |
|---|---|
| capability specification | `CAPABILITIES.json` (`tool_profile`에서 `observed`·`derived`만 옮긴 것; `inferred`는 `unverified[]`로, `unknown`은 `gaps[]`로) |
| scientific model & parameters | `envelope/snapshot.json`의 항목과 `parameters.json`(시트의 행, 안전 행은 `null`) |
| callable tools (tool adapter) | `tools/<name>/` (어댑터 코드 + `tool.json` 계약 + 에러 계약), 소스가 GPL 등일 때는 호출만 하고 포함하지 않는다(§14-10) |
| steering instructions & skills | `CLAUDE.md`(역할·절차·하지 않는 것), `skills/<name>/SKILL.md`(상황별 절차) |
| validation tasks | `validation/interface/*.json`, `validation/scientific/*.json`(+ 기준 결과의 출처), `replay/`(회귀 스위트) |
| deployment configuration | `.claude/settings.json`(deny는 A1에서 유도, Bash/PowerShell 쌍둥이, PostToolUse 검증 훅), `envelope/`(safety `null`, snapshot), `tasks/001-start.md`, `failures.jsonl` |
| (선택) GUI specification & components | `gui/gui_spec.json` + 공통 구성요소의 조합 + (필요할 때만) 도구 특화 구성요소 (§5.7) |

**하네스 표면**(harness2의 여덟 구성요소를 번들에 대응). 제안이 편집할 수 있는 것은 이 표면뿐이다. GUI는 표면이 아니라 **표면이 노출하는 인터페이스**이고, 제안이 GUI를 바꾸려면 `gui_spec`을 거친다.

| 구성요소 | 번들 경로 | 컨텍스트 비용 |
|---|---|---|
| system prompt | `CLAUDE.md`의 역할·절차 | 상시 |
| guardrails | `CLAUDE.md`의 "하지 않는 것" + `.claude/settings.json`의 deny | 상시 / 도구 루프 |
| memory | `envelope/snapshot.json`, `case_refs` | 상시(스냅샷) |
| tool guidance | `tools/*/tool.json`의 설명, `CLAUDE.md`의 도구 절 | 상시 |
| skills | `skills/<name>/SKILL.md` (+ `scripts/`) | 호출 시 |
| subagents | `.claude/agents/<name>.md` | 자기 컨텍스트 |
| scripts | `src/` 결정론적 도우미 | 호출 시 |
| plugins / hooks | `.claude/settings.json`의 hooks | 도구 루프 안, 건너뛸 수 없음 |

편집 계약: **생략은 상속**(제안은 바꾸는 것만 낸다). 유효성 검사(체크 B-계열)를 통과 못 한 제안은 **통째로** 폐기한다. 폐기 규칙 세 가지: 스킬은 `CLAUDE.md`에 트리거 문장이 있어야 하고, 이름 붙은 스크립트는 존재해야 하며, 명령 deny는 두 셸 모두를 이름 붙여야 한다. 비용 순서: **skill > script > subagent > hook > 상시 산문**. 상시 산문을 더하면 다른 것을 빼서 값을 치른다(SMA의 산문 예산).

`build` 카드: `spec_ref`, `lab_profile_ref`, `template_version`, `diff_from_template`, `bundle_sha256`, `held[]`, `gate_verdict`, `lineage`, `landed_at`(사람).

**S6 Validate → `validation_report`.** 두 게이트, 둘 다 통과해야 완성이다.

| 게이트 | 무엇을 | 어디서 | 판정 |
|---|---|---|---|
| **Interface validity** | 도구 호출과 응답의 정확성, 입출력 일관성, 오류 처리와 복구(에러 계약 준수), 설정값·명령 전달의 정확성, (GUI가 있으면) GUI 필드 → 도구 파라미터 전달의 정확성 | 모의 백엔드 또는 샌드박스(소프트웨어 도구는 작업 폴더 밖 격리 환경, 하드웨어는 모의만) | 과제별 `pass | fail | not_run`, 결정론적 |
| **Scientific validity** | 물리량·단위 정합성, 파라미터와 적용 조건의 타당성, 모델 가정, **기준 결과와의 일치**(해석해, 문헌값, 기준 데이터), 결과 해석의 재현성 | 같은 환경에서 `validation/scientific/` 과제 실행 | 기준 결과는 항목 또는 출처를 가진 수치; 일치 기준(허용 오차)은 **사람이 고른 임계값**, 없으면 UNDECIDED |

`not_run`은 통과가 아니다. 하드웨어가 있어야만 돌 수 있는 과제는 `not_run: requires bench`로 남고, 번들은 "모의에서 유효"로만 인계된다. GUI의 브라우저 측 검사는 어느 게이트도 대신하지 않는다(MP13).

**S7 Hand over.** Meta-Agent는 `meta_agent/builds/` 밖에 쓰지 않는다. 사람이 번들을 목적지로 옮기고 `landed_at`을 적는다. 실행 엔진(장비 운전 코드)은 번들의 **스켈레톤**(결정론적 게이트의 자리, 안전 값 `null`)까지가 Designer의 일이고, 실제 운전 코드는 목적지의 소유 좌석이 사람과 함께 만든다(MP1). 소프트웨어 도구(RheoTool)의 어댑터는 Designer가 만들고 샌드박스에서 검증한다.

### 5.2 F1 Knowledge Engine (`meta_agent/knowledge/`)

v0.1의 세 층(출처 / 증류 노트 / 항목)을 유지한다. 바뀌는 것:

- **입력의 범위**: 논문, 기술 문서, API 문서, 매뉴얼, 실행 기록, `inbox/materials/`의 큐(`registered` 상태). S2의 `tool_profile`과 S0의 `discovery_report`도 입력이다.
- **`value_kind`**: 모든 수치에 `measured | correlation | computed | predicted | literature | estimated | model_generated` 중 하나. 등급은 (`source` 종류, `value_kind`)에서 **유도**된다. DB 유래 값과 예측 구조의 유도 규칙은 §14-12.
- **충돌**: 기존 항목과 다른 값은 `conflict`로 기록하고 둘 다 남긴다(SMA 사서의 `kb_conflicts`). 근거가 부족하면 `gap(unqualified_source)`.
- **문헌 평가**: 후보 생성 → 비판 → 정련(제안서 §2.3이 인용한 방식)을 **증류 노트 안에서** 한다. 정련된 주장만 항목이 되고, 비판 기록은 노트에 남는다.
- **출처 어댑터 공유**: §5.3의 어댑터는 `knowledge/sources/`에 출처 기록을 쓴다. 지식과 파라미터는 같은 출처 층을 쓴다.
- **연결 모드**: 사서가 권위, 여기 항목은 `kb_candidate`.

### 5.3 F2 Parameter Intelligence (`parameter_sheet`)

v0.1의 행 형식을 유지하고 다음을 더한다.

**세 단계**(대화 1 §5): **Discovery**(논문·매뉴얼·실행 기록·DB에서 파라미터와 그 값이 쓰인 모델·장비·환경·가정·단위·유효 범위를 함께 식별) → **Reasoning**(파라미터 사이의 상관과 제약, 스케일링, 무차원수, 수치 안정성 조건, 장비 사양을 결정론적 도우미로 검사) → **Recommendation**(값 또는 범위 + 근거 + 불확실성; 근거가 없으면 값 대신 **필요한 추가 측정·보정을 제안**).

**계층형 검색**(기본 순서이지 신뢰 순위가 아니다):

1. 검증된 실험 데이터 (측정 DB, 공개 데이터셋, 내부 실측)
2. 큐레이션된 모델과 오픈소스 파라미터 (상관식 라이브러리, 포텐셜·역장 저장소)
3. 문헌 검색 (본문과 보충 자료)
4. 증거 검증과 비교 (단위, 조건, 불확실성, 유효 범위, 출처 일치)
5. → `parameter_sheet`의 행, 또는 `gap`

**출처 어댑터 후보**(`meta_agent/src/sources/`). 아래는 대화에서 온 후보이고 **전부 "확인 필요"다**. 확인 항목: 존재, 접근 방식(API / 다운로드 / 라이브러리), 수록 범위와 갱신 시점, 라이선스·이용 약관, 반환값의 `value_kind`.

| 영역 | 후보 | 기대 역할 |
|---|---|---|
| 유체·열역학 물성 | NIST ThermoML (확인 필요: REST는 메타데이터, 수치는 아카이브 파일에서; 공개 아카이브의 수록 시점), NIST Chemistry WebBook, `chemicals` / `thermo` (Python), CoolProp | 점도·밀도·계면장력·열물성. 상관식 결과는 `correlation`으로 표시 |
| 화학종 식별 | PubChem | CAS·식별자·분자 정보 |
| 시뮬레이션 파라미터 | NIST Interatomic Potentials Repository, OpenFF Toolkit, 각 엔진의 공식 모델 | 포텐셜·역장 파라미터, 출처와 버전 |
| 특수·레올로지 데이터 | Zenodo, NIST 개별 데이터셋(광레올로지·열경화 레올로지 등), 논문 보충 자료 | 비뉴턴 응답은 물질명만으로 정해지지 않는다: η = η(T, c, γ̇, M_w, 이력, …). 조건을 행에 함께 적는다 |
| 보조 라이브러리 | `thermoml-io` (확인 필요: 비공식, 신생) | ThermoML 아카이브 검색·파싱 |

첫 비교 시험(M3): 같은 물질·같은 조건에 대해 둘 이상의 어댑터가 돌려주는 값을 나란히 놓고, 어느 것이 측정이고 어느 것이 상관식인지가 행에 남는지를 본다.

**단백질 특화 영역**(요청이 올 때 어댑터를 만든다, MP8; 카드 형식은 지금 정한다).

- `protein` 항목: 식별자(UniProt / PDB / design id), 기원(`natural | de_novo | engineered`), 구성(서열, 길이, 분자량), 구조(2차, 좌표, 조립), 물성(pI, 안정성, 응집 성향), 기능(표적, 친화도, 활성), 검증 상태(`experimental | computational | unverified`), 근거(DOI, 데이터셋 버전, 조건). `parameter_sheet`의 행이 `protein_ref`로 연결된다.
- **구성과 조건의 분리**: 단백질 자체의 구성·구조 정보와, **실험 조건에 의존하는 측정값**(올리고머화 상태, 결합 부위, 가교 가능성, 농도·온도·용액 조건에서의 물성)은 다른 자리에 저장한다. 후자는 조건 태그가 붙은 `parameter_sheet` 행이다. 연성물질(단백질 네트워크)에서는 후자가 설계를 좌우한다(대화 2).
- 규칙 세 가지: **예측 구조와 실험 구조는 다른 `value_kind`다**(`predicted` vs `measured`). **존재·구조의 확인과 기능·물성의 확인은 별개로 기록한다.** **설계 도구(RFdiffusion, ProteinMPNN 등)는 데이터베이스가 아니고**, 단백질 설계 자체는 요청이 올 때까지 범위 밖이다.
- **검색 경로**(대화 2): 질의(서열 / 이름 / 원하는 구조·기능·물성) → 자연 단백질은 UniProt · InterPro, 설계 단백질은 PDA · Proteinbase, 3차원 구조는 RCSB PDB · ModelArchive, 실험 물성은 ProtaBank · 논문 → **교차 검증**(서열 동일성, 구조의 출처, 실험 조건) → `protein` 항목 + `parameter_sheet` 행.
- 출처 후보(확인 필요): UniProt, InterPro(자연 단백질), Protein Design Archive(PDA; 데이터와 처리 코드가 깃허브에 공개되어 있다고 함; 독립 공개 API의 범위는 별도 확인), Proteinbase(설계 단백질과 실험 결과; Hugging Face 데이터셋으로 읽을 수 있다고 함), RCSB PDB(REST / GraphQL), ModelArchive(연구자 제출 계산 모델), AlphaFold DB(예측 구조; 임의의 설계 서열은 없을 수 있음), ProtaBank(변이·안정성 측정값).

**하드웨어의 경우**는 v0.1과 같다: `vendor_spec`은 그 장비의 실측이 아니고, `bench_confirmed: false`가 기본이다.

### 5.4 F4 Experience Memory (`meta_agent/cases/`)

**수집**(대화 1 §6.1): 연구 목표, 실행 당시의 도구·시스템 상태, 사용한 지식과 파라미터(refs), 계획과 실제 조건, 결과, 실패·예외, 연구자의 개입, 시도한 해결, 해결 뒤의 결과. 출처는 `observed.json`의 읽기 전용 경로(§5.5)나 `observation` 카드다.

**한 사례 한 파일**, v0.1의 필드에 다음을 더한다:

```
cue:          이 교훈이 적용되는 상황의 모양 (이 과제의 사실이 아니라 패턴)
lesson:       적용하고 검사할 수 있게 적은 조작, 관련 구성요소를 이름 붙여서
evidence:     기대는 실행·커밋·카드와 그 대조
confidence:   high | medium | low, 그리고 왜
cause_status: observed | suspected | confirmed     (confirmed는 run 또는 commit 증거 필요)
```

너무 일반적이면 쓸모없고("철저히 하라"), 너무 구체적이면 다시 불이 붙지 않는다(harness2). `cue`는 그 사이에 쓴다.

**검색**: 결정론적, 입력 카드의 `signature`(과제·도구·방법론·관측량·파라미터·원인 클래스·조건 태그)와의 교집합, 같은 입력에 같은 출력, 정렬은 등급 → 건수 → id. 텍스트 유사도는 §14-7.

**승격**(Knowledge Promotion): `cause_status: confirmed`이고 `count.supports ≥ N`(N은 사람의 것, 그 전엔 UNDECIDED)인 사례는 (a) `kb_candidate`로 지식 항목 후보가 되거나 (b) `harness_proposal`(kind `reshape`)로 스킬이 된다. 원 사례의 적용 범위와 한계가 따라간다.

**씨앗**: SMA의 `failures.jsonl`·`incidents.jsonl`은 이전 항목이고 판정(`transfer | downgrade | drop`)과 출처 커밋을 남긴다. 사람의 허락이 먼저다(§14-6).

### 5.5 F3 Meta-Harness (`meta_agent/harness/`)

SMA §8.3의 루프(관찰 → 분류 → 제안 → 증명 → 게이트 → 도달 → 측정 → 은퇴)와 규칙 1–7을 채택한다. 더하는 것:

**관찰 대상**: 이 레포 자신(`failures.jsonl`, verdict, 거부, `--no-verify`), 빌드된 에이전트(`envelope/observed.json`의 읽기 전용 경로 + 읽은 커밋 해시; 닿지 않으면 `degraded`), 세션 사이의 사건(`incidents.jsonl`), 온보딩 기록(불필요했던 질문, 틀린 추론).

**두 경로의 자리**: knowledge-based 개선은 항목·사례를 바꾸는 일이라 F1·F4의 카드로 끝난다. structural 개선만 `harness_proposal`이 된다. 한 사건이 두 경로 모두를 낳을 수 있고, 어느 쪽이었는지는 평가(§11)가 가른다.

**두 수준의 재귀**(harness2를 우리 규칙으로 옮긴 것):

| 수준 | 무엇 | 우리 방식 |
|---|---|---|
| 빌드 수준 | 한 요청 안에서 후보 번들 k개를 **같은 검증 과제**로 probe하고, 실행의 대조에서 compose | k는 사람이 준 예산(기본 1). probe는 모의 재생 + 결정론적 두 게이트. compose는 모델이 초안을 쓴다. 채택은 게이트 + 소유 좌석. **기준(편집 없는 번들)을 먼저 판정하고, 기준이 실패하면 "판정 없음"** |
| 하네스 수준 | 채택된 하네스와 교훈을 도메인별 라이브러리에 쌓고, 같은 도메인의 다음 빌드가 먼저 읽는다 | `harness/library/<domain>/<build_id>/{diff, EXPERIENCE.md}`. 도메인 = 레지스트리의 방법·도구 종류(`rheometer`, `cfd_solver`, `md_engine`, `microscope`, …). 실행 설정(모델, 실행기, k, 시드)별로 분리 |

**제안 카드의 추가 필드**: `edit_rows[]` = `{component, change, observed(어느 실행 어디서 갈라졌나), verdict: helped | hurt | no_observed_effect | confounded}`. 한 후보가 여러 구성요소를 동시에 바꿨거나 롤아웃이 하나뿐이면 `confounded`를 **우선** 쓴다. `confounded`만 딛고 선 교훈은 라이브러리에 들어가지 않는다(`NO_ENTRY`).

**증명**: 조이기는 (a) 사건을 재현하는 픽스처(바꾸기 전 실패, 후 통과), (b) 이력 재생(새 FAIL 없음). 지시문·스킬 변경은 (c) `replay/`와 `validation/`의 재생에서 판정 유지. 변경은 **대조적 증거**(같은 과제, 편집 전후의 실행)를 `edit_rows`로 남긴다.

**예산 장부**: `ledger.jsonl`의 각 줄에 롤아웃 수, 개선 세션 수, 토큰(입력·출력), 벽시계 시간, 비용(공급자가 말하는 대로, 아니면 공개 가격으로 계산하고 "계산됨"으로 표시). 같은 설정끼리만 비교한다.

**되돌림**: 개정은 추가 전용이므로 "되돌림"은 이전 개정을 다시 채택하는 새 개정이다. 성능 저하가 기록되면 `ledger`에 `reverted_by`로 남는다.

**핵심(제안만, 착륙 불가)**: MP1, MP4, MP10, MP11, 등급 유도와 E6 배제, 사람의 좌석 배정, 게이트의 존재, SMA §8.3 규칙 1–5, 빌드된 에이전트의 `envelope/`·`approvals/`, `lab_profile`의 정책 필드, 안전 정책과 실행 권한의 변경(일반 개선과 별도 관리).

**외부 엔진**: harness2를 엔진으로 쓰는 일은 §14-8. 쓴다면 SMA §8.3의 2026-10-19 시험 설계로만, 장비 없는 컴퓨터에서, 작업 폴더 밖에서, 산출물은 제안.

### 5.6 Simulation Method Registry와 Lab Profile

**세 층의 분리.** 시뮬레이션을 DFT → MD → BD → CFD의 사다리로만 보지 않는다. 스케일은 겹치고, 같은 물리 모델을 여러 소프트웨어가 구현하며, 한 엔진이 여러 방법을 지원한다(대화 2).

```
Physical Scale  ──▶  Modeling Method  ──▶  Simulation Engine      (방법 ↔ 엔진은 다대다)
electronic / atomistic / coarse-grained / mesoscale / continuum
```

**레지스트리** (`contracts/registry/{methods,engines,instruments}.json`): 목록이지 순위가 아니다(MP12). 각 항목은 `{id, name, scale[], methods[](엔진), interface: python_api | input_file_cli | gui | sdk, language, license(확인 필요 표시 가능), material_refs[], verified: {by, date, evidence}}`. 대화에서 온 **대표 예**(배타적 분류가 아니고, 라이선스·버전은 M2의 확인 뒤 등재):

| 방법론 | 대표 도구 (확인 필요) | 설정·GUI에서 중요한 것 |
|---|---|---|
| Electronic structure / DFT | Quantum ESPRESSO, CP2K, VASP | 원자 구조, 전자 상태, basis, k-points |
| Molecular dynamics | GROMACS, LAMMPS, OpenMM | 원자·분자, force field, topology |
| Brownian / coarse-grained dynamics | HOOMD-blue, LAMMPS, 자체 코드 | 입자, 포텐셜, 확산, 마찰, 경계 조건 |
| Mesoscale / multiphase | LAMMPS, OpenFOAM, 전용 LBM/DPD 코드 | 상 구성, 입자–유체 상호작용, 계면 |
| CFD | OpenFOAM(+ RheoTool), SU2 | geometry, mesh, 경계 조건, solver |
| Structural / FEM | FEniCSx, deal.II, Abaqus, COMSOL | mesh, 구성 모델, 하중, 구속 |
| (장비) | 현미경, 레오미터, … | 제어 인터페이스, 측정 조건, 보정, 안전 한계의 자리 |

예컨대 HOOMD-blue는 MD와 BD 모두, CP2K는 DFT와 MD 모두, FEniCSx는 구조해석을 넘어 일반 PDE를 다룬다. 그래서 방법과 엔진은 다대다다.

**Lab Profile** (`meta_agent/profiles/<lab_id>/v<N>_lab_profile.json`). 에이전트 생성에 쓰는 **환경과 제약 정보**이지, 연구실을 중앙에서 관리하는 것이 아니다. 필드마다 세 상태(§5.0)와 근거.

| 묶음 | 필드 | 예 |
|---|---|---|
| 도구 | `preferred_engines[]`, `preferred_instruments[]` (레지스트리 id) | HOOMD-blue; 현미경 |
| 하드웨어 | `hardware` | CPU, GPU, HPC 클러스터, 장비 컴퓨터의 격리 |
| 소프트웨어 환경 | `software_env` | Python, C++, MPI, conda / pixi, OS |
| 기존 자산 | `existing_code[]`, `existing_data[]`, `validated_workflows[]` | 저장소 링크, 입력 파일 |
| 과학적 관행 | `conventions` | 단위계, force field, 검증 기준, 명명 |
| GUI 선호 | `gui_preference` | none / parameter_form / visual_editor / reuse_existing |
| 운영 제약 | `operational_constraints` | 라이선스, 권한, 지원 OS, 네트워크 |
| 협업 | `collaboration` | first_agent, existing_agents[], bridge |
| **정책** | `policy` | 작업 방식, 승인 방식, 공개 범위, 실행 권한, 비공개 코드의 외부 전송 — **`confirmed` 필수** |

`agent_spec`의 A1·A2·A5와 `synthesis`가 Lab Profile을 읽는다. 추천 엔진은 `lab_profile.preferred_engines`가 있으면 그것이고, 없을 때만 레지스트리에서 방법론으로 후보를 내되 근거를 적는다.

### 5.7 GUI (선택 기능)

**원칙**: MP13. HOOMD_GUI에서 가져온 세 가지, 시각적 모델링 · 투명한 코드 생성 · 과학 코어의 분리.

**구조**(대화 2): 모든 시뮬레이션을 한 GUI로 다루면 과하고, 소프트웨어마다 새로 만들면 유지가 안 된다. 그래서 세 층.

| 층 | 내용 | 공통화 |
|---|---|---|
| 공통 틀 | Project(자료 투입 "Add material" 포함; §5.0의 길 (e)) · Parameters · Validation · Execution · Results, 카드 입출력 | **공통** (작업 흐름과 카드 인터페이스) |
| 도메인 편집기 | Particle editor (MD·BD) / Mesh editor (CFD·FEM) / Structure editor (DFT·분자) / Instrument panel (장비) | 도메인별. 물리 모델을 하나의 범용 스키마로 억지로 합치지 않는다 (MD의 입자와 CFD의 mesh는 다른 도메인 모델) |
| 도구별 과학 코어·어댑터 | 검증, 코드 생성, 실행 인터페이스, 결과 처리 | 도구별. GUI 밖에 있고 CLI·에이전트도 같은 것을 쓴다 |

**선택지**(마법사 질문 7): GUI 없이 CLI와 에이전트만 / 기본 파라미터 폼 / 도메인별 시각 편집기 / 기존 연구실 GUI 재사용. 반드시 GUI가 필요한 것은 아니다.

**유도 규칙**: `gui_spec`은 `CAPABILITIES.json`과 `tools/*/tool.json`에서 유도된다. GUI의 모든 입력 필드는 도구 파라미터나 capability 항목에 매핑되고(체크 B10), GUI 파일 안에 GUI만 아는 수치 임계값은 없다(값은 `envelope/`와 과학 코어에서 읽는다). GUI의 입력 검증은 과학 코어의 검증기를 **호출**하는 것이지 자기 규칙을 갖지 않는다. 새 엔진이 들어오면 화면을 처음부터 그리지 않고 공통 구성요소를 재사용하고 특수한 기능만 따로 정의한다.

**시작 방식**: 처음부터 완전한 GUI 자동 생성은 범위가 크다. **검증된 공통 UI 구성요소의 조합**으로 시작하고, 특수한 시각화가 필요할 때만 새 구성요소를 만든다. 참고 사례는 HOOMD_GUI(입자 기반). DFT·CFD·FEM 도구를 조사한 뒤에 공통화할 요소를 판단한다. 구체적인 GUI 아키텍처와 기술 스택은 지금 정하지 않는다(§14-16).

---

## 6. 카드

### 6.1 종류

| 카드 | 쓰는 이 | 무엇 | 대화 1의 범주 |
|---|---|---|---|
| `material` | 사람(위치) + 접수 좌석(메타데이터, `inferred`) | 투입된 매뉴얼·논문·링크 한 건, 출처 스냅샷, 상태 | |
| `discovery_report` | 온보딩 좌석 | Step 0의 발견: 필드마다 `inferred` + 근거, 또는 `unknown` | |
| `onboarding_record` | 온보딩 좌석 (+ 사람의 답) | 물은 것, 답, 건너뛴 것과 이유 | |
| `lab_profile` | 온보딩 좌석 (+ 사람의 `confirmed`) | §5.6의 표, 필드마다 상태와 근거 | |
| `agent_goal` | 사람 → 실행 좌석 | 왜·무엇을 하는 에이전트가 필요한가. 수치 없음 | |
| `tool_profile` | 실행 좌석 | 도구의 능력과 한계, 주장마다 종류·증거·한계, 권한 기록 | Agent Card의 전반부 |
| `knowledge_brief` + `kb_entry` | 실행 좌석 | 요청에 들어간 항목과 공백 / 한 주장 한 파일 | Knowledge Card |
| `parameter_sheet` (+ `protein`) | 실행 좌석 | §5.3의 표 | Parameter Card |
| `agent_spec` (+ `spec_a1..a6`, `synthesis`) | 실행 좌석 | 여섯 축과 종합, `held[]` | Agent Card |
| `gui_spec` (선택) | 실행 좌석 | 화면과 입력 필드, 각 필드의 capability·tool 매핑 | |
| `build` | 실행 좌석 (+ 사람의 `landed_at`) | 번들과 게이트 판정, 계보 | Agent Card의 배포 구성 |
| `validation_report` | 실행 좌석 | 인터페이스·과학 두 절의 과제별 판정 | Execution Card |
| `case` | 실행 / 하네스 좌석 | §5.4 | Experience Card |
| `harness_proposal` | 하네스 좌석 | 한 구조 변경과 증명, `edit_rows[]` | Improvement Card |
| `refusal` | 누구나 | 왜 할 수 없는가 + 반례 | |
| `kb_candidate` | 실행 좌석 | 사서에게 넘기는 항목 후보 | |
| `observation` | 사람 또는 브릿지 (inbox) | 빌드된 에이전트에서 온 실행·실패·성공 보고 | Execution Card |

### 6.2 공통 필드 (SMA `common.schema.json`과 호환)

`card`, `schema_version`, `id`, `rid`(SMA의 `qid` 자리; 연결 시 `thread`도), `revision`, `author`, `created_at`, `numbers[]`(4-튜플 + `value_kind`), `assumptions[]`, `kb_refs[]` / `kb_gaps[]`, `case_refs[]` / `case_gaps[]`, `degraded[]`, `status`.

### 6.3 수치와 주장의 규칙

- 수치는 `{name, value, unit, source, grade, value_kind}`. 등급은 유도되고 자가 신고되지 않는다. E6은 카드에 들어가지 않는다.
- 주장은 `observed | derived | inferred | unknown` (MP9). 설정 값은 `confirmed | inferred | unknown` (§5.0).
- MD 안의 모든 수는 같은 폴더의 JSON에 있어야 한다. 유효숫자는 입력 중 최악을 따른다 (P15).

### 6.4 에러 계약 (생성된 callable tool이 반환하는 것)

`{code, category, message, retryable, remediation: {action}, evidence?}`. `category`는 REA의 어휘에서 시작한다: `invalid_input | unsupported_target | integrity_mismatch | truncated | cancelled | timeout | resource_constraint | unavailable | execution_failure`, 여기에 `refused_by_safety`(결정론적 게이트의 거부)와 `permission_required`를 더한다. 체크 B7이 픽스처 호출로 확인한다.

### 6.5 상태기계

`draft → validated → (approved) → done | refused | held | superseded`. `held`는 MP10의 상태이고 사람이 푼다. 기록은 추가 전용, 수정은 새 개정 `v<N>_`. `material`은 따로 `queued → registered → distilled | declined | held`(`registered`는 사람의 확정, `held`는 접근 권한이나 라이선스가 막을 때; §5.0).

---

## 7. 저장소 레이아웃

```
meta-agent/
  PLAN.ko.md                  이 문서 (승인 후 docs/origin/으로 동결)
  plan.md                     설계 기록 (영어; M0에서 생성)
  CLAUDE.md / README.md / LICENSE / pyproject.toml / .claude/settings.json / .gitattributes / .gitignore

  contracts/                  ★ 유일한 공유 코드
    schemas/                  material, discovery_report, onboarding_record, lab_profile, agent_goal, tool_profile,
                              knowledge_brief, kb_entry, kb_candidate, parameter_sheet, protein, agent_spec, spec_axis,
                              synthesis, gui_spec, build, validation_report, case,
                              harness_{incident, proposal, ledger_entry, retro, experience}, refusal, observation,
                              tool_contract, error_contract, common
    registry/                 methods.json, engines.json, instruments.json  (목록, 순위 아님; verified 필드)
    units.json                단위 레지스트리 (SMA 형식)
    case_classes.json         원인 클래스 어휘
    claim_kinds.json          observed / derived / inferred / unknown, cause_status, 설정 상태 confirmed / inferred / unknown
    seats.json                커밋 정체성 → 경계
    validate.py               결정론적 검증기 (§8); --bundle 로 번들 게이트
    examples/ + examples/rejected/
    hooks/                    pre-commit
    tools/seat_commit.py      (§14-9)

  meta_agent/                 ★ 에이전트 하나. contracts/와 함께 옮길 수 있는 단위
    CLAUDE.md / README.md / .claude/settings.json   (Tier 0, builds/ 밖 쓰기 금지, 두 셸 쌍둥이)
    tasks/ · failures.jsonl · envelope/observed.json
    inbox/<thread>/           브릿지·사람의 observation
    inbox/materials/README.md            "A link on one line is enough" (영어; 투입 방법과 그 뒤 절차)
    inbox/materials/LINKS.md             사람이 링크를 한 줄씩 적는 표  (언제든 추가)
    inbox/materials/drop/                사람이 파일을 두는 곳  (언제든 추가; 접수 뒤 아래 폴더로 이동)
    inbox/materials/<YYYYMMDD>-<slug>/   접수된 자료 + MATERIAL.json  (Meta-Agent가 만든다)
    profiles/<lab_id>/        discovery_report, onboarding_record, v<N>_lab_profile
    requests/<rid>/           agent_goal, tool_profile, knowledge_brief, parameter_sheet, spec_a1..a6, synthesis,
                              agent_spec, gui_spec, build, validation_report, refusal, failures.jsonl  (평평하게, v<N>_ 개정)
    knowledge/{sources, distilled, entries, index.json}   sources/raw/는 may_quote: true인 사본만
    cases/<case_id>.json + index.json
    harness/{incidents.jsonl, proposals/, ledger.jsonl, retro/, library/<domain>/<build_id>/}
    templates/agent@<hash>/   번들 템플릿 (하네스 표면 + tools/ + validation/ + envelope/ 스켈레톤 + gui/ 공통 구성요소)
    builds/<agent>/<build_id>/  번들 + build 카드 + validation_report
    eval/                     네 조건 비교의 과제 묶음, 설정, 결과 (§11)
    src/                      onboarding/, materials/(투입구 접수), intake/, tooling/(tool understanding), knowledge/, sources/(어댑터), parameters/,
                              spec/, build/, gui/, validate/, cases/, harness/   (의존은 한 방향, 형제 import 금지)
    tests/

  docs/ideas/<YYYYMMDD>.md · docs/origin/PLAN.ko.md · docs/reference/<name>.md (참고 사례: hoomd_gui 등)
```

---

## 8. 검증 계층 (`contracts/validate.py`)

번호는 고정이고 은퇴해도 재사용하지 않는다.

| # | 검사 | 종류 |
|---|---|---|
| 1 | `card`/`artifact`가 있는 모든 JSON이 자기 스키마를 통과 (파일명을 믿지 않음) | 스키마 |
| 2 | 수치가 4-튜플 + `value_kind`, 등급이 유도값과 일치, E6 없음 | 수치 |
| 3 | MD의 모든 수가 같은 폴더의 카드에 존재 | 수치 |
| 4 | 안전 관련 값은 `null`이거나 `author: human` | 안전 |
| 5 | `kb_refs`/`case_refs`가 핀된 인덱스에서 해석; `*_gaps.searched`가 비어 있지 않음 | 참조 |
| 6 | 커밋 경로가 커미터 좌석의 경계 안 | 경계 |
| 7 | 추가 전용, 개정은 `v<N>_` | 이력 |
| 8 | `case`에 `falsification`, `count`, `cue`, `cause_status`; `confirmed`는 run/commit 증거; `cause_class` 등록됨 | 사례 |
| 9 | `harness_proposal.kind` 넷 중 하나; loosen/retire/핵심은 사람의 말 + `docs/ideas/` 커밋; tighten은 픽스처 | 하네스 |
| 10 | `ledger` 줄이 존재하는 제안과 커밋을 가리킴; 비용 필드 존재 | 하네스 |
| 11 | `tool_profile.claims[].kind` 넷 중 하나, 증거 ref 존재; `unknown`은 `requires` 필수; 바이너리/런타임 유래 주장에 `analysis_permission` 없으면 FAIL | 도구 이해 |
| 12 | `validation_report`에 interface와 scientific 두 절, 과제별 `pass|fail|not_run`; scientific의 기준 결과는 항목 또는 출처; 허용 오차 없으면 UNDECIDED; `not_run`은 통과 아님 | 검증 |
| 13 | `edit_rows[].verdict` 넷 중 하나; `confounded`만 딛는 `experience`는 library 거부(`NO_ENTRY`) | 하네스 |
| 14 | `held[]`의 항목이 번들에 없음; `held` 해제는 사람의 말 + 커밋 | fail-closed |
| 15 | `lab_profile`의 모든 필드에 `state`; `inferred`는 `evidence[]` 비어 있지 않음; `confirmed`는 `confirmed_by: human`; `policy.*`·`collaboration.mode`·실행 권한 필드는 빌드 참조 시 `confirmed` 아니면 FAIL; `inferred → confirmed` 전이에 사람 외 작성자 있으면 FAIL | 온보딩 |
| 16 | `onboarding_record.questions[]`의 각 질문이 그 시점 `unknown`인 필드 또는 정책 필드를 가리킴 (이미 `confirmed`인 필드를 물으면 FAIL); `skipped[]`에 이유(`inferred` 근거 또는 조건) | 온보딩 |
| 17 | `material`: `location`에 `url`과 `path` 중 정확히 하나; `about.*`·`license_note`가 세 상태 어휘를 따르고 `inferred`는 `evidence[]` 비어 있지 않음; `added_by: human`이고 메타데이터 작성자는 접수 좌석; `url` 자료가 `distilled`인데 `source_snapshot.retrieved_at`·`content_hash` 없으면 FAIL; `may_quote`가 `true`가 아닌데 `archived`가 있으면 FAIL; `held`·`declined`에 `state_reason` 필수 | 자료 투입 |
| B1 | 번들 필수 파일 (§5.1 S5 표) | 빌드 |
| B2 | 모든 `Bash(...)` deny/ask에 `PowerShell(...)` 쌍둥이, 그 역도 | 빌드 |
| B3 | `envelope/safety.json` 값 전부 `null` | 빌드 |
| B4 | `snapshot.json` 항목 해시가 `knowledge/`와 일치, `kb_version` 핀 | 빌드 |
| B5 | `replay/`와 `validation/{interface,scientific}/`에 과제 하나 이상, 기대 판정 있음 | 빌드 |
| B6 | 번들 `CLAUDE.md`의 모든 수가 `snapshot.json`에 존재 | 빌드 |
| B7 | 모든 `tools/<name>/tool.json`이 `tool_contract` 스키마를 통과하고, 픽스처 호출에서 에러 계약을 지킴 | 빌드 |
| B8 | 모든 스킬에 `CLAUDE.md`의 트리거 문장; 이름 붙은 스크립트 존재; `CAPABILITIES.json`에 `inferred` 주장 없음 | 빌드 |
| B9 | 안전 관련 도구 호출 경로에 결정론적 게이트의 자리가 있음(A5) | 빌드 |
| B10 | `gui/`가 있으면: `gui_spec`의 모든 입력 필드가 `tools/*/tool.json` 파라미터 또는 `CAPABILITIES.json` 항목에 매핑; `gui/` 안에 수치 임계값 없음(모든 수가 `envelope/` 또는 `parameters.json`에 존재); GUI 검증 훅이 과학 코어 검증기를 호출 | 빌드 |

규칙(SMA에서 인용): 체크와 픽스처는 같은 커밋, 새 픽스처는 실패하는 것을 먼저 본다, `--expect-fail`의 두 총계 전부 거부, UNDECIDED와 PENDING은 통과가 아니다, 모든 수는 실행에서 읽고 verdict 줄은 판정한 트리를 함께 찍는다.

---

## 9. 권한 모델

**좌석**: `design-…`(루트 파일, `contracts/`, `docs/`, `meta_agent/CLAUDE.md`, `meta_agent/.claude/`), `meta-…`(`meta_agent/` 나머지; 온보딩도 이 좌석), M5부터 `harness-…`(`meta_agent/harness/`). 사람이 세션마다 직접 배정한다. 이름은 `<role>-<machine>-<YYYYMMDD>-<n>`.

**사람만 하는 일**: 안전 값, 좌석 배정, 번들 인계(`landed_at`), 풀기·은퇴·핵심 변경의 허락, 임계값(허용 오차, k, N), 이전 항목의 판정, **분석 권한의 확인**(`analysis_permission`), `held`의 해제, 하드웨어 위에서의 검증 과제 실행, **온보딩 정책 질문의 답과 `inferred → confirmed` 전이**, 공개 범위, 자료 투입(위치를 주는 일)과 접수된 메타데이터의 확정, 인용 허락(`may_quote`)과 라이선스 판단.

**하나의 작업 사본, 워크트리 없음**(SMA의 결정). 경로를 이름 붙여 커밋한다.

**격리**: 소프트웨어 도구의 어댑터 검증은 작업 폴더 밖의 격리 환경(컨테이너 또는 WSL의 별도 디렉터리)에서, 네트워크는 필요한 호스트만. 장비 컴퓨터에서는 모의만. GUI의 Local Runner가 있으면 loopback 전용(HOOMD_GUI의 기본). 자료 투입구의 URL 접근은 읽기 전용이고 저장된 자격 증명이나 로그인 세션을 쓰지 않는다(필요하면 `held`).

---

## 10. 테스트베드, 참고 사례, 브릿지

| 테스트베드 | 대상 | 목적 | 비고 |
|---|---|---|---|
| **A** 기존 에이전트 | SMA 현미경 에이전트, HOOMD 시뮬레이션 에이전트 | 두 개선 경로의 효과 비교(§11). Designer는 **개정**만 제안. 온보딩 Step 0의 첫 실제 입력(SMA 저장소) | 관찰은 읽기 전용 경로 또는 브릿지. 변경은 SMA 소유 좌석이 착륙 |
| **B** 레오미터 | TA Instruments 레오미터 (하드웨어) | 새 장비 인터페이스에 대한 에이전트 생성: 제어 인터페이스, 측정 조건, 보정, 단위, 작동 한계, 검증 절차 | 제어 소프트웨어의 분석 권한은 S2에서 사람이 확인. 안전 값은 사람. 실행 엔진은 소유 좌석이 사람과 함께 |
| **C** RheoTool | RheoTool (C++, OpenFOAM 기반, GPL-3.0) | 비파이썬·설정 파일·명령줄·결과 파싱 인터페이스에 같은 절차가 통하는가 | 소스가 있으므로 일반 도구로 분석. 과학 검증 과제는 **해석해가 있는 흐름**(예: 뉴턴 유체의 평면 Couette 흐름, 점탄성 모델의 정상 전단 점도 함수)부터 |
| 교차 검증 | 레오미터 ↔ RheoTool(모델·단위), 현미경·HOOMD ↔ 레오미터(미시 동역학 ↔ 거시 레올로지) | 도구 간 비교 | 브릿지의 일. Meta-Agent는 카드 형식의 호환만 책임진다 |
| 멀티스케일 결합 (장기) | 서로 다른 스케일의 시뮬레이션 연결 | 인터페이스와 변환 조건(단위, 스케일, 경계 데이터)의 명시 | **Meta-Agent가 엔진을 통합하지 않는다.** 브릿지나 별도 결합 도구가 맡고, Meta-Agent는 변환 조건을 카드로 적는 데까지 |

**참고 사례**: HOOMD_GUI를 입자 기반 시뮬레이션 GUI의 참고 사례로 `docs/reference/hoomd_gui.md`에 등록한다(§2.6의 사실 확인과 함께). 코드 재사용은 라이선스가 정해진 뒤.

**첫 실제 에이전트의 권고**: **C → B** 순서. C는 하드웨어가 없어 P0 노출이 없고, 비파이썬 인터페이스라 일반화를 시험하며, 과학 검증에 해석해를 쓸 수 있다. B는 C의 결과(인터페이스 계약, 검증 과제 형식)를 재사용한다. 두 경우 모두 S0가 먼저 돌고, 이 연구실의 `lab_profile`이 생긴다.

**브릿지 연결 준비**(v0.1 §10과 같다): `meta_agent/` + `contracts/`가 옮길 수 있는 단위, 공통 필드 호환, `inbox/<thread>/` 예약, 연결 시 사서가 지식의 권위, `contracts/`가 둘이 될 때의 결정은 §14-3. 마법사의 협업 질문이 "예"면 브릿지 계획이 `agent_spec.A2`에 들어간다.

---

## 11. 평가

**원칙**: 두 루프를 따로 잰다. 기준선을 먼저 판정한다. 판정과 보고는 같은 과제 묶음·실행기·모델·k·시드로 한다. 실패한 평가는 0점이 아니라 "미채점"으로 남긴다. 표본 수와 합격 기준은 **기준선을 모은 뒤** 사람이 정한다(제안서 §2.4).

**네 조건**: C0 개선 없음 / C1 구조만 / C2 지식만 / C3 둘 다. `eval/<set>/<condition>/`에 설정과 결과. 지식을 끄는 것은 번들을 `degraded: [knowledge, cases]`로 빌드하는 것이고, 구조를 끄는 것은 템플릿 그대로의 번들이다.

| 묶음 | 지표 | 어디서 읽나 |
|---|---|---|
| 에이전트 개발 | 작업 시간, 연구자의 수동 설정·개입 횟수, **마법사의 질문 수와 불필요했던 질문 수**, 자료 투입 1건당 사람이 직접 쓴 필드 수(목표 1: 위치), 검증을 통과한 기능의 범위, 새 인터페이스 적응(C 대 기존), **첫 과학적 유효 실행까지의 시간** | `profiles/`의 `onboarding_record`, `inbox/materials/*/MATERIAL.json`의 `added_by`·`entry_path`, `requests/<rid>/`의 타임스탬프, `docs/ideas/`의 개입 기록, `validation_report` |
| 과학적 성능 | 물리량·단위 정확성, 파라미터 추천의 타당성, 재현성, 기준 결과와의 일치, 실패 탐지·회복 | `validation_report`, `case` |
| 자기 개선 | 네 조건 사이의 차이, 재발률(사건 클래스가 다시 나오는가), 되돌림 횟수 | `incidents.jsonl`, `ledger.jsonl`, `eval/` |
| 운영 효율 | 사람의 개입 시간, 오류 복구율, 지연, 토큰·비용, 개선에 따른 성능 저하 발생률 | `ledger.jsonl`, 실행 로그 |

수동 구성 대 Designer 보조 구성의 비교는 **짝지은 과제**로 한다(같은 도구, 같은 목표).

---

## 12. 마일스톤과 완료 조건

이름은 일의 덩어리이지 순서가 아니다. M0만 나머지 전부를 막는다.

| M | 덩어리 | 완료 조건 (실행에서 읽는다) |
|---|---|---|
| **M0** | 계약: 스키마 전부, `validate.py` 체크 1·2·3·6·7·11·15·16·17, 예시 + 거부 픽스처, `seats.json`, 레지스트리 빈 틀, `inbox/materials/`(README, LINKS.md, drop/), 훅, `CLAUDE.md`, `plan.md` | `0 failed`; `--expect-fail` 두 총계 전부 거부; 첫 커밋부터 좌석 커미터 |
| **M1** | 온보딩 + Designer 골격: Step 0(자료 폴더와 저장소 읽기) → Step 1(`unknown`만 질문) → Step 2 → Step 3 → `agent_goal` → `tool_profile`(문서만으로) → `agent_spec` → 템플릿 v1 → **echo 번들** → 인터페이스 게이트 B1–B9 → `validation_report` | 자료가 가득한 픽스처 연구실에서는 **정책 질문만** 나오고, 빈 연구실에서는 전체 질문이 나온다(둘 다 `onboarding_record`에서 읽는다); echo 번들이 두 게이트(과학 게이트는 자명한 과제 하나)를 통과하고 Meta-Agent 없이 `replay/` 하나를 처리 |
| **M2** | Knowledge Engine: 출처/증류/항목, `value_kind`, 충돌, 인덱스, `knowledge_brief`, `inbox/materials/` 접수(메타데이터 추론, URL 스냅샷, 사람 확정)와 큐 처리, `add-material` 명령; **출처 어댑터 후보와 레지스트리 대표 항목의 확인**(존재·접근·범위·라이선스)과 첫 어댑터 하나 | 유도 등급을 통과한 항목과 `searched`가 있는 공백 각 하나 이상; 확인 결과가 `knowledge/sources/`와 `registry/*.json`의 `verified`로 존재 |
| **M3** | Parameter Intelligence: 세 단계, 계층형 검색, 도우미, 둘 이상 어댑터의 비교 시험, `protein` 카드 형식(구성과 조건의 분리 포함) | 안전 행이 빈 시트가 체크 4를 통과; 채운 시트가 거부 픽스처; 비교 시험의 행마다 `value_kind`가 남음 |
| **M4** | Experience Memory: 스키마(`cue`…), 어휘, `recall.py`, 주입, 승격 규칙, (허락 시) SMA 씨앗 이전 | 새 `agent_goal`에 `case_refs` 또는 `case_gaps`; 같은 입력 같은 출력 |
| **M5** | Meta-Harness: 사건/제안/장부/회고/라이브러리, `edit_rows`, `observed.json`, 재생, 래칫, **네 조건 평가 하네스(모의)** | 조이기 하나가 픽스처+재생으로 착륙; 풀기 하나가 사람의 말 없이 거부(픽스처); 네 조건이 echo 과제 묶음에서 돈다 |
| **M6** | **테스트베드 C**: RheoTool 에이전트 — 이 연구실의 S0, 소스 분석 `tool_profile`, 어댑터(설정 파일·명령·결과 파싱), 샌드박스 인터페이스 검증, 해석해 과학 검증, 인계 | `validation_report` 두 절 `pass`(하드웨어 과제 없음); 소유 좌석이 목적지에 착륙하고 `landed_at` 기록 |
| **M7** | **테스트베드 B**: 레오미터 에이전트 — 권한 확인, `tool_profile`(권한 범위 안), 어댑터와 실행 엔진 **스켈레톤**, 안전 값 `null`, 모의 검증 | 모의에서 두 절 `pass`, 벤치 과제는 `not_run: requires bench`; 안전 값은 사람이 목적지에서 채움 |
| **M8** | 브릿지·교차 검증: inbox 왕복 모의, 카드 호환, 테스트베드 A의 관찰 경로와 네 조건 비교 | `r1_ask_*`가 읽히고 `degraded`가 전파; A의 네 조건 결과가 `eval/`에 존재 |
| **M9** (선택) | GUI: 공통 틀 + `CAPABILITIES.json`에서 유도한 파라미터 폼을 `gui_preference`가 있는 첫 에이전트에; 도메인 편집기는 그 다음 | B10 통과; GUI에서 넣은 값이 같은 과학 코어 검증기를 거쳐 CLI와 같은 판정을 냄(재생으로 확인) |

---

## 13. 범위 밖 (non-goals)

- 장비 운전, 시뮬레이션 실행(모의·샌드박스 검증 제외), 콘솔 UI, 웹 서비스.
- 여러 Scientific Agent의 상시 중앙 조정(브릿지의 일). 연구실들의 중앙 관리(Lab Profile은 생성 입력일 뿐).
- 서로 다른 스케일의 엔진을 Meta-Agent가 직접 통합하는 일(멀티스케일 결합은 브릿지·결합 도구).
- 처음부터 완전한 GUI의 자동 생성. 엔진·언어의 강제.
- 사람의 승인 없이 실행 권한을 넓히는 기능. 모델 가중치 재학습.
- 자동 병합·자동 착륙. 범용 에이전트 프레임워크.
- 벡터 DB·임베딩·크롤러(조건은 §14-7). REA·harness2 엔진의 내장. 단백질 설계 도구의 내장.
- 외부 클라우드 서비스에 종속된 배포 구조.

---

## 14. 열린 질문 (사람의 결정)

1. **저장소 위치와 깃 초기화.** `D:\codes\github\meta-agent`로 추정.
2. **기록의 언어.** 영어 `plan.md`를 기록으로, 이 문서는 동결(권고).
3. **`contracts/`의 관계.** SMA의 `common.schema.json`·`units.json`을 커밋 해시 핀으로 복사하고 출처를 적음(권고). 연결 시 어느 쪽이 기록인가.
4. **첫 실제 에이전트.** 권고 **C RheoTool → B 레오미터**(§10). 동의하는가.
5. **런타임.** 빌드된 에이전트가 Claude Code 세션(D11)으로 도는지, SDK 프로세스도 대상인지. 권고: 스킬은 REA처럼 **이식 가능한 레이아웃**(`skills/<name>/SKILL.md` + 플러그인 매니페스트)으로 내고 런타임별 설치만 다르게.
6. **씨앗 이전.** SMA의 `failures.jsonl`·`incidents.jsonl`을 사례로 옮기는 것을 허락하는가.
7. **텍스트 유사도·벡터 검색의 도입 조건.** 권고: 결정론적 매칭이 `case_gaps`를 냈는데 사람이 손으로 관련 사례를 찾은 일이 N번 쌓이면.
8. **harness2.** 참고만 할지(권고, 지금), 엔진으로 시험할지(M5 이후, SMA의 시험 설계로, 장비 없는 컴퓨터).
9. **커밋 도구.** SMA `seat_commit.py`를 가져올 시점.
10. **라이선스.** 이 레포 MIT. 제3자: harness2 Apache-2.0(참고만), REA MIT(도구로 호출), RheoTool/OpenFOAM GPL-3.0(**번들에 포함하지 않고 호출만**; 재배포 조건은 법적 확인), HOOMD_GUI **미정**(정해질 때까지 참고만).
11. **외부 DB 접근 정책.** 허용 호스트, API 키의 보관, 로컬 아카이브(캐시) 위치, 각 DB의 이용 약관.
12. **DB 유래 값과 예측 구조의 등급 유도 규칙.** `value_kind`별로 어느 등급인가(측정 DB / 상관식 / 예측 구조 / 설계 기록).
13. **단백질 특화 영역의 시점.** 카드 형식은 M3, 어댑터는 요청이 올 때(권고).
14. **분석 권한의 확인 절차.** 누가(사람), 무엇으로(라이선스 조항·제조사 동의), 어디에(`docs/ideas/` 커밋 → `analysis_permission.basis`).
15. **임계값 목록(UNDECIDED).** 과학 검증의 허용 오차, 빌드 수준 재귀의 k, 승격 건수 N, 네 조건 비교의 표본 수. 전부 기준선 뒤에 사람이 고른다.
16. **GUI의 범위와 기술 스택.** M9를 할지, 할 때 HOOMD_GUI의 `web/` + `python/` 구조를 공통 틀의 출발점으로 쓸지(라이선스가 정해진 뒤), 파라미터 폼만으로 시작할지(권고).
17. **Lab Profile의 범위.** 이 연구실 하나만(권고, 지금) 또는 복수 연구실. 복수라면 `lab_id`의 부여와 프로필 사이의 공유 규칙.
18. **선호하는 시뮬레이션 엔진·실험 플랫폼의 자료 (자리; 질문이 아니다).** 매뉴얼·API 문서·논문·사양서의 PDF나 링크는 **지금 없어도 되고**, 생기면 언제든 넣는다. M0 전에는 이 대화에 링크나 파일을 주면 되고, M0 뒤에는 `meta_agent/inbox/materials/LINKS.md`에 한 줄 또는 `drop/`에 파일 하나면 된다(§5.0). 대상은 §0의 표에 있는 넷(HOOMD-blue, 현미경, TA 레오미터, RheoTool/OpenFOAM)과 그 밖에 연구실이 쓰거나 쓰려는 엔진(예: LAMMPS, GROMACS, OpenMM, OpenFOAM, FEniCSx)·장비. 들어오면 접수 → 확정 → 증류 → 그 항목에 대한 발견 재실행의 순서로 처리되고, 없는 동안 설계와 빌드는 멈추지 않는다. **2026-10-29 현재: 없음, 나중에 투입 예정.**
19. **이 연구실의 온보딩 답.** 마법사가 묻게 될 것 중 자료로 추론할 수 없는 것: 주로 할 연구 종류와 방법론(복수 선택), 선호 언어·환경, 에이전트와 결과의 공개 범위, 승인 방식(어느 행위에 사람의 승인이 필요한가), 기존 SMA 에이전트와의 협업 방식(브릿지). 지금 답해도 되고 M1의 마법사가 물을 때 답해도 된다.

---

## 15. 승인 후 첫 작업 (M0 체크리스트)

1. 저장소 위치 확정, `git init`, `.gitattributes`(LF), `.gitignore`, `LICENSE`.
2. `plan.md` 생성(영어, 기록). 이 문서는 `docs/origin/`으로.
3. `contracts/seats.json`에 `design-…`, `meta-…` 등록. 사람이 두 세션을 배정.
4. `contracts/schemas/` 전부(§7), `units.json`, `case_classes.json`, `claim_kinds.json`, `tool_contract` · `error_contract` 스키마, `registry/{methods,engines,instruments}.json`의 빈 틀(항목은 `verified` 없이 "확인 필요"로 시작).
5. `contracts/validate.py`: 체크 1·2·3·6·7·11·15·16·17 + `--expect-fail` + verdict 줄.
6. `contracts/examples/` 한 벌(`material`·`lab_profile`·`onboarding_record`·`tool_profile`·`validation_report` 포함)과 `rejected/` 픽스처(체크당 하나 이상; 15·16은 "정책 필드가 inferred인 프로필"과 "이미 확정된 필드를 묻는 기록", 17은 "url과 path를 둘 다 가진 자료"와 "may_quote 없이 사본을 가진 자료"). 실패하는 것을 본 사실을 커밋 메시지에.
7. `contracts/hooks/pre-commit`, `.claude/settings.json`(루트와 `meta_agent/`, 두 셸 쌍둥이, PostToolUse 검증 훅).
8. 루트 `CLAUDE.md`(짧게), `README.md`, `meta_agent/CLAUDE.md`, `meta_agent/README.md`, `meta_agent/inbox/materials/{README.md, LINKS.md, drop/.gitkeep}`(README는 "A link on one line is enough"로 시작하고 접수 뒤 절차를 적는다; LINKS.md는 머리글만 있는 빈 표), `meta_agent/tasks/001-onboard-this-lab-on-fixtures.md`, `tasks/002-echo-agent-on-mock.md`.
9. `docs/ideas/20261029.md`에 이 계획을 낳은 사람의 말(요구 다섯 가지, 참고 자료 네 건 + 대화 2 + HOOMD_GUI, "AWS 부분 제외", "선호 엔진·플랫폼 자료는 언제든 넣을 수 있게", "추후 사용자가 해당 링크를 넣을 수 있도록 디자인")을 원문으로. `docs/reference/hoomd_gui.md`에 §2.6의 사실 확인.
10. 첫 실행: `python contracts/validate.py` → `0 failed`; `--expect-fail` 두 총계 전부 거부. 수는 실행에서 읽어 보고.

---

## 부록 A. 용어 대조표

| 한국어 | 영어 식별자 | 비고 |
|---|---|---|
| 메타 에이전트 / 에이전트 디자이너 / 과학 에이전트 | Meta-Agent / Agent Designer / Scientific Agent | §1.1 |
| 온보딩, 설치 마법사 | onboarding, Agent Setup Wizard | §5.0 |
| 발견 보고 / 온보딩 기록 / 연구실 프로필 | `discovery_report` / `onboarding_record` / `lab_profile` | §5.0, §5.6 |
| 설정 상태 | `confirmed` / `inferred` / `unknown` | MP11 |
| 자료 (투입구) | `material`, `inbox/materials/` | §5.0 |
| 방법 레지스트리 | `contracts/registry/{methods,engines,instruments}.json` | §5.6 |
| 연구 루프 / 개선 루프 | Scientific Research Loop / System Improvement Loop | §1.2 |
| 지식 기반 개선 / 구조 개선 | knowledge-based / structural improvement | §1.3 |
| 도구 프로필 | `tool_profile` | 주장 + 증거 + 한계 + 권한 |
| 주장의 종류 | observed / derived / inferred / unknown | MP9 |
| 원인 상태 | observed / suspected / confirmed | §5.4 |
| 값의 종류 | `value_kind`: measured / correlation / computed / predicted / literature / estimated / model_generated | MP7 |
| 인터페이스 검증 / 과학 검증 | interface validity / scientific validity | §5.1 S6 |
| 하네스 표면 | harness surface (8 components) | §5.1 S5 |
| GUI 명세 | `gui_spec` | §5.7, MP13 |
| 보류 | `held` | MP10 |
| 에러 계약 | error contract | §6.4 |
| 편집 행 | `edit_rows`: helped / hurt / no_observed_effect / confounded | §5.5 |
| 교훈 | `cue / lesson / evidence / confidence` | §5.4 |
| 라이브러리 | `harness/library/<domain>/` | 하네스 수준 재귀 |
| 네 조건 | C0 / C1 / C2 / C3 | §11 |
| 카드, 요청, 명세, 번들, 증류, 항목, 공백, 사례, 사건, 제안, 장부, 회고, 래칫, 좌석, 봉투, 거부, 축소 모드, 등급 | card, request(`rid`), spec, bundle, distillation, entry, gap, case, incident, proposal, ledger, retro, ratchet, seat, envelope, refusal, degraded, grade | v0.1과 같다 |

## 부록 B. 카드 스케치 (형식 감각용; 스키마가 기록이다)

`lab_profile`의 일부 (세 상태):

```json
{"card": "lab_profile", "id": "lab-softmatter-01", "revision": 1, "author": "meta-office-20261029-1",
 "preferred_engines": {"value": ["hoomd-blue"], "state": "inferred",
   "evidence": [{"source_ref": "repo_soft-matter-agents@<sha>", "locus": "simulation_agent/"},
                {"source_ref": "repo_HOOMD_GUI@<sha>", "locus": "readme.md"}]},
 "software_env": {"value": {"language": ["python"], "package_manager": ["pixi"]}, "state": "inferred",
   "evidence": [{"source_ref": "repo_HOOMD_GUI@<sha>", "locus": "pixi.toml"}],
   "note": "the repository's development environment is not shown to be the current execution environment"},
 "collaboration": {"first_agent": {"value": false, "state": "inferred",
                     "evidence": [{"source_ref": "repo_soft-matter-agents@<sha>", "locus": "contracts/seats.json"}]},
                   "mode": {"value": null, "state": "unknown"}},
 "gui_preference": {"value": null, "state": "unknown"},
 "policy": {"publication_scope": {"value": null, "state": "unknown"},
            "approval_mode": {"value": null, "state": "unknown"},
            "external_transfer_of_private_code": {"value": false, "state": "confirmed", "confirmed_by": "human", "date": "2026-10-29"}},
 "held": ["collaboration.mode", "policy.publication_scope", "policy.approval_mode"],
 "numbers": [], "degraded": [], "status": "draft"}
```

`material` (사람이 `LINKS.md`에 쓴 것은 URL 한 줄; 아래는 접수 뒤, 사람 확정 전):

```json
{"card": "material", "id": "mat-20261030-001", "kind": "repo",
 "about": {"name":    {"value": "RheoTool", "state": "inferred", "evidence": [{"source_ref": "src_mat_20261030_001", "locus": "README.md:1"}]},
           "role":    {"value": "engine", "state": "inferred", "evidence": [{"source_ref": "src_mat_20261030_001", "locus": "README.md:3-8"}]},
           "methods": {"value": ["cfd", "viscoelastic_flow"], "state": "inferred", "evidence": [{"source_ref": "src_mat_20261030_001", "locus": "README.md:3-8"}]}},
 "location": {"url": "https://github.com/fppimenta/rheoTool"},
 "source_snapshot": {"retrieved_at": "2026-10-30T09:12:00Z", "content_hash": "sha256:<...>", "archived": null},
 "added_by": "human", "added_at": "2026-10-30", "entry_path": "links_md",
 "license_note": {"value": "GPL-3.0", "state": "inferred", "evidence": [{"source_ref": "src_mat_20261030_001", "locus": "LICENSE"}]},
 "may_quote": "unknown",
 "state": "queued", "state_reason": null,
 "questions": ["may_quote: may excerpts of the tutorial dictionaries be stored verbatim?"]}
```

`tool_profile`의 주장 세 개:

```json
{"card": "tool_profile", "id": "tp-20261029-001", "rid": "req-20261029-001", "revision": 1,
 "author": "meta-office-20261029-1",
 "tool": {"name": "RheoTool", "kind": "engine", "language": "C++", "license": "GPL-3.0", "source": "src_rheotool_repo_<sha>"},
 "analysis_permission": null,
 "claims": [
  {"claim": "steady shear is configured through a dictionary file read at solver start",
   "kind": "observed", "evidence": [{"source_ref": "src_rheotool_repo_<sha>", "locus": "tutorials/<path>/constant/constitutiveProperties"}],
   "limitations": "one tutorial read; other solvers not checked"},
  {"claim": "the solver accepts a time step smaller than the viscoelastic relaxation time",
   "kind": "inferred", "evidence": [{"source_ref": "src_rheotool_manual_<sha>", "locus": "§numerics"}],
   "limitations": "a stability bound is not stated as a number anywhere read"},
  {"claim": "the output field for the polymeric stress tensor is written every N steps",
   "kind": "unknown", "evidence": [], "requires": "a run in the sandbox with the tutorial case"}
 ],
 "numbers": [], "kb_refs": [], "kb_gaps": [], "case_refs": [], "case_gaps": [], "degraded": [], "status": "draft"}
```

`case`의 경험 필드:

```json
{"card": "case", "id": "case-20261029-002", "kind": "failure",
 "signature": {"science_task": "tracer diffusivity", "executes": "instrument", "instrument": "widefield microscope",
               "observables": ["tracer_diffusivity"], "parameter_names": ["tracer_emission_peak"], "condition_tags": ["vendor_spec_vs_bench"]},
 "what_happened": "vendor Ex/Em entered as E3 and served for an hour; the bench value differed",
 "cause_class": "correctly_graded_but_wrong_for_this_instance", "cause_status": "confirmed",
 "evidence": [{"kind": "commit", "ref": "soft-matter-agents@<sha> librarian_agent/failures.jsonl:4"}],
 "cue": "a value for a specific physical part comes from the vendor's characterisation and not from this bench",
 "lesson": "set bench_confirmed=false on the parameter row and have the skill that builds the plan refuse to treat it as E1",
 "confidence": "medium, one instance, cause confirmed by the person's measurement",
 "falsification": "vendor values for this part class match the bench within the stated tolerance in N consecutive cases",
 "count": {"supports": 1, "contradicts": 0, "last_seen": "2026-09-19"},
 "source_agent": "librarian_agent", "source_repo_commit": "<sha>", "grade": "E2", "superseded_by": null}
```

`harness_proposal`의 편집 행:

```json
{"card": "harness_proposal", "id": "HP-003", "kind": "tighten", "class": "guard-covers-one-route-of-two",
 "answers": ["INC-20261101-02"],
 "changes": [{"path": "builds/rheotool/0007/.claude/settings.json", "owner": "meta-office-20261029-1",
              "change": "add the PowerShell twin for each Bash deny line"}],
 "edit_rows": [{"component": "guardrails", "change": "PowerShell twins added",
                "observed": "replay/003: the shell route that bypassed the deny in build 0006 is refused in 0007 at step 4",
                "verdict": "helped"}],
 "proof": {"fixtures": [{"path": "contracts/examples/rejected/checkB2_bash_without_powershell_twin/", "watched_failing_before": "<sha>", "watched_passing_after": "<sha>"}],
           "replay": {"range": "<sha>..<sha>", "new_fail": 0}},
 "touches_core": [], "needs_threshold": false,
 "cost": {"rollouts": 2, "sessions": 1, "tokens_in": 0, "tokens_out": 0, "usd": 0.0, "usd_basis": "provider"}}
```

## 부록 C. 참고 자료의 핵심 문장 (요약, 인용이 아님)

- **제안서**: Meta-Agent는 다른 에이전트의 구성·운영·개선을 책임지고, Agent Designer Agent는 새 도구를 위한 에이전트를 설계·생성·검증하는 역할이다. 산출물은 capability specifications, callable tools, steering instructions, validation tasks, deployment configurations. 인터페이스 동작과 과학적 유효성은 따로 검사한다. 자기 개선은 네 조건으로 평가하고, 연구 루프와 시스템 개선 루프를 구분한다. 테스트베드는 TA Instruments 레오미터와 RheoTool.
- **REA**: 관찰·유도·추론·미지를 구분하고 증거 출처를 보존한다. 결과는 증거와 한계를 포함한다. 소스가 있는 저장소에는 쓰지 않는다. 통합은 fail-closed. 에러 계약은 category·retryable·remediation.
- **harness2**: 하네스는 모델 주위의 시스템이고, 하네싱은 그것의 최적화다. 여덟 구성요소, Propose–Probe–Compose, 두 수준의 재귀, 생략은 상속, 유효하지 않은 제안은 폐기, 상시 산문은 가장 비싸다, 교훈은 cue·lesson·evidence·confidence, 채택만으로 "도움"을 말하지 않는다, 기준선을 먼저 판정한다, 실행기의 네트워크는 제한되어야 한다.
- **대화 1**: Agent Designer / Knowledge Engine / Parameter Intelligence / Experience Memory / Meta-Harness의 구획, 평가 지표 네 묶음, 로드맵 Phase 0–5, 파라미터 DB와 단백질 DB의 후보 목록, 계층형 검색, 측정·계산·문헌·추정의 구분.
- **대화 2**: 설치 마법사는 먼저 분석하고 나중에 묻는다. 설정은 confirmed / inferred / unknown이고 추론은 추천일 뿐이며 정책·권한은 추론으로 채우지 않는다. 시뮬레이션은 스케일·방법·엔진을 분리하고 방법과 엔진은 다대다다. 연구실의 기존 도구를 존중한다(Lab Profile). GUI는 공통 틀 + 도메인 편집기 + 도구별 과학 코어로 나누고 capability spec에서 유도하며, GUI 검증은 엔진 검증을 대체하지 않는다. 단백질은 자연/설계/구조/실험 물성의 경로로 찾고 교차 검증한다. 멀티스케일 결합은 브릿지·결합 도구의 일.
- **HOOMD_GUI**: 시각적 모델링, 투명한 코드 생성, 과학 코어의 분리, 재현성 우선, 실행 전 검증, 버전이 있는 JSON 프로젝트 문서, loopback 전용 Local Runner. 2026-10-29 기준 개념 문서 + 2D 편집기 골격이고 코드 생성·실행은 미구현, 라이선스 미정.
