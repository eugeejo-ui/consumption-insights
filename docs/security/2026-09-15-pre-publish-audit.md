# 게시 전 보안 점검 (2026-09-15)

| 항목 | 내용 |
|---|---|
| 계기 | 첫 LinkedIn 게시(3-10) 전에 공개 저장소와 공개 사이트에 보안 문제가 없는지 확인하라는 사용자 지시 |
| 범위 | 저장소의 현재 파일과 **전체 이력**, 커밋 메타데이터, 공개 Issue·PR·코멘트, 워크플로 실행 로그, 공개 사이트, 워크플로 설정, 저장소 설정, Google Cloud 워크로드 아이덴티티 |
| 방식 | 모두 읽기 전용으로 확인했다. 비밀값·개인정보 패턴 검사는 양성 대조(가짜 값 7종이 모두 걸리는지)로 검사기 자체를 먼저 확인했다 |
| 원칙 | 이 문서에는 이메일 주소, 프로젝트 ID, 시트 ID 같은 실제 값을 적지 않는다(규칙 6·11) |

## 결과 요약

| # | 발견 | 심각도 | 처리 |
|---|---|---|---|
| 1 | **머지 커밋 2개의 작성자 이메일이 GitHub noreply가 아니라 개인 이메일이다** (PR #3, #7을 사용자 계정 토큰으로 머지하며 생겼다) | 중간(개인정보) | 재발 방지는 사용자 계정 설정이 필요하다. 기존 커밋 처리는 사용자 결정 |
| 2 | 워크플로 실행 로그 3건에 서비스 계정 주소와 워크로드 아이덴티티 경로(프로젝트 번호 포함)가 보인다. 저장소 **변수**(`vars`)는 로그에서 가려지지 않는다 | 낮음(식별자, 인증 수단 아님) | 사용자 결정(변수를 Secret으로 옮기기, 옛 로그 삭제) |
| 3 | 게시 워크플로가 워크플로 전체에 `id-token: write`를 줘서, pip 설치와 테스트가 도는 build 작업도 OIDC 토큰을 받을 수 있었다 | 낮음 | **코드로 고쳤다.** 작업별 최소 권한 |
| 4 | 액션을 태그(`@v7`)로 불러, 태그가 옮겨지면 다른 코드가 돈다. 그중 `google-github-actions/auth`는 OIDC 토큰을 다룬다 | 낮음 | **코드로 고쳤다.** 모든 액션을 커밋 SHA로 고정 |
| 5 | `sheets-baseline.yml`이 수동 실행 입력을 식(`${{ inputs.day }}`)으로 셸에 넣는다(실행 권한은 저장소 소유자뿐) | 낮음 | **코드로 고쳤다.** 환경변수로 넘긴다 |
| 6 | 저장소 설정 4건(점검 2026-09-12부터 결정 대기): 기본 토큰 권한 write, 워크플로의 PR 승인 허용, 액션 SHA 고정 미요구, main 보호 없음. Dependabot 알림 꺼짐 | 낮음~중간 | 사용자 설정 변경(아래 권장값) |

**문제없음으로 확인한 것 [확인]**

| 항목 | 결과 |
|---|---|
| 비밀값(개인 키, 서비스 계정 키 JSON, GitHub·Google·AWS 토큰, 비밀번호 대입) | 전체 이력의 객체 1,089개에서 0건 |
| 이메일·로컬 사용자 경로·서비스 계정 주소·시트 주소·전화번호(파일 내용) | 0건. 허용한 것은 GitHub noreply와 커밋 서명용 noreply뿐 |
| 커밋 메시지 | 개인 이메일 0건 |
| 추적 파일 | `.env`, 키, `secrets/`, `_workspace/`(템플릿 원본), `.claude/` 없음 |
| 공개 Issue 8건·코멘트 4건 | 개인정보·식별자 0건 |
| 공개 사이트(대시보드, 소개 카드 HTML·게시문) | 0건 |
| 카드 PDF·PNG 메타데이터 | PDF: 제목 `cards`, 생성 브라우저 식별 문자열(운영체제·브라우저 버전)만 있다. PNG: 글자 메타데이터 없음 |
| Google Cloud 워크로드 아이덴티티 | 조건이 이 저장소(`assertion.repository`)로 한정된다. 서비스 계정을 가장할 수 있는 주체는 이 저장소뿐이다. 사용자 관리 키 0개. 프로젝트 역할 없음(시트 공유만) |
| 저장소 | 비밀값 스캔과 푸시 보호가 켜져 있다. 협업자는 소유자 1명. 배포 키·웹훅 0개. Pages 환경에 브랜치 정책이 있다 |
| 워크플로 권한 | 다섯 워크플로 모두 권한을 명시한다. 포크 PR에서 도는 쓰기 작업이 없다(`revise.yml`은 같은 저장소 브랜치로 한정) |

## 코드로 고친 것 (발견 3~5)

| 파일 | 변경 |
|---|---|
| `.github/workflows/publish.yml` | 워크플로 기본 권한을 `contents: read`로 낮췄다. build `contents: write`(승인 기록 push), deploy `pages: write`·`id-token: write`(deploy-pages README의 최소 권한), log `contents: read`·`id-token: write`·`issues: write` |
| 모든 워크플로 | `actions/checkout` v7.0.1, `actions/setup-python` v7.0.0, `actions/upload-pages-artifact` v5.0.0, `actions/deploy-pages` v5.0.1, `google-github-actions/auth` v3.0.0을 커밋 SHA로 고정하고 버전을 주석으로 남겼다 |
| `.github/workflows/sheets-baseline.yml` | 입력값을 환경변수 `DAY`로 넘긴다 |
| `tests/test_workflows.py` | 테스트 1개 추가: 모든 워크플로가 권한을 명시하고, 모든 액션이 SHA로 고정되고, OIDC 권한이 인증 작업 3곳(게시 deploy·log, 기준선)에만 있고, 사람 입력이 식으로 셸에 들어가지 않는다. 옛 워크플로로 돌리면 실패한다 [확인] |

## 사용자가 해야 하는 것

설정 변경과 비밀값 입력, 영구 삭제는 사용자가 직접 한다(규칙 4·12).

| # | 조치 | 위치 | 이유 |
|---|---|---|---|
| U1 | **"Keep my email addresses private"** 켜기, 가능하면 "Block command line pushes that expose my email"도 켜기 | GitHub → Settings → Emails | 웹·API 머지 커밋이 noreply 주소로 기록된다 [지식]. 켜기 전까지 Claude는 `gh pr merge`로 머지하지 않는다 |
| U2 | 기존 머지 커밋 2개 처리 결정 | — | 아래 "발견 1의 선택지" |
| U3 | 기본 토큰 권한을 **Read repository contents and packages permissions**로 바꾸기 | Settings → Actions → General → Workflow permissions | 모든 워크플로가 권한을 명시하므로 read로 바꿔도 동작한다 [확인, 테스트]. 같은 화면의 "Allow GitHub Actions to create and approve pull requests"는 **켠 채로 둔다.** 생성과 승인이 한 체크박스라, 끄면 수집 워크플로가 검토 PR을 만들지 못한다. main 보호(U5)와 소유자 1인 구조에서 승인 권한의 실질 위험은 작다 |
| U4 | **Require actions to be pinned to a full-length commit SHA** 켜기 | Settings → Actions → General | 이번 수정으로 모든 액션이 고정됐다. 이 수정을 push한 뒤에 켠다 |
| U5 | main 규칙: **force push 차단, 삭제 차단**만 켜기(PR 필수는 켜지 않는다) | Settings → Rules → Rulesets | 봇이 main에 직접 커밋한다(매일 확인 기록, 승인 기록, 가격 지문). PR 필수를 켜면 자동화가 멈춘다. U2에서 이력 재작성을 고르면 그 뒤에 켠다 |
| U6 | Dependabot alerts 켜기 | Settings → Code security | 의존성 취약점 알림 |
| U7 (선택) | 변수 `GCP_WIF_PROVIDER`, `GCP_SERVICE_ACCOUNT`를 **Secret으로 옮기기**. 옮긴 뒤 Claude가 워크플로의 `vars.`를 `secrets.`로 바꾼다 | Settings → Secrets and variables | Secret은 로그에서 가려진다. 순서가 바뀌면 인증이 깨진다 |
| U8 (선택) | 식별자가 보이는 옛 실행 로그 3건 삭제 | Actions → 해당 실행 → Delete workflow run | 영구 삭제라 사용자가 직접 한다 |
| U9 (선택) | 워크로드 아이덴티티 조건에 main 브랜치 한정(`assertion.ref=='refs/heads/main'`) 추가 | Google Cloud IAM | 저장소 안의 다른 브랜치 실행이 서비스 계정을 쓰지 못하게 한다. 지금은 소유자만 브랜치를 만들 수 있다 |

### 발견 1의 선택지

| 안 | 내용 | 대가 |
|---|---|---|
| **A. 설정만 켜고 기존 커밋은 둔다** | 재발을 막는다 | 기존 머지 커밋 2개에 주소가 남는다. 2026-09-12부터 공개돼 있었다 |
| B. main 이력을 다시 쓴다 | 두 커밋의 작성자를 noreply로 바꾸고 강제 push한다 | 첫 대상 뒤 커밋 60개의 해시가 모두 바뀐다(문서의 해시 참조 수십 곳 수정). 공개 main에 강제 push한다. PR #3·#7 화면은 원래 머지 커밋을 계속 가리키고, GitHub는 참조가 끊긴 커밋도 해시로 한동안 열어 준다 [지식]. 완전히 지우려면 GitHub 지원팀 요청이 필요하다 |
