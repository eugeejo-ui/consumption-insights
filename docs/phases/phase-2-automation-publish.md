# Phase 2: 자동 수집 + 변동 감지 + 승인 흐름 + 아카이브 게시

| 항목 | 내용 |
|---|---|
| 상태 | 대기 (Phase 1 게이트 이후) |
| 목표 | 매일 자동으로 가격을 모은다. 의미 있는 변동이 생기면 글 초안을 PR로 올리고, 사용자가 머지하면 GitHub Pages에 게시한다. 가격 변동 이력은 사용자의 Google 스프레드시트에도 쌓는다 |
| 선행 조건 | Phase 1 완료, 사용자의 GitHub 준비(2-0), Google Sheets 준비(2-0c) |
| 코드 단위 계획 | 착수할 때 `docs/plans/phase2-*.md`로 작성하고 승인을 받는다 |

## 흐름
```
[매일 00:17 UTC, collect.yml]
수집 → 스냅샷 커밋 → 이전 값과 비교(diff.py)
                          ├ 변동 없음 → 끝
                          └ 변동 있음 → events.json ─┬→ 템플릿 글 초안 → 숫자 일치 검사 → PR(needs-approval)
                                                    │                                         │
                                                    │                        [사용자가 PR 머지 = 승인]
                                                    │                                         │
                                                    │                publish.yml → 사이트·아카이브 빌드 → GitHub Pages
                                                    └→ Google 스프레드시트에 변동 이력 행 추가 (2-2b, 실패해도 파이프라인은 계속)
```

## 진행 과정
| 단계 | 작업 | 담당 | 산출물 | 완료 기준 |
|---|---|---|---|---|
| 2-0 | GitHub 준비: `gh auth refresh -s workflow`(브라우저 승인), 공개 저장소 생성, Actions 설정 2개(PR 생성 허용, 토큰 쓰기 권한), Pages 소스를 Actions로, Secret `SEC_USER_AGENT` | U | 원격 저장소 | 설정 5개 완료 |
| 2-0b | `.gitattributes`(`* text=auto eol=lf`) 검토 | C | `.gitattributes` | Windows와 CI의 줄바꿈 일치 |
| 2-0c | Google Sheets 준비: Sheets API 활성화, 서비스 계정과 키, 스프레드시트 생성과 공유, Secret 2개(`GOOGLE_SA_KEY`, `PRICE_SHEET_ID`). 아래 "Google Sheets 준비 방법" 참고 | U (+C) | 비공개 스프레드시트 | 서비스 계정으로 테스트 행 1줄 추가 성공 |
| 2-1 | 매일 수집 워크플로 | C | `.github/workflows/collect.yml` | Actions 서버에서 AWS·Azure·SEC 호출 성공, 스냅샷 커밋 |
| 2-2 | 변동 감지 | C | `detect/diff.py`, `events.json` | 가짜 변동을 주입하면 이벤트가 생성되고, 변동이 없으면 이벤트가 없다 |
| 2-2b | **가격 변동 이력 Google Sheets 적재** | C | `publish/sheets_log.py`(Python + `google-auth`, Sheets API `values.append`) | 가짜 이벤트 1건 → 시트에 1행이 추가된다. 인증 실패는 파이프라인을 멈추지 않고 Issue로 알린다. 처음 연결할 때 현재 가격을 기준선으로 한 번 기록한다 |
| 2-3 | 글 생성 | C | `templates/post_price_change.md.j2`, `publish/render_post.py` | 숫자 하나를 바꿔 넣으면 검사가 실패한다 |
| 2-4 | 초안 PR 생성 | C | `posts/` 초안, PR | 이벤트가 있으면 PR 1건이 생긴다 |
| 2-5a | **대시보드 디자인 게이트** (2026-09-11 사용자 지시): 공개 대시보드를 만들기 **전에 멈추고 보고**한다. 사용자가 마음에 드는 대시보드 템플릿을 주면, Claude가 그 디자인(레이아웃, 색, 타이포, 차트 스타일)을 분석해 비슷한 디자인으로 대시보드를 만든다. Phase 1의 `site/index.html`은 기능 확인용 임시 디자인이다 | U → C | 사용자 템플릿, 디자인 적용 계획 | 사용자가 템플릿을 주고 디자인 적용 계획을 승인한다 |
| 2-5 | 게시 워크플로 | C | `.github/workflows/publish.yml` | main에 push하면 Pages가 갱신된다(2-5a 디자인 반영 후) |
| 2-6 | 가격 확인 알림 | C | Issue 생성 로직 | 분기 알림이 생성되고, BigQuery 지문이 바뀌면 Issue가 열린다 |
| 2-7 | 종단 검증 | C+U | 검증 기록 | 사람이 머지했을 때 publish.yml이 실행된다(실측). 멱등성, `--dry-run`, 시트 적재 확인 |

## 이벤트 기준 (사전 고정, `config/thresholds.yaml`)
- **E1 가격 변동:** 어떤 시나리오든 월 비용이 ±1% 이상 바뀌거나 순위가 바뀌면 이벤트다. 사람이 수동 가격표를 고친 경우도 포함한다.
- **게시 빈도:** 같은 날 생긴 이벤트는 하나로 합치고, 하루 최대 1건만 게시한다.
- **게시 전 검사:** 글에 나오는 모든 숫자가 `events.json`에 있어야 한다. 하나라도 없으면 게시를 중단한다.

## 가격 변동 이력 Google Sheets 적재 (2-2b, 2026-09-11 사용자 결정)
- **방식:** Python + `google-auth`(Google 공식 라이브러리)로 Sheets API의 `spreadsheets.values.append`를 호출한다. 의존성은 `google-auth` 하나만 늘어난다. HTTP 호출에는 기존 `requests`를 쓴다.
- **인증:** 서비스 계정 키를 쓴다(GitHub Secret `GOOGLE_SA_KEY`). 스프레드시트는 사용자의 개인 Google 계정에 두고, 서비스 계정 이메일에만 편집 권한을 공유한다(비공개).
- **정본과의 관계:** 정본은 Git의 CSV 스냅샷이다. 시트는 사용자가 보는 비공개 변동 기록장이다.
- **한 행에 기록하는 항목:** 감지일, 플랫폼, 항목(SKU), 리전, 이전 단가, 새 단가, 변동률(%), 출처, 커밋 링크
- **실패 처리:** 시트 쓰기가 실패해도 수집·게시는 계속하고, Issue로 알린다.
- **쓰지 않는 도구와 이유**
  - `gcloud`: Sheets 명령이 없다.
  - `gws` CLI: 0.x 버전이고 Google 공식 지원 제품이 아니다. 로컬 수동 작업에는 써도 된다.

## Google Sheets 준비 방법 (2-0c, 사용자)
계정: 개인 Google 계정. 이미 gcloud에 로그인되어 있다(사용자 확인).

**2026-09-11 확인한 현재 상태** [확인]
- 활성 gcloud 프로젝트(강의용 기존 프로젝트)에서 **Sheets API는 이미 사용 설정돼 있다.** 따라서 1단계는 새 프로젝트를 쓸 때만 필요하다.
- 이 프로젝트에 서비스 계정은 0개다.
- Aside CLI는 계정 u0(Google 제공자)로 로그인돼 있다.
- **결정(2026-09-11, 사용자): 이 프로젝트 전용 새 GCP 프로젝트를 만든다.** 서비스 계정 권한과 키의 범위를 기존 강의용 프로젝트와 분리하기 위해서다.
  - 새 프로젝트에서는 Sheets API를 다시 활성화해야 한다. 아래 1단계가 필요하다.
  - 프로젝트 ID는 공개 문서에 적지 않는다.
  - 프로젝트 생성은 사용자가 콘솔(https://console.cloud.google.com/projectcreate)에서 하거나, `gcloud projects create`로 한다. 결제 계정 연결은 필요 없다(Sheets API는 무료).

1. **Sheets API 활성화** (새 전용 프로젝트에서 필요). 방법은 둘 중 하나다.
   - 콘솔: https://console.cloud.google.com/apis/library/sheets.googleapis.com 에서 프로젝트를 선택하고 "사용(Enable)"을 누른다.
   - CLI: `gcloud services enable sheets.googleapis.com --project <프로젝트ID>`
2. **서비스 계정 생성.** https://console.cloud.google.com/iam-admin/serviceaccounts 에서 "서비스 계정 만들기"를 누른다. 프로젝트 역할은 주지 않아도 된다. Sheets 접근 권한은 시트 공유로 준다.
3. **키 발급.** 서비스 계정 → 키 → 키 추가 → JSON. 키 파일은 저장소 밖에 보관하고, 내용을 GitHub Secret `GOOGLE_SA_KEY`에 붙여 넣는다. **키 파일은 커밋하지 않고, 채팅에도 붙여 넣지 않는다.**
4. **스프레드시트 공유.** 본인 Google Drive에서 스프레드시트를 새로 만들고, 서비스 계정 이메일(`…@<프로젝트ID>.iam.gserviceaccount.com`)을 편집자로 공유한다.
5. **시트 ID 등록.** URL의 `/d/<시트ID>/` 부분을 Secret `PRICE_SHEET_ID`로 등록한다.

## 가격 확인 알림 (약관 준수)
| 대상 | 방식 | 이유 |
|---|---|---|
| Snowflake, Databricks | 분기 1회 "가격표 확인" Issue(공식 링크 + 체크리스트). 자동 접근은 하지 않는다 | 사이트 약관이 자동 모니터링을 금지한다 [확인] |
| BigQuery | 하루 1회 리전별 가격 문자열의 지문을 비교한다 | Google 약관은 robots.txt만 지키면 허용한다 [확인] |

## 사용자가 할 일
- 2-0의 GitHub 준비. 브라우저 승인과 설정 변경은 직접 해야 한다.
- 2-0c의 Google Sheets 준비. 키 발급과 Secret 등록은 직접 해야 한다.
- 초안 PR을 검토하고 머지한다. 머지가 곧 게시 승인이다.
- 분기마다 Snowflake·Databricks 가격을 확인하고, 바뀌었으면 수동 가격표를 PR로 고친다.

## 위험과 대응 (Phase 0에서 확인한 사항 포함)
| 위험 | 대응 |
|---|---|
| GITHUB_TOKEN으로 머지하면 다른 워크플로가 실행되지 않는다 | 사람이 머지하면 push로 트리거되는지 2-7에서 실측한다. 자동 모드(Phase 5)에서는 같은 실행 안에서 배포한다 |
| 공개 저장소는 60일 무활동이면 스케줄이 멈춘다 | 매일 스냅샷을 커밋하고, 재활성화 API를 보조 수단으로 둔다 |
| cron이 정각 혼잡으로 늦게 실행된다 | 00:17 UTC로 잡는다 |
| 새 저장소 기본값: 워크플로 PR 생성 금지, 토큰 읽기 전용 | 2-0에서 설정을 바꾼다 |
| gh 토큰에 `workflow` 권한이 없다 | `gh auth refresh -s workflow`를 실행하고, 사용자가 브라우저에서 승인한다 |
| 봇이 만든 PR의 CI는 승인이 필요하다(2026-06 변경) | 받아들인다 |
| 줄바꿈 CRLF/LF 불일치 | 2-0b에서 처리한다 |
| 서비스 계정 키 유출(만료 없는 비밀값) | Secret에만 보관한다. `.gitignore`에 키 파일 패턴을 추가하고, 커밋 전 검사 대상에 넣는다. 실제로 쓸 때(Phase 2)에 발급한다 |
| 시트 쓰기 실패(권한, 할당량) | 파이프라인은 계속 진행하고 Issue로 알린다. 할당량은 분당 수백 회 수준이라 하루 1건이면 충분하다 [지식] |

## 완료 기준 (게이트)
- 2-7 검증을 모두 통과한다(시트 적재 포함).
- 첫 실제 게시 전에 사용자가 확인한다.
- 위 두 가지가 끝나면 Phase 3을 결정하고 계획한다.
