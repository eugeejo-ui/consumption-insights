# Phase 0 점검 보고서

- 점검일: 2026-09-11
- 범위: CLAUDE.md의 0-1 ~ 0-8 (읽기 전용 점검. 저장소에 코드 없음)
- 표기: [확인] 직접 호출하거나 공식 문서·약관 원문에서 확인 / [지식] 모델 지식 / [미확인] 확인하지 못함

## 요약
| 항목 | 판정 | 막힘 / 대체 경로 |
|---|---|---|
| 0-1 로컬 환경 | 조건부 통과 | gh 토큰에 `workflow` 권한 없음, duckdb 미설치 |
| 0-2 AWS 가격 파일 | 통과 | 데이터 함정 있음 (선결제 금액이 시간당 단가처럼 들어 있음) |
| 0-3 Azure Databricks | 통과 | 클래식 SKU는 VM 비용이 별도 |
| 0-4 가격 페이지 변경 감지 | **Snowflake·Databricks: 약관상 막힘** / BigQuery: 통과 | 두 벤더는 자동 감지 대신 사용자가 주기적으로 직접 확인 |
| 0-5 LinkedIn | **약관상 막힘** | API 약관이 자동 게시를 금지한다 → 수동 게시 / 매번 직접 실행 / 제외 중 결정 필요 |
| 0-6 GitHub | 통과 | 저장소 설정 2개 필요(PR 생성 허용, 토큰 쓰기 권한). 사람이 머지할 때의 트리거는 Phase 2에서 실측 |
| 0-7 BigQuery 샌드박스 | 조건부 | 스토리지는 평생 10GiB이고 복구되지 않는다. 서비스 계정과 JOBS 조회는 Phase 4-4에서 실측 |

**가장 큰 발견:** 계획 v2에서 자동화하려던 외부 접근 두 곳이 기술이 아니라 **약관**에서 막혔다.
- LinkedIn 자동 게시
- Snowflake·Databricks 가격 페이지 자동 감시

두 곳 모두 "사람이 하는 단계"로 바꾸면 해결된다. 나머지 흐름(가격 수집 → TCO → 대시보드 → 아카이브 게시)은 그대로 진행할 수 있다.

---

## 0-1 로컬 환경: 조건부 통과
- Python 3.11.7 (Anaconda 기본 환경), pip 23.3.1, git 2.55.0, gh 2.100.0 (로그인됨) [확인]
- 설치된 패키지 [확인]: requests 2.31, pandas 2.1.4, pyarrow 14.0.2, jinja2 3.1.3, plotly 5.9.0, pyyaml 6.0.1, pytest 7.4.0
- **막힘 1: gh 토큰 권한이 `gist, read:org, repo`뿐이고 `workflow`가 없다** [확인]
  - 이 권한이 없으면 `.github/workflows/` 파일을 push할 때 거부된다 [지식].
  - 대체 경로: 사용자가 `gh auth refresh -s workflow`를 한 번 실행한다(브라우저 승인). Phase 2 전까지 하면 된다.
- **막힘 2: duckdb 미설치** [확인]
  - 대체 경로: Phase 1-0에서 설치한다.
  - Anaconda 기본 환경을 건드리지 않도록 프로젝트 전용 가상환경(venv)을 권장한다. Phase 1 계획에서 확정한다.

## 0-2 AWS 가격 파일: 통과
- 인증 없이 서비스별·리전별 파일을 받을 수 있다. 서울(ap-northeast-2)도 포함된다 [확인].
  - Redshift 리전 파일 0.12~0.13 MB (전체 4 MB)
  - S3 리전 파일 0.47~0.51 MB (전체 12.6 MB)
  - 전체 파일 대신 리전 파일만 받으면 된다.
- 온디맨드 가격 (offer 버전 20260910) [확인]

| 항목 | us-east-1 | 서울 | 서울 프리미엄 |
|---|---|---|---|
| Redshift Serverless (RPU-시간) | $0.375 | $0.438 | +16.8% |
| Redshift ra3.4xlarge (노드-시간) | $3.26 | $3.836 | +17.7% |
| Redshift 관리형 스토리지 (GB-월) | $0.024 | $0.0261 | +8.8% |
| S3 Standard 첫 50TB (GB-월) | $0.023 | $0.025 | +8.7% |

- **데이터 함정** [확인]
  - 1년 선결제 용량 예약(`ServerlessUsage-CR-1YR-AU`)이 OnDemand 항목 안에 "$2,430 per RPU-Hr"(서울 $2,839)로 들어 있다. 실제로는 시간당 단가가 아니라 선결제 금액이다.
    - usagetype을 정확히 `*Redshift:ServerlessUsage`로 거르지 않으면 월 비용이 수천 배로 튄다. 수집기 테스트 케이스로 넣는다.
  - Reserved의 All Upfront 옵션은 "시간당 $0 + 일시불(Quantity)"로 나뉘어 있다. 약정가를 계산할 때는 둘을 합산해야 한다.
  - usagetype 접두어가 리전마다 다르다(`USE1-`, `APN2-`, 미국 노드는 접두어 없음). 문자열을 정확히 일치시키지 말고 접미어로 매칭한다.

## 0-3 Azure Retail Prices API (Azure Databricks): 통과
- 인증 없이 조회된다. eastus 43개, koreacentral 41개 항목이 있고, Korea Central도 포함된다 [확인].
- DBU-시간 가격 [확인]

| SKU | eastus | koreacentral | 서울 프리미엄 |
|---|---|---|---|
| Premium Serverless SQL | $0.70 | $0.95 | +35.7% |
| Premium SQL Compute Pro | $0.55 | $0.74 | +34.5% |
| Premium Automated Serverless Compute | $0.45 | $0.50 | +11.1% |
| Premium Jobs Compute (클래식) | $0.30 | $0.30 | 0% |
| Premium All-purpose Compute (클래식) | $0.55 | $0.55 | 0% |

- **발견:** 클래식 DBU는 리전과 관계없이 가격이 같다. VM 비용이 따로 붙기 때문이다. 서버리스는 VM 비용이 포함돼 있어서 리전마다 다르다.
- **함정**
  - productName이 `Azure Databricks`(클래식)와 `Azure Databricks Regional`(서버리스)로 나뉜다.
  - 무료 체험·POC SKU(단가 $0)는 제외해야 한다.
  - 클래식을 비교하려면 VM 가격을 따로 조회해야 한다.
- **주의:** Azure Databricks 가격은 AWS 위 Databricks 직판 가격과 다르다. 다만 서버리스 SQL은 AWS 직판도 같은 값이다(아래 0-4).

## 0-4 가격 페이지 변경 감지: Snowflake·Databricks는 약관상 막힘, BigQuery는 가능
**Snowflake**
- robots.txt: 전체 허용이다. 가격 페이지와 소비표 PDF 모두 차단되지 않는다 [확인].
- **사이트 약관 5(i)** (2025-04-14 개정): 수동·자동 소프트웨어(스파이더, 로봇, 스크레이퍼, 크롤러 등)로 사이트를 스크랩·복사·**모니터링**하는 것을 금지하고, 예외가 없다 [확인, 원문 직접 확인].
- 기술적으로는 감지가 가능하다 [확인].
  - 가격 페이지 HTML에는 가격이 없고, 서비스 소비표 PDF로 연결된다.
  - PDF에 ETag와 Last-Modified가 있어서 HEAD 요청 한 번이면 감지할 수 있다. 약관 때문에 쓰지 않는다.
- 가격 (서비스 소비표 PDF, 2026-09-09 발효) [확인]
  - AWS US East: 크레딧당 Standard $2.00 / Enterprise $3.00, 스토리지 $23/TB-월
  - AWS 서울: 크레딧당 Standard $2.75 / Enterprise $4.05, 스토리지 $25/TB-월
  - 서울 행은 텍스트 추출에서 줄이 어긋난 적이 있다. **Phase 1-1에서 사용자가 PDF 원본으로 한 번 확인한다.**

**Databricks**
- robots.txt: 전체 허용이다 [확인].
- **이용약관** (2018-05-25): 로봇·크롤러·스크레이퍼 등 수동·자동 장치로 사이트 일부를 접근·복사·색인·스크랩·**모니터링**하는 것을 금지한다 [확인, 원문 직접 확인].
- 기술: 가격은 JavaScript가 `cards.json`(353KB)에서 불러온다. ETag가 있다 [확인].
- 가격 (AWS, DBU): SQL Serverless는 US East $0.70, 서울 $0.95다. Azure koreacentral 값과 같다 [확인].

**BigQuery**
- robots.txt: `/bigquery/pricing`은 차단되지 않는다 [확인].
- Google 약관(2026-07-30): robots.txt 같은 기계 판독 지침을 어기는 자동 접근만 금지한다. 지침을 지키면 허용된다 [확인].
- 기술 [확인]
  - 가격이 HTML에 들어 있고, 리전별 데이터도 내장돼 있다(4.5MB).
  - ETag가 없고, 보안 토큰(nonce)이 매번 바뀐다. 그래서 페이지 전체 해시가 아니라 **추출한 가격 문자열을 비교**한다.
- 가격 [확인]

| 항목 | US 멀티리전 | 서울 | 서울 프리미엄 |
|---|---|---|---|
| 온디맨드 (TiB, 월 1TiB 무료) | $6.25 | $7.50 | +20.0% |
| Standard 에디션 (슬롯-시간) | $0.04 | $0.051 | +27.5% |
| Enterprise 에디션 (슬롯-시간) | $0.06 | $0.0765 | +27.5% |

**대체 경로 (Snowflake·Databricks)**
- 두 사이트는 자동 감지를 폐기한다. 우리 자동화는 두 사이트에 접근하지 않는다.
- 대신 정해진 주기마다 "가격표 확인" 알림 Issue만 만든다(공식 링크 + 체크리스트).
- 사용자가 브라우저로 확인하고 수동 가격표를 PR로 고치면, 그 변경 자체가 E1 가격 변동 이벤트가 된다.
- 수동 가격표에 "확인일"을 두고, 대시보드에 "Snowflake 가격 확인일: YYYY-MM-DD"로 공개한다.
- 참고: 이번 점검에서 가격 확인을 위해 소비표 PDF와 `cards.json`을 1회 조회했다. 이 파일들은 임시 폴더에만 있고 저장소에는 없다. 약관을 확인한 이후로는 두 사이트에 자동으로 접근하지 않는다.

## 0-5 LinkedIn API 조건: 기술적으로는 가능, 약관상 막힘
- **약관 막힘** [확인]: LinkedIn API 약관 3.1조 26항은 "Use the Content or the APIs to automate posting on the LinkedIn Services."를 금지한다. 회원이 시작하거나 승인한 게시를 예외로 두는 조항은 없다 (https://www.linkedin.com/legal/l/api-terms-of-use, 2022-12-13 개정).
  - 계획 v2의 Phase 5 "완전 자동 게시"는 이 조항과 정면으로 충돌한다.
  - 게시마다 승인을 받는 방식도 허용된다는 근거가 없어서 회색지대다.
- 기술 조건 [확인]
  - 개발자 앱에는 LinkedIn 페이지를 반드시 연결해야 한다. 페이지는 무료로 만들 수 있고, 만든 사람이 슈퍼 관리자로서 앱을 직접 인증할 수 있다.
  - Share on LinkedIn(`w_member_social`)과 OpenID Connect(`openid profile`)는 심사 없이 셀프서비스로 쓸 수 있다. 작성자 URN은 `/v2/userinfo`로 얻는다.
  - 토큰은 60일마다 만료된다. 갱신 토큰은 승인된 파트너만 받을 수 있어서 60일마다 브라우저로 직접 재발급해야 한다.
  - 엔드포인트는 `POST /rest/posts`이고, 헤더 `Linkedin-Version: YYYYMM`이 필요하다. 버전은 매달 나오고 각 버전은 최소 1년 지원된다(202508은 2026-08-17 종료).
  - 한도: 회원당 하루 150회, 앱당 하루 100,000회
- [미확인] 앱 인증(Verify)이 Share on LinkedIn에 필수인지, Share on LinkedIn 권한만으로 `/rest/posts`를 호출할 수 있는지는 문서에 명시돼 있지 않다.
- **추가 확인 (사용자 지시 "aside cli로 API 따서 진행" 검토, 2026-09-11)**
  - Aside는 로그인된 실제 브라우저를 CLI로 조종하는 자동화 플랫폼이다 [확인] (https://aside.com/blog/developers).
  - LinkedIn **사용자 약관**(2025-11-03 시행)의 금지 항목 [확인] (https://www.linkedin.com/legal/user-agreement)
    - 13번: "Use bots or other unauthorized automated methods to access the Services … create, comment on, like, share, or re-share posts"
    - 이 밖에 스크래핑 도구 사용(2번), 접근 통제 우회(3번)도 금지한다.
  - 결론: 브라우저 자동화로 게시하는 방식은 API 약관과 별개로 사용자 약관 13번에 해당한다. 위험은 **사용자의 실제 LinkedIn 계정 제한**이다.
    - Claude는 이 방식(세션을 이용한 자동 게시)을 구현하지 않는다.
  - Snowflake·Databricks도 마찬가지다. 두 약관 모두 "수동 또는 자동" 도구로 모니터링하는 것을 금지하므로, 브라우저 자동화 도구를 써도 결론이 같다.
    - 사용자가 지정한 대체안(분기 1회 확인)을 적용한다.
- **대체 경로 후보**
  - A'. 공식 공유 링크(반자동, 추천): 게시 PR에 LinkedIn 게시문과 공식 공유 링크(`linkedin.com/sharing/share-offsite/?url=…`)를 함께 넣는다 [지식]. 사용자가 링크를 누르고 붙여 넣은 뒤 직접 게시한다. 약관 위험도, 토큰 관리도 없다.
  - A. 수동 게시(API 없음): 자동화는 LinkedIn용 게시문과 링크까지만 만들고, 게시는 사용자가 복사해 붙여 넣는다. 약관 위험도, 60일 토큰 관리 부담도 없다.
  - B. API를 쓰되 게시마다 사용자가 직접 실행: 사용자가 누를 때만 게시한다. 회색지대이고 60일 토큰 관리가 필요하다.
  - C. LinkedIn 제외: 웹 아카이브만 운영한다.

## 0-6 GitHub (60일 규칙, Pages, GITHUB_TOKEN): 통과, 저장소 설정 2개 필요
- **Pages** [확인]: Free 플랜에서는 공개 저장소에서만 쓸 수 있다. Actions 워크플로(`actions/deploy-pages`)로 배포할 수 있고, `pages: write`와 `id-token: write` 권한이 필요하다. 사이트 크기 한도는 1GB다. (docs.github.com, githubs-plans / github-pages-limits)
- **Actions 요금** [확인]: 공개 저장소는 표준 러너가 무료다. 스케줄 실행은 부하가 높을 때 늦어지고, 매시 정각이 특히 혼잡하다. 계획대로 정각을 피한다.
- **60일 규칙** [확인]: 공개 저장소에만 적용되지만, 문서에 "활동"의 정의가 없다.
  - [미확인] 봇 커밋이 활동으로 인정된다는 정황은 있으나 공식 답변은 없다.
  - 대응: 매일 스냅샷 커밋을 main에 쌓는다. 보조 수단으로 워크플로 재활성화 API(`actions: write`)를 둔다.
- **GITHUB_TOKEN이 일으킨 이벤트** [확인]: 새 워크플로를 실행시키지 않는다.
  - 예외는 `workflow_dispatch`와 `repository_dispatch`다.
  - 2026-06-11부터 봇이 만든 PR도 `pull_request` 워크플로를 실행할 수 있게 됐다. 단, 쓰기 권한을 가진 사람이 승인해야 한다.
  - 워크플로가 GITHUB_TOKEN으로 머지하면 push 워크플로는 실행되지 않는다. 그래서 자동 게시 모드에서는 같은 실행 안에서 배포하거나 `workflow_dispatch`를 호출한다.
  - [미확인] 사람이 머지하면 push 워크플로가 실행돼야 맞지만, 반대 사례 보고도 있다. Phase 2-7에서 한 번 실측한다.
- **저장소 설정 필요** [확인]: 새 개인 저장소는 기본값이 두 가지 막혀 있다.
  1. 워크플로의 PR 생성과 승인이 금지돼 있다.
  2. GITHUB_TOKEN이 읽기 전용이다.
  - 대응: (U) Settings > Actions > General에서 둘 다 허용한다. Phase 2-0에 추가한다.

## 0-7 BigQuery 샌드박스: 조건부 (Phase 4-4에서 실측)
- 공식 문서 확인 사항 [확인] (docs.cloud.google.com/bigquery/docs/sandbox)
  - **스토리지는 평생 10GiB이고, 데이터를 삭제해도 한도가 돌아오지 않는다.**
    - 원문: "lifetime limit of 10 GiB of storage. This quota is not refunded upon data deletion."
  - 쿼리는 매월 1TiB까지 무료다.
  - 모든 테이블·뷰·파티션은 60일 뒤 만료된다.
  - 지원되지 않는 기능: 스트리밍, DML, Data Transfer Service
- 쿼리 과금 [확인] (bigquery/pricing, dry-run, cached-results 문서)
  - 쿼리마다, 그리고 참조하는 테이블마다 최소 10MB가 과금된다.
  - dry run은 무료다.
  - 캐시 적중 쿼리와 실패한 쿼리는 과금되지 않는다. 캐시는 `use_query_cache=False`로 끈다.
- JOBS 뷰 [확인]
  - `JOBS`와 `JOBS_BY_PROJECT`는 같은 뷰다.
  - 최근 180일치를 보관한다. 조회할 때 `` `region-us` `` 같은 리전 한정자가 필요하다.
  - 필요한 컬럼(total_bytes_billed, total_bytes_processed, total_slot_ms, cache_hit)이 모두 있다.
- [미확인] 샌드박스에서 JOBS 뷰 조회, CTAS·파티션·클러스터 테이블 생성, 서비스 계정 키 사용이 되는지는 문서에 없다. 한 벤더 문서는 결제 계정이 필요하다고 한다.
- **H5 설계에 미치는 영향**
  - V3(클러스터 사본)와 V4(사전 집계) 테이블을 매일 다시 만들면, 평생 스토리지 한도를 반복해서 써 버린다.
  - 따라서 사본 테이블은 작게(수백 MB) 한 번만 만들고, 60일 만료 때만 다시 만든다.
  - 그래도 한도가 부족하면 결제 계정을 연결해 무료 등급으로 전환하는 방안이 있다(스토리지 월 10GiB 무료). 다만 카드 등록이 필요하다.
  - Phase 4 계획에서 결정한다.

---

## T2 초기 신호 (정식 판정은 Phase 1)
점검 과정에서 모은 공시 가격만으로도 서울 프리미엄이 서비스마다 크게 다르다는 신호가 보인다.

| 구분 | 서울 프리미엄 |
|---|---|
| Databricks 클래식 DBU (VM 별도) | 0% |
| 스토리지 (S3, Redshift 관리형, Snowflake) | +8.7 ~ +8.8% |
| Redshift 컴퓨트 (서버리스, ra3) | +16.8 ~ +17.7% |
| BigQuery 온디맨드 / 에디션 | +20.0% / +27.5% |
| Databricks 서버리스 SQL | +35.7% |
| Snowflake 크레딧 (Enterprise / Standard) | +35.0% / +37.5% (서울 행 재확인 필요) |

패턴(가설 아님, 관찰): 스토리지는 약 9%, 관리형 컴퓨트는 17~38%로, 컴퓨트 쪽 프리미엄이 훨씬 크다.

## 결정이 필요한 사항
1. **LinkedIn 처리 방식** (0-5): A 수동 게시 / B API + 매번 직접 실행 / C 제외
2. **Snowflake·Databricks 가격 확인 주기** (0-4): 자동 감지 대신 알림 Issue를 보내는 주기

## Phase 1 전후 사용자 할 일
- Phase 1-1: Snowflake 소비표 PDF의 서울 가격 행을 원본으로 확인
- Phase 2 전: `gh auth refresh -s workflow` 실행, 저장소 Settings > Actions > General에서 PR 생성 허용 및 토큰 쓰기 권한 설정
- Phase 4 전: 개인 Gmail로 BigQuery 샌드박스 준비
