# consumption-insights: 프로젝트 마스터 계획

데이터 플랫폼(Snowflake, Databricks, BigQuery, Redshift)에서 **같은 워크로드를 돌릴 때 드는 월 비용(TCO)** 을 추정해 비교하는 대시보드를 만든다. 비용이나 실적에 의미 있는 변동이 생기면 글을 자동으로 생성하고, 사용자 승인을 거쳐 웹 아카이브(GitHub Pages)에 게시한다. 가격 변동 이력은 사용자의 Google 스프레드시트에도 쌓는다. LinkedIn 게시 방식은 결정 대기 중이다. 포트폴리오용 프로젝트다.

> **현재 위치:** Phase 1 진행 중. Task 1~5 코드 완료.
> - **가정 검토에서 변경 1건이 나와 Task 6을 보류했다.** BigQuery 스토리지를 논리 과금에서 물리 과금으로 바꿨다.
> - 변경분은 **아직 커밋하지 않았다.** 사용자 검토를 기다린다.
> - BigQuery 물리 스토리지 2행은 사용자 확인 대기다.
> - Phase별 진행계획은 `docs/phases/`에 있다.
>
> **마지막 갱신:** 2026-09-11

---

## 0. 진행 현황 한눈에

| 단계 | 상태 | 핵심 결과 | 진행계획 / 산출물 |
|---|---|---|---|
| 기획 1: 데이터 소스 조사 (09-10) | 완료 | 고객별 소비량은 비공개 → 층위를 나눠 설계. SEC·pypistats 직접 확인 | — |
| 기획 2: v1 가설 (09-10) | 완료(보존) | H1~H5, P | `docs/00_hypotheses_v1.md` |
| 기획 3: v2 방향 전환 (09-11) | 완료 | TCO 비교 + 변동 게시. T1~T3, H1·H2 | `docs/01_plan_v2.md` |
| Phase 0: 막힘 점검 (09-11) | 완료 | 약관 막힘 2건(LinkedIn, Snowflake·Databricks), 나머지는 통과 또는 조건부 | `docs/phases/phase-0-access-check.md`, `docs/02_phase0_report.md` |
| Phase 1: 가격·TCO·대시보드 | **진행 중** (Task 5/8 코드 완료, Task 6 보류) | 테스트 20/28 통과. 가정 검토로 BigQuery 스토리지를 물리 기준으로 바꿨다. 미리보기에서는 세 시나리오 모두 Redshift가 최저다 | `docs/phases/phase-1-tco-dashboard.md`, `docs/plans/phase1-tco-dashboard.md` |
| Phase 2: 자동 수집·변동 감지·게시·Sheets 적재 | 대기 | Sheets 적재 방식 확정(Python + google-auth). **전용 새 GCP 프로젝트 사용 결정** | `docs/phases/phase-2-automation-publish.md` |
| Phase 3: LinkedIn | 대기 (방식 결정 필요) | — | `docs/phases/phase-3-linkedin.md` |
| Phase 4: 실적 코너 + 비용 설계 실험 | 대기 | — | `docs/phases/phase-4-earnings-experiment.md` |
| Phase 5: 안정화·자동 게시 전환 | 대기 | — | `docs/phases/phase-5-stabilize.md` |

**결정·확인 대기**
1. **가정 변경 검토:** BigQuery 스토리지를 논리 과금에서 물리 과금으로 바꾼 것과 그 영향(T1이 기각 쪽으로 기움)을 확인한다. 확인되면 변경분을 커밋하고 Task 6으로 간다.
2. **BigQuery 물리 스토리지 2행 확인:** 스토리지 섹션의 "활성 물리적 스토리지", US(us) $0.000054795 / 서울 $0.000071233 per GiB-시간
3. LinkedIn 방식: Phase 3에서 결정한다. A' 공식 공유 링크를 추천한다.

**다음 행동:** 사용자가 1번을 확인하고 지시하면 변경분을 커밋한 뒤 Task 6(T1·T2 판정)을 한다. 끝나면 보고하고 멈춘다.

## 1. 작업 규칙 (Claude가 매 세션 지킬 것)

1. **계획 → 승인 → 실행.** 각 Phase는 두 문서로 관리한다.
   - **진행계획** `docs/phases/phase-N-*.md`: 목표, 단계, 담당, 사용자 할 일, 위험, 완료 기준, 진행 기록
   - **코드 단위 상세 계획** `docs/plans/phaseN-*.md`: 테스트와 구현 코드
   - Phase를 시작하기 전에 두 문서를 쓰거나 갱신하고, 승인을 받는다. 계획 없이 실행하지 않는다.
2. **"의견만" 달라는 요청에는 아무것도 실행하지 않는다.** 답은 결론 + 근거로 한다.
3. **근거에는 표기를 붙인다.**
   - [확인] 직접 호출해 확인한 것
   - [지식] 모델 지식(2026-05 기준)
   - [미확인] 아직 확인하지 않은 것
   - [가정] 모델에 넣은 가정
4. **외부로 나가는 행동은 매번 사용자 확인을 받는다.** LinkedIn 게시, 공개 배포, 계정 생성, 비밀키 입력이 여기에 해당한다. 계정 생성과 비밀키 입력은 사용자가 직접 한다.
5. **판정 기준은 데이터를 보기 전에 고정한다** (`config/thresholds.yaml`). 기준을 바꾸면 아래 결정 로그에 이유와 함께 기록한다.
6. **공개 저장소 전제로 작업한다.** 코드와 문서에 이메일, 토큰 같은 개인정보나 비밀값을 넣지 않는다. 필요한 값은 환경변수나 GitHub Secret으로 받는다(예: `SEC_USER_AGENT`, `GOOGLE_SA_KEY`, `PRICE_SHEET_ID`).
7. **작업이 끝날 때마다 문서를 갱신한다.**
   - 이 파일: 진행 현황 표, 체크박스, "현재 위치", 진행 로그
   - 해당 Phase의 진행계획 파일: 상태, 진행 과정 표, 진행 기록
8. **Windows 환경을 전제한다.** 기본 셸은 PowerShell이다. venv는 `.venv\Scripts\python.exe`로 직접 호출한다. Python에서 한글·특수문자를 출력할 때는 `PYTHONIOENCODING=utf-8`을 설정한다(cp949 오류를 겪었다 [확인]). 따옴표가 많은 인라인 Python은 PowerShell 대신 Bash heredoc으로 실행한다(f-string 따옴표가 깨졌다 [확인]).
9. **자동 접근·자동 게시 전에는 대상 사이트의 약관과 robots.txt를 확인한다.** 약관이 금지하는 대상에는 자동으로 접근하거나 게시하지 않는다. 브라우저 자동화 도구(예: Aside)로 우회하는 방식도 쓰지 않는다.
   - Snowflake·Databricks 웹사이트는 자동 모니터링을 금지한다 [확인].
   - LinkedIn은 API 약관과 사용자 약관 모두 자동 게시를 금지한다 [확인].
10. **진행 단위: 한 번에 Task 하나만 한다** (2026-09-11 사용자 지시).
    - 승인된 계획이라도 Task 하나를 끝내면 결과를 보고하고, 다음 지시를 기다린다.
    - 여러 Task나 Phase를 이어서 실행하지 않는다.
    - 사용자가 다른 단위를 지정하면 그 단위를 따른다.
    - 검토에서 변경이 필요하면 진행을 멈추고 문서에 먼저 반영한다(2026-09-11 사용자 지시).
11. **공개될 수 있는 개인정보가 기록되는 행동은 먼저 묻는다.** 커밋 이메일 같은 것이 여기에 해당한다. 문서에는 실제 주소나 개인 프로젝트 ID를 적지 않는다.
    - 커밋 전에는 커밋할 파일에 이메일 주소, 로컬 사용자 경로, 개인 프로젝트 ID가 없는지 검사한다.
12. **막히면 사용자 지시에 따라 Aside CLI(설치됨, 로그인됨)를 쓸 수 있는지 먼저 확인하고 보고한다** (2026-09-11 사용자 지시).
    - 규칙 9와 충돌하는 용도에는 쓰지 않는다.
    - 로그인, 비밀번호 입력, OAuth 승인, 서비스 계정 키 발급·열람은 사용자가 직접 한다.

## 2. 문서 지도

| 파일 | 역할 |
|---|---|
| `CLAUDE.md` (이 파일) | 전체 진행 마스터. 진행 현황, 규칙, 단계 요약, 결정 기록 |
| `docs/phases/phase-0-access-check.md` | Phase 0 진행계획과 결과(완료). 이 Phase가 바꾼 계획, 남은 확인 항목 |
| `docs/phases/phase-1-tco-dashboard.md` | Phase 1 진행계획. Task 표, 가격 확인 상태, **가정 검토 결과**, 사용자 할 일, 가정, 위험, 진행 기록 |
| `docs/phases/phase-2-automation-publish.md` | Phase 2 진행계획. 자동 수집, 이벤트 기준, 승인 흐름, Sheets 적재(2-2b)와 준비 방법(2-0c, 전용 새 프로젝트), 위험 |
| `docs/phases/phase-3-linkedin.md` | Phase 3 진행계획. 약관 제약, 선택지 A'/A/B/C 비교 |
| `docs/phases/phase-4-earnings-experiment.md` | Phase 4 진행계획. 실적 코너 판정 기준, H5/T3 실험 설계 |
| `docs/phases/phase-5-stabilize.md` | Phase 5 진행계획. 자동 전환·복귀 조건, 운영 점검표 초안 |
| `docs/plans/phase1-tco-dashboard.md` | Phase 1 코드 단위 상세 계획(Task 1~8). 맨 위에 진행 현황과 재개 계획이 있다 |
| `docs/01_plan_v2.md` | 설계 근거. 가설(T1~T3, H1·H2), TCO 모델, 가격 소스, 게시 흐름 |
| `docs/00_hypotheses_v1.md` | 이전 가설 설계(보존용) |
| `docs/02_phase0_report.md` | Phase 0 점검 결과. 가격 실측값, 약관 확인, T2 초기 신호, Aside 검토 |

## 3. 전체 흐름

```
[매일 GitHub Actions]
자동 수집: AWS 가격 파일(Redshift) · Azure API(Databricks, ADLS) ─┐
수동 가격표: Snowflake · BigQuery (사람이 원본 확인, confirmed_on) ─┼─→ 스냅샷(CSV) → TCO 계산 → 이전 값과 비교
SEC 실적 수집 (Phase 4) ────────────────────────────────────────┘                          │
                                                                              의미 있는 변동?
[분기 1회 알림 Issue: "Snowflake·Databricks 가격표 확인"]                      ├ 없음 → 스냅샷만 커밋
[BigQuery 가격 페이지 가격 문자열 지문 비교 (Phase 2, 약관 허용)]              └ 있음 ─┬→ 템플릿 글 초안 → PR
  → 사용자가 브라우저로 확인 → 수동 가격표 PR                                           │        │
                                                                                         │  [사용자가 PR 머지 = 승인]
                                                                                         │        │
                                                                                         │  사이트 빌드 → GitHub Pages → LinkedIn (방식 결정 대기)
                                                                                         └→ Google 스프레드시트에 변동 이력 행 추가 (Phase 2-2b)
```

- **기술 스택:** Python 3.11(프로젝트 venv), requests, PyYAML, Jinja2, plotly, pytest, GitHub Actions, GitHub Pages. Phase 2에서 google-auth를 추가한다.
- **저장:** 날짜별 CSV 스냅샷을 `data/raw/`에 둔다. Git에서 차이를 읽기 쉽기 때문이다. 정본은 Git이고, 스프레드시트는 비공개 변동 기록장이다.

## 4. 단계별 계획 (요약. 상세 과정은 각 Phase 진행계획 파일에 있다)

담당 표기: (C) Claude / (U) 사용자 / (C+U) 함께

### Phase 0: 막힘 점검 (완료). 진행계획: `docs/phases/phase-0-access-check.md`
- [x] 0-1 로컬 환경: 조건부 통과(gh `workflow` 권한과 duckdb 없음. duckdb는 Phase 1에서 불필요해져서 제외)
- [x] 0-2 AWS 가격 파일: 통과
- [x] 0-3 Azure Retail Prices API: 통과
- [x] 0-4 가격 페이지 약관: Snowflake·Databricks는 자동 모니터링 금지 [확인] → 자동 감지 폐기. BigQuery는 가능
- [x] 0-5 LinkedIn: API 약관 3.1(26)과 사용자 약관 13번이 자동 게시 금지 [확인]
- [x] 0-6 GitHub: 통과(저장소 설정 2개 필요)
- [x] 0-7 BigQuery 샌드박스: 조건부(스토리지 평생 10GiB)
- [x] 0-8 보고서 `docs/02_phase0_report.md`

### Phase 1: 가격 수집 + TCO 모델 + 정적 대시보드 (로컬). **진행 중**
진행계획: `docs/phases/phase-1-tco-dashboard.md`. 코드 계획: `docs/plans/phase1-tco-dashboard.md`. 괄호 안은 이전 1-x 번호다.

**목표:** 로컬에서 명령 한 번으로 가격을 수집하고 월 비용을 계산해 `site/`를 만든다.
- [x] **Task 1 (1-0) 뼈대 + 공통 스키마.** 완료, 커밋 `d5930d1`
  - [x] 뼈대 파일(`requirements.txt`, `pytest.ini`, `.gitignore`)
  - [x] venv 생성과 의존성 설치
  - [x] git init(main)
  - [x] 테스트 작성 → 실패 확인(`ModuleNotFoundError`)
  - [x] `common/schema.py` 구현
  - [x] 테스트 3개 통과
  - [x] 첫 커밋: 이 저장소 전용 noreply 이메일 사용. 개인정보 검사 0건, 파일 11개
- [x] **Task 2 (1-2) AWS Redshift 수집기.** 완료, 커밋 `0c5b6c9`
  - 테스트 3개 통과(누적 6개).
  - 실제 조회값은 서버리스 RPU $0.375/$0.438, 관리형 스토리지 $0.024/$0.0261(미국/서울)로 Phase 0 값과 같다 [확인].
  - 선결제 항목이 실제 데이터에서도 걸러졌다.
- [x] **Task 3 (1-3) Azure 수집기.** 완료, 커밋 `4e2ef6c`
  - 테스트 3개 통과(누적 9개).
  - 실제 조회값은 Databricks 서버리스 SQL DBU $0.70/$0.95, ADLS Hot LRS $0.0208/$0.02(미국/서울)로 Phase 0 값과 같다 [확인].
- [ ] **Task 4 (1-1, 1-4 변경) 수동 가격표 + 확인 게이트.** 코드 완료(커밋 `c8da16f`), 확인 10행 중 8행 완료
  - [x] 테스트 4개 통과(누적 13개)
  - [x] (U) Snowflake 4행 확인(2026-09-11)
  - [x] (U) BigQuery 컴퓨트 4행 확인(2026-09-11): 온디맨드 $6.25/$7.50, 용량 컴퓨팅 기본값 $0.06/$0.0765
  - [ ] (U) **BigQuery 물리 스토리지 2행 확인**(가정 검토로 논리 → 물리로 변경). 비어 있으면 파이프라인이 멈춘다.
- [ ] **Task 5 (1-5) 워크로드 가정 + 월 비용 계산.** 코드 완료(커밋 `56e95fb`), 가정 검토 완료, 변경 1건(미커밋)
  - [x] `data/manual/workloads.yaml`, `tests/conftest.py`, `model/tco.py`
  - [x] 테스트 7개 통과(누적 20개). W1 손계산 $1,550, GiB 변환, W3 스캔 → 시간 환산을 검증했다.
  - [x] 가정 검토
    - 변경: 스토리지 기준을 "압축(물리) 후 10TB"로 통일하고, BigQuery는 물리 과금을 쓴다.
    - 명시: W3 스캔량은 논리 바이트 기준이다.
    - 나머지 가정은 유지한다.
  - [ ] (U) 변경 검토 → 커밋
- [ ] Task 6 (1-6) T1 순위·민감도, T2 서울 프리미엄 판정: `config/thresholds.yaml`. **보류**(1번 확인 후)
- [ ] Task 7 (1-7) 정적 대시보드: 판정표, 차트, 가정 공개, 가격 확인일
- [ ] Task 8 (1-8) `pipeline.py` 실제 실행과 검증
  - pytest 28개 통과
  - (U) 화면 확인, 가격 3개 대조
- **게이트:** (U) 화면 확인 → Phase 2 상세 계획 승인

### Phase 2: 자동 수집 + 변동 감지 + 승인 흐름 + 아카이브 게시 + Sheets 적재. 진행계획: `docs/phases/phase-2-automation-publish.md`
**목표:** 매일 자동 수집하고, 변동이 생기면 PR로 초안을 올리며, 머지하면 Pages에 게시된다. 변동 이력은 Google 스프레드시트에 쌓는다.
- [ ] 2-0 (U) GitHub 준비
  - `gh auth refresh -s workflow` 실행(브라우저 승인은 사용자가 직접)
  - 공개 저장소 생성
  - Settings > Actions > General에서 워크플로 PR 생성 허용, GITHUB_TOKEN 쓰기 권한 설정
  - Pages 소스를 GitHub Actions로 설정
  - Secret `SEC_USER_AGENT` 등록
- [ ] 2-0b (C) `.gitattributes`(`* text=auto eol=lf`) 추가를 검토한다. Windows 작업 사본(CRLF)과 Linux CI의 줄바꿈을 맞추기 위해서다.
- [ ] 2-0c (U, C 보조) Google Sheets 준비
  - **이 프로젝트 전용 새 GCP 프로젝트를 만든다(2026-09-11 사용자 결정).** 새 프로젝트에서 Sheets API를 활성화한다.
  - 서비스 계정과 JSON 키 발급 → Secret `GOOGLE_SA_KEY`
  - 스프레드시트를 만들어 서비스 계정에 편집 권한을 공유 → Secret `PRICE_SHEET_ID`
  - 키 발급과 열람은 사용자가 직접 한다.
- [ ] 2-1 (C) `.github/workflows/collect.yml`
  - 매일 00:17 UTC(= 09:17 KST, 정각 혼잡 회피)
  - 수집 → 스냅샷 커밋
  - Actions 서버에서 AWS·Azure·SEC 호출이 되는지 여기서 확인
- [ ] 2-2 (C) `detect/diff.py`
  - 이전 스냅샷과 비교해 `events.json` 생성
  - E1 기준: 월 비용 ±1% 이상 변동 또는 순위 변경. 수동 가격표 변경도 여기서 E1이 된다.
  - 같은 날 이벤트는 합치고, 하루 최대 1건
- [ ] 2-2b (C) **가격 변동 이력 Google Sheets 적재** `publish/sheets_log.py`
  - Python + google-auth로 Sheets API `values.append`를 호출한다.
  - 실패해도 파이프라인은 계속하고 Issue로 알린다.
  - 처음 연결할 때 현재 가격을 기준선으로 한 번 기록한다.
- [ ] 2-3 (C) 글 생성
  - `templates/post_price_change.md.j2`, `publish/render_post.py`
  - 숫자 일치 검사: 글에 나온 모든 숫자가 `events.json`에 있어야 하고, 아니면 중단
- [ ] 2-4 (C) 이벤트가 있으면 `posts/`에 초안을 쓰고 PR 생성(라벨 `needs-approval`)
- [ ] 2-5 (C) `.github/workflows/publish.yml`: main에 push되면 사이트와 아카이브를 빌드해 Pages에 배포
- [ ] 2-6 (C) 가격 변경 감지와 알림
  - **분기 1회** "Snowflake·Databricks 가격표 확인" Issue(공식 링크 + 체크리스트). 두 사이트에는 자동으로 접근하지 않는다.
  - BigQuery 가격 페이지는 리전별 가격 문자열의 지문을 비교하고, 바뀌면 Issue를 연다(Google 약관 허용, robots.txt 준수, 하루 1회).
- [ ] 2-7 (C+U) 검증
  - 가짜 가격 변동 주입 → PR 생성 → **사람이 머지했을 때 publish.yml이 실행되는지 실측** → 게시
  - 변동이 없으면 PR이 없는지(멱등성)
  - `--dry-run` 모드 동작
  - 시트에 행이 추가되는지 확인
- **게이트:** (U) 첫 실제 게시 전 확인 → Phase 3 상세 계획 승인

### Phase 3: LinkedIn (사용자 결정 대기). 진행계획: `docs/phases/phase-3-linkedin.md`
- **사용자 지시(2026-09-11):** aside cli로 API를 따서 자동 게시
- **검토 결과:** Aside는 로그인 세션을 쓰는 브라우저 자동화다. 이 방식은 LinkedIn 사용자 약관 13번(봇·무단 자동화로 게시물 생성 금지)과 API 약관 3.1(26)에 해당하고, 사용자 계정이 제한될 위험이 있다 [확인].
  - **Claude는 이 방식을 구현하지 않는다.**
- **선택지**
  - A' 공식 공유 링크(반자동, 추천): 게시 PR에 게시문 + `share-offsite` 공식 공유 링크를 넣고, 사용자가 눌러서 게시한다.
  - A 수동 복사·붙여넣기
  - B 공식 API + 매번 사용자가 직접 실행: 회색지대이고, 60일마다 토큰을 재발급해야 한다.
  - C 제외
- 결정이 나면 이 Phase의 작업 목록을 다시 쓴다.

### Phase 4: 실적 코너(H1·H2) + 비용 설계 실험(H5 → T3). 진행계획: `docs/phases/phase-4-earnings-experiment.md`
**목표:** 실적 공시 이벤트로 글이 생성되고, BigQuery 실측으로 T3를 판정한다.
- [ ] 4-1 (C) `collectors/sec_filings.py`
  - companyfacts에서 매출과 RPO
  - submissions에서 8-K item 2.02 감지
  - 본문에서 NRR과 $1M 초과 고객 수 파싱. 보도자료 파일명이 비표준이므로 인덱스의 EX-99.1 타입으로 찾는다 [확인]
- [ ] 4-2 (C) E2 이벤트 처리 + `templates/post_earnings.md.j2`
  - H1: 기존 고객 기여 비중
  - H2: RPO 커버리지
- [ ] 4-3 (C) 재현 검증: 2026-07 분기의 NRR 126%, RPO $9.0B, 커버리지 1.51 → 1.45 [확인]
- [ ] 4-4 (U+C) 개인 Gmail로 BigQuery 샌드박스 준비
  - 서비스 계정 키, JOBS 조회, CTAS·클러스터 테이블 생성이 되는지 실측
  - 스토리지는 평생 10GiB이고 복구되지 않는다. 부족하면 결제 계정 연결 여부를 결정한다.
- [ ] 4-5 (C) H5 실험
  - V0(dry run 추정치만)부터 V4까지 실행
  - 쿼리 캐시를 끄고, 결과 해시가 같은지 확인
  - V3·V4 사본은 작게 한 번만 만들고, 60일 만료 때만 다시 만든다.
  - `JOBS_BY_PROJECT` 수집 → T3 판정
- [ ] 4-6 (C) BigQuery 실측으로 `workloads.yaml`의 플랫폼 간 환산값을 보정한다. Snowflake 30일 트라이얼로 1회 보정하는 것은 선택
- [ ] 4-7 (C, 선택) E3 이벤트: H5/T3 실험 결과를 매달 요약하는 글 템플릿(`templates/post_experiment.md.j2`)
- **게이트:** (U) 확인 → Phase 5 상세 계획 승인

### Phase 5: 안정화와 자동 게시 전환 (아카이브 한정). 진행계획: `docs/phases/phase-5-stabilize.md`
- [ ] 5-1 (C) 승인 기록 집계. 연속 5건을 수정 없이 승인하면 전환을 제안한다.
- [ ] 5-2 (C+U) 아카이브 자동 게시 모드로 전환
  - 수집 워크플로 안에서 바로 배포한다.
  - 이유: GITHUB_TOKEN으로 한 머지는 다른 워크플로를 트리거하지 않는다 [확인]
  - LinkedIn은 약관상 자동으로 전환하지 않는다.
- [ ] 5-3 (C) `docs/operations.md` 운영 점검표 작성
  - 분기 1회 벤더 가격 확인
  - 공개 저장소 60일 규칙과 재활성화 API
  - (B안을 택한 경우) LinkedIn 토큰 재발급
- [ ] 5-4 (C) 포트폴리오용 README 작성

## 5. 확인된 사실 (재사용)
**데이터 소스**
- SEC EDGAR는 `User-Agent`에 연락처가 있어야 하고, 초당 10회까지 호출할 수 있다.
  - companyfacts: 매출, RPO [확인]
  - submissions: 공시 목록 [확인]
  - NRR과 제품매출은 XBRL에 없다 [확인].
- Snowflake 2026-07 분기 [확인]
  - 총매출 $1.547B, NRR 126%, $1M 초과 고객 828곳, RPO $9.0B
  - 보도자료 파일명은 `fy2027q2earnings.htm`이었다(`ex99` 패턴이 아니다).
- AWS 가격 파일: 인증 없이 받을 수 있고, 리전별 파일은 0.1~0.5MB다. OnDemand 항목 안에 선결제 금액이 시간당 단가처럼 섞여 있다 [확인]. Task 2 수집기가 이를 걸러낸다 [확인].
- Azure Retail Prices API [확인]
  - Databricks 서버리스 SKU는 `Azure Databricks Regional`이다. 클래식 DBU는 리전과 관계없이 가격이 같다.
  - ADLS Gen2 Hot LRS 첫 구간은 eastus $0.0208, koreacentral $0.02로 서울이 더 싸다.
  - Task 3 수집기로 다시 확인했다.
- BigQuery 가격 페이지: HTML에 리전별 가격이 SKU 이름 없이 위치 배열로 들어 있다. nonce가 매번 바뀐다 [확인].
  - 리전 이름은 "US (us)"다.
  - **스토리지**: GiB-시간 단위로 표시된다. 매월 10GiB가 무료다.
    - Active logical: US $0.000027397, 서울 $0.000031507 (사용자 확인)
    - Active physical: US $0.000054795, 서울 $0.000071233 (페이지 데이터에서 추출한 후보, 확인 대기)
  - **주문형 컴퓨팅** 섹션: 쿼리(주문형)는 매월 1TiB 무료이고, 그 이상은 US $6.25 / 서울 $7.50 per TiB다(사용자 확인).
  - **용량 컴퓨팅** 섹션: 기본값(종량제)은 US $0.06 / 서울 $0.0765 per slot-hour다(사용자 확인). 약정은 두 종류다.
    - BigQuery CUD: 1년 $0.054 / 3년 $0.048 (서울 $0.06885 / $0.0612)
    - 리소스 CUD: 1년 $0.048 / 3년 $0.036 (서울 $0.0612 / $0.0459)
- Snowflake 서비스 소비표(2026-09-09 발효)는 Table 2(a)에 크레딧 단가, Table 3(a)에 스토리지 단가가 있다. AWS US East (N. Virginia)와 Seoul 값을 사용자가 확인했다.
- 스토리지 과금 기준 [지식]: Snowflake·Redshift RMS·ADLS(Parquet/Delta)는 압축된 저장량으로 과금한다. BigQuery는 논리(압축 전) 과금과 물리(압축 후) 과금 중 하나를 고를 수 있다.
- 가격 실측값과 서울 프리미엄 표는 `docs/02_phase0_report.md`에 있다.

**약관**
- Snowflake 사이트 약관 5(i)(2025-04-14)와 Databricks 이용약관(2018-05-25)은 수동·자동 도구로 사이트를 모니터링하는 것을 금지한다 [확인].
- LinkedIn API 약관 3.1(26)은 API로 게시를 자동화하는 것을 금지한다 [확인]. 사용자 약관 13번(2025-11-03)은 봇·무단 자동화로 게시물을 생성하는 것을 금지한다 [확인].
- Google 약관은 robots.txt 등 기계 판독 지침을 지키는 자동 접근을 허용한다 [확인].
- Aside(aside.com)는 로그인된 브라우저를 CLI로 조종하는 자동화 플랫폼이다 [확인]. 도구를 바꿔도 위 약관의 적용은 같다.

**플랫폼**
- GitHub [확인]
  - Pages는 Free 플랜에서 공개 저장소만 쓸 수 있다.
  - GITHUB_TOKEN이 일으킨 이벤트는 새 실행을 만들지 않는다(workflow_dispatch·repository_dispatch 예외).
  - 새 저장소는 워크플로 PR 생성이 금지돼 있고 토큰이 읽기 전용이다.
- BigQuery 샌드박스: 스토리지는 평생 10GiB이고 삭제해도 복구되지 않는다. 쿼리는 월 1TiB, 테이블은 60일 뒤 만료되고 DML은 쓸 수 없다 [확인].
- Google Sheets 연동 [확인]
  - `gcloud`에는 Sheets 명령이 없다 [지식].
  - `gws` CLI 0.22.5는 설치돼 있고, OAuth와 서비스 계정 인증을 지원한다. 다만 공식 지원 제품은 아니다.
  - 기존 강의용 gcloud 프로젝트에서 Sheets API가 사용 설정돼 있고, 서비스 계정은 0개다. 이 프로젝트에는 전용 새 프로젝트를 쓴다.

**실행 환경 (Phase 1에서 확인)**
- 로컬: Python 3.11.7(Anaconda). gh 토큰에 `workflow` 권한이 없다 [확인].
- Google Cloud SDK 579.0.0(`gcloud`, `bq` 2.1.36)이 설치돼 있고, 사용자 개인 계정 1개로 로그인돼 있다 [확인].
- venv에 설치된 버전 [확인]: requests 2.34.2, PyYAML 6.0.3, Jinja2 3.1.6, plotly 7.0.0, pytest 9.1.1 (pip 23.2.1)
- plotly는 계획 기준(5.x)보다 새 버전(7.0.0)이 설치됐다. 그래도 Task 7에서 쓸 API(`get_plotlyjs_version`, `to_html`, `add_bar`)는 동작하고, JS 4.0.0 CDN 파일도 200 응답(약 4.3MB)을 확인했다 [확인].
- 커밋 이메일: 이 저장소에서만 `git config --local`로 GitHub noreply 주소를 쓴다. 전역 설정(noreply 아님)은 그대로다 [확인]. 주소 자체는 기록하지 않는다(규칙 11). 작성자 이름은 전역 설정을 쓰고, push 전까지는 공개되지 않는다.
- git 줄바꿈: 커밋할 때 "LF will be replaced by CRLF" 경고가 나온다. 전역 autocrlf 설정 때문이며, 저장소에는 LF로 저장된다 [확인]. Phase 2 전에 `.gitattributes`를 검토한다(2-0b).
- Aside CLI 1.26.906.1630이 설치돼 있고, 계정 u0(Google 제공자)로 로그인돼 있다 [확인]. `aside account`는 하위 명령(`list`, `status`)이 필요하다.
- PowerShell에서 `gh --jq` 식을 쓰면 따옴표가 깨진다. `gh api ... | ConvertFrom-Json`을 쓴다 [확인].
- 첫 커밋 전에는 git worktree를 만들 수 없어서 main에서 진행했다. 이후 Task도 규칙 10(Task마다 확인)에 따라 main에 로컬 커밋한다.

## 6. 결정 로그
| 날짜 | 결정 | 이유 |
|---|---|---|
| 2026-09-10 | 고객별 소비량 대신 층위를 나눠 설계 | 고객별 소비량은 어디에도 공개되지 않는다 |
| 2026-09-10 | 혼합안 채택: 가입 필요 서비스 최소화, 기간제 무료 체험은 계속 수집에 쓰지 않음 | 막힘(접근권한·무료 조건) 최소화 |
| 2026-09-10 | v1 가설 설계(H1~H5, P) | `docs/00_hypotheses_v1.md` |
| 2026-09-11 | 방향 전환: 같은 워크로드의 월 비용(TCO) 비교 + 변동 시 자동 게시 | 사용자 결정. 포트폴리오용 웹 아카이브 |
| 2026-09-11 | 게시 위치는 GitHub Pages + LinkedIn, 글은 템플릿 문장, 처음엔 승인 후 안정되면 자동 | 사용자 결정 |
| 2026-09-11 | 가설 v2: T1~T3 신규, H1·H2 유지, H3·H4 보류, P·합성 코호트 제외 | `docs/01_plan_v2.md` |
| 2026-09-11 | 저장소를 비공개에서 공개로 변경 | GitHub Pages 무료 사용 조건 [확인] |
| 2026-09-11 | 대시보드를 Streamlit에서 정적 HTML + Plotly로 변경 | Pages 배포와 아카이브를 한 사이트로 합치기 위해 |
| 2026-09-11 | Snowflake·Databricks 가격은 스크래핑하지 않고 수동 가격표로 관리 | 공식 API가 없고, 약관이 자동 모니터링을 금지한다 [확인] |
| 2026-09-11 | Snowflake·Databricks 가격 확인은 **분기 1회** 알림 + 사용자 확인 | 사용자 지정 대체안. aside 자동 감지는 약관상 불가 |
| 2026-09-11 | LinkedIn 자동 게시(aside 세션 자동화)를 구현하지 않음. A'/A/B/C 중 결정 대기 | LinkedIn 사용자 약관 13번, API 약관 3.1(26) [확인]. 계정 제한 위험 |
| 2026-09-11 | Phase 1: BigQuery는 수동 가격표, Databricks는 Azure API(서버리스 SQL + ADLS) | BigQuery 페이지 파싱이 불안정하다. Azure는 공식 API이고 AWS 직판과 같은 가격이다 [확인] |
| 2026-09-11 | Phase 1에서 S3, duckdb, pandas, pyarrow를 제외하고 스냅샷은 CSV로 | YAGNI. Git 차이를 읽기 쉽다 |
| 2026-09-11 | T2 판정 기준: 서울 프리미엄의 최대-최소 차이 10%p 이상이면 지지 | **주의:** Phase 0 초기 신호(0~37%)를 본 뒤 정한 값이라 사전 고정 원칙의 예외다. 공개한다 |
| 2026-09-11 | Phase 1 실행 방식: 이 세션에서 Task별로 진행 | 사용자 무응답이라 기본값 적용. 과정을 따라가기 쉽다 |
| 2026-09-11 | 진행 단위: Task 하나마다 멈추고 보고(규칙 10) | 사용자 지시("한 번에 모든 phase를 진행하려고 하지 말고 여기서 중단") |
| 2026-09-11 | main 브랜치에 로컬 커밋 | 커밋 없는 새 저장소라 worktree가 불가하다. 승인된 계획 |
| 2026-09-11 | 커밋 이메일: 이 저장소만 GitHub noreply(`--local`), 이름은 전역 설정 | 사용자 결정. 공개 저장소에서 실제 이메일이 드러나지 않게 한다(규칙 11) |
| 2026-09-11 | 막히면 Aside CLI를 먼저 검토(규칙 12). 첫 커밋에는 쓰지 않음 | 사용자 지시. 로컬 커밋은 인증이 필요 없어 막히지 않았다 |
| 2026-09-11 | Phase별 진행계획은 `docs/phases/`에 별도 파일로 두고, 코드 계획은 `docs/plans/`에 둔다(규칙 1·7) | 사용자 지시. 전체 계획서에서 각 Phase의 과정을 상세히 보기 위해서다 |
| 2026-09-11 | 가격 변동 이력은 Google 스프레드시트에 적재한다: Python + google-auth + 서비스 계정, Phase 2-2b | 사용자 결정(권장안 채택). gcloud는 Sheets 명령이 없고, gws는 0.x 비공식 도구라 매일 도는 자동화에 쓰지 않는다 |
| 2026-09-11 | Sheets 적재는 Phase 2에서 구현하고, 서비스 계정 키도 그때 발급한다 | Sheets API는 이미 사용 설정돼 있어서 Aside로 따로 확보할 것이 없다 [확인]. 쓰지 않는 장기 키를 미리 만들면 노출 기간만 늘어난다 |
| 2026-09-11 | BigQuery 스토리지는 페이지의 GiB-시간 값에 730시간/월을 곱해 GiB-월로 저장 | 모델의 단위(GiB-월)에 맞춘다. 원래 표시값은 Phase 1 진행계획에 남긴다 |
| 2026-09-11 | BigQuery 슬롯 단가는 용량 컴퓨팅의 **기본값(종량제)**을 쓴다(약정가 제외) | TCO 모델이 약정 할인을 제외하기 때문이다(가정 공개 항목) |
| 2026-09-11 | **이 프로젝트 전용 새 GCP 프로젝트를 쓴다**(Phase 2-0c) | 사용자 결정. 서비스 계정 권한과 키의 범위를 기존 강의용 프로젝트와 분리한다 |
| 2026-09-11 | **가정 검토 결과: 스토리지 기준을 "압축(물리) 후 10TB"로 통일하고, BigQuery는 active physical storage 단가를 쓴다.** W3 스캔량은 논리 바이트 기준이라고 명시한다 | 사용자가 검토를 위임했다. BigQuery 논리 과금만 압축 전 기준이라 비용이 과소평가됐다. 이 변경으로 W3 1위가 BigQuery에서 Redshift로 바뀐다(미리보기). 사용자 검토 대기, 미커밋 |

## 7. 진행 로그
- **2026-09-10:** 데이터 소스 조사. SEC와 pypistats를 직접 호출해 확인했다. 혼합안과 v1 가설 설계를 확정했다.
- **2026-09-11:** 프로젝트 폴더 `C:\consumption-insights`를 만들었다. v2 방향 전환을 승인받았다. 이 마스터 계획(CLAUDE.md)을 작성했다.
- **2026-09-11:** Phase 0 점검을 완료했다. 약관 막힘 2건(LinkedIn 자동 게시, Snowflake·Databricks 자동 감시)을 발견했다.
- **2026-09-11:** 사용자 지시(aside cli)를 검토했다. Aside는 브라우저 자동화이고, 약관 적용이 같다는 것을 확인했다. Snowflake·Databricks는 사용자가 지정한 대체안(분기 1회)을 적용하고, LinkedIn은 자동 게시를 구현하지 않기로 하고 대안을 제시했다. Phase 1 상세 계획(Task 1~8, 테스트 28개)을 작성했다.
- **2026-09-11:** Phase 1 승인 → Task 1의 1~6단계를 완료했다(venv·의존성·git init·스키마, 테스트 3개 통과). 커밋 전 git 이메일을 확인하던 중 사용자 지시로 중단했다. 이어서 진행 현황을 정리하고 규칙 10·11을 추가했다.
- **2026-09-11:** Task 1을 재개해 완료했다.
  - 재개 계획을 계획서 맨 위에 정리했다.
  - 이 저장소 전용으로 noreply 이메일을 설정했다.
  - 개인정보 검사는 0건, 테스트 3개가 통과했다.
  - 첫 커밋은 `d5930d1`(파일 11개)이다. 작성자 이메일이 noreply인 것을 확인했다.
  - Aside CLI가 설치돼 있는 것을 확인했지만 쓸 필요는 없었다.
- **2026-09-11:** 사용자 지시로 Phase별 진행계획 파일 6개를 `docs/phases/`에 작성했다(Phase 0~5). 규칙 1·7을 갱신했다. 문서 커밋은 `6e8c670`이다.
- **2026-09-11:** Task 2를 완료했다(커밋 `0c5b6c9`).
  - `collectors/aws_prices.py`를 TDD로 구현했다(실패 확인 → 구현 → 통과).
  - 테스트는 누적 6개가 통과했다.
  - 실제 AWS 조회값이 Phase 0 값과 같다: RPU $0.375/$0.438, 스토리지 $0.024/$0.0261.
  - 선결제 항목이 걸러지는 것을 확인했다.
- **2026-09-11:** Task 3을 완료했다(커밋 `4e2ef6c`).
  - `collectors/azure_prices.py`를 TDD로 구현했다(ImportError로 실패 확인 → 구현 → 통과).
  - 테스트는 누적 9개가 통과했다.
  - 실제 Azure 조회값이 Phase 0 값과 같다: DBU $0.70/$0.95, ADLS $0.0208/$0.02.
- **2026-09-11:** Google Sheets 적재 방식을 검토했고, 사용자가 권장안(Python + google-auth, Phase 2-2b)을 채택했다.
  - gcloud 579.0.0, bq, gws 0.22.5가 설치돼 있다.
  - Sheets API는 이미 사용 설정돼 있고, 서비스 계정은 0개다.
  - Aside는 로그인돼 있다.
  - Phase 2 진행계획에 2-0c(준비 방법)와 2-2b를 추가했다.
- **2026-09-11:** Task 4 코드를 완료했다(커밋 `c8da16f`).
  - `collectors/manual_prices.py`를 TDD로 구현하고, 가격표 2개를 작성했다.
  - 테스트는 누적 13개가 통과했다.
  - 사용자 확인: Snowflake 4행과 BigQuery 논리 스토리지 2행을 확인했다.
  - 실제 가격표에서 게이트가 멈추는 것을 확인했다.
- **2026-09-11:** Task 5 코드를 완료했다(커밋 `56e95fb`).
  - `workloads.yaml`, `tests/conftest.py`, `model/tco.py`를 TDD로 작성했다.
  - 테스트는 누적 20개가 통과했다.
- **2026-09-11:** 사용자 확인을 반영하고 가정을 검토했다(미커밋).
  - BigQuery 컴퓨트 4행을 확인해 `confirmed_on`을 적었다.
  - 전용 새 GCP 프로젝트를 쓰기로 했다.
  - 가정 검토 결과 변경 1건이 나와 **Task 6을 보류했다**.
    - 스토리지를 물리 기준으로 통일했다. BigQuery는 active physical이고, 후보값은 $0.04/$0.052(확인 대기)다.
    - W3 스캔량은 논리 바이트 기준이라고 명시했다.
  - 미리보기에서는 세 시나리오 모두 Redshift가 1위다(이전에는 W3가 BigQuery였다).
  - 약정 가격 안내 오류(CUD 두 종류)를 바로잡았다.
  - 사용자의 변경 검토를 기다린다.
