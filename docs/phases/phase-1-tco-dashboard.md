# Phase 1: 가격 수집 + TCO 모델 + 정적 대시보드

| 항목 | 내용 |
|---|---|
| 상태 | **진행 중**: Task 1~4 완료(Task 4는 BigQuery 컴퓨트 4행 확인 대기), **Task 5 코드 완료. 사용자 가정 검토 대기** (2026-09-11) |
| 목표 | 로컬에서 명령 한 번으로 플랫폼 4개 × 리전 2개의 가격을 모으고, 워크로드 3개의 월 비용을 추정해 `site/index.html`을 만든다 |
| 선행 조건 | Phase 0 완료 |
| 코드 단위 계획 | `docs/plans/phase1-tco-dashboard.md` (테스트와 구현 코드 전문) |
| 진행 규칙 | Task는 하나씩 진행하고, 끝나면 보고한 뒤 지시를 기다린다 (CLAUDE.md 규칙 10) |

## 이 Phase에서 답하려는 질문
- **T1:** 워크로드마다 월 비용 1위 플랫폼이 다른가? 가정을 ±50% 흔들어도 1위가 그대로인가?
- **T2:** 서울 리전 추가 비용(서울 프리미엄)이 서비스마다 다른가? 기준은 최대값과 최소값의 차이가 10%p 이상인가이다.

## 데이터 흐름
```
AWS 가격 파일 ──┐
Azure API ──────┼─→ PriceRecord(공통 스키마) → data/raw/<날짜>/*.csv → model/tco.py → publish/render_site.py → site/index.html
수동 가격표 ────┘                                                     ↑
                                                         data/manual/workloads.yaml (가정)
                                                         config/thresholds.yaml (판정 기준)
```

| 플랫폼 | 가격 출처 | 방식 | US / 서울 | 확인 상태 |
|---|---|---|---|---|
| Redshift | AWS 가격 파일 | 자동 | RPU-시간 $0.375 / $0.438, 스토리지 GB-월 $0.024 / $0.0261 | Task 2 실제 조회 [확인] |
| Databricks | Azure Retail API | 자동 | 서버리스 SQL DBU $0.70 / $0.95, ADLS GB-월 $0.0208 / $0.02 | Task 3 실제 조회 [확인] |
| Snowflake | 서비스 소비표 PDF | 수동 | Enterprise 크레딧 $3.00 / $4.05, 스토리지 TB-월 $23 / $25 | **사용자 확인 2026-09-11** (4행 전부) |
| BigQuery 스토리지 | 가격 페이지 | 수동 | Active logical GiB-월 $0.02 / $0.023 | **사용자 확인 2026-09-11** |
| BigQuery 컴퓨트 | 가격 페이지 | 수동 | Enterprise 슬롯-시간 $0.06 / $0.0765, 온디맨드 TiB $6.25 / $7.50 | **확인 대기** (`confirmed_on` 비어 있음) |

**BigQuery 가격표 참고 사항**
- **스토리지 단위 변환:** 가격 페이지는 스토리지를 **GiB-시간** 단위로 표시한다. US(us)는 $0.000027397, 서울은 $0.000031507이다. 가격표에는 730시간/월을 곱한 GiB-월 값으로 적었다. US는 $0.0200, 서울은 $0.0230이다.
- **리전 이름:** 페이지의 리전 이름은 "US (multi-region)"가 아니라 "US (us)"다.
- **무료 구간:** 매월 10GiB 무료 구간이 있지만 TCO 모델에서는 제외한다.
- **컴퓨트 4행을 찾는 위치:**

  | 가격표 행 | 페이지 섹션 | 볼 곳 | 미국 / 서울 |
  |---|---|---|---|
  | 온디맨드 | **주문형 컴퓨팅 가격 책정**(On-demand compute pricing) | 쿼리 행의 "1 TiB 이상" | $6.25 / $7.50 per TiB |
  | 슬롯 | **용량 컴퓨팅 가격 책정**(Capacity compute pricing) | **Enterprise 버전 / 종량제(Pay as you go)** 열 | $0.06 / $0.0765 per slot-hour |

  - 슬롯 행에서 1년·3년 약정 열과 헷갈리지 않도록 주의한다.
  - 페이지 데이터로 본 Enterprise 가격은 US $0.06 / $0.048 / $0.036, 서울 $0.0765 / $0.0612 / $0.0459다(종량제 / 1년 / 3년 순).

## 진행 과정
| Task | 작업 | 담당 | 산출물 | 완료 기준 | 상태 |
|---|---|---|---|---|---|
| 1 | 뼈대 + 공통 스키마 | C | `requirements.txt`, `pytest.ini`, `.gitignore`, `common/schema.py` | 테스트 3개 통과, 첫 커밋 | **완료** (`d5930d1`) |
| 2 | AWS Redshift 수집기 | C | `collectors/aws_prices.py`, 픽스처 | 테스트 3개 통과, 실제 조회값이 Phase 0 값과 같음 | **완료** (`0c5b6c9`) |
| 3 | Azure 수집기 (Databricks, ADLS) | C | `collectors/azure_prices.py`, 픽스처 | 테스트 3개 통과, 실제 조회값 확인 | **완료** (`4e2ef6c`) |
| 4 | 수동 가격표 + 확인 게이트 | C+U | `collectors/manual_prices.py`, `data/manual/*_prices.csv` | 테스트 4개 통과, 사용자가 `confirmed_on` 입력 | **코드 완료** (`c8da16f`). 확인 10행 중 6행 완료, BigQuery 컴퓨트 4행 대기 |
| 5 | 워크로드 가정 + 월 비용 계산 | C+U | `data/manual/workloads.yaml`, `model/tco.py`, `tests/conftest.py` | 테스트 7개 통과(W1 손계산 $1,550 포함), 사용자 가정 검토 | **코드 완료**. 가정 검토 대기 |
| 6 | T1·T2 판정 | C | `config/thresholds.yaml`, 판정 함수 | 테스트 6개 통과 | **다음** |
| 7 | 정적 대시보드 | C | `publish/render_site.py`, `templates/site/index.html.j2` | 테스트 1개 통과 | 대기 |
| 8 | 파이프라인 + 실제 실행 | C+U | `pipeline.py`, 첫 가격 스냅샷 | 전체 테스트 28개 통과, 사용자 화면 확인 | 대기. BigQuery 4행이 확인돼야 실행된다 |

Task마다 순서는 같다: 테스트 작성 → 실패 확인 → 구현 → 통과 확인 → 로컬 커밋.

## 사용자가 할 일 (시점별)
| 시점 | 할 일 |
|---|---|
| Task 4 (남음) | BigQuery 가격 페이지(https://cloud.google.com/bigquery/pricing)에서 컴퓨트 4행을 확인한다. 위치는 위 표에 있다(주문형 섹션 1행, 용량 섹션의 Enterprise 종량제 1행, 각각 US(us)와 서울). Task 8 전까지 `confirmed_on`을 채운다 |
| Task 5 (지금) | `data/manual/workloads.yaml`의 가정을 검토한다: small 1단위의 정의, 시나리오 시간과 규모, W3 스캔 속도, 스토리지 10TB, 에디션 |
| Task 8 | `site/index.html` 화면을 확인하고, 자동 수집한 가격 3개를 공식 페이지와 대조한다 |

## 핵심 가정 (결과를 좌우한다. `data/manual/workloads.yaml`)
- **small 1단위:** Snowflake 시간당 2크레딧 / Databricks 시간당 12 DBU / Redshift 8 RPU / BigQuery 100슬롯
- **시나리오:**
  - W1: small×1로 월 220시간
  - W2: small×2로 월 60시간
  - W3: 월 20TiB 스캔. BigQuery는 온디맨드로 과금하고, 나머지는 small×4가 시간당 2TiB를 스캔한다고 보고 10시간으로 계산한다
- **스토리지:** 10TB
- **제외 항목:** 네트워크 송출, 무료 등급, 최소 과금 단위, 약정 할인
- **미리보기 결과** (확인된 가격 + 확인 대기 중인 BigQuery 컴퓨트 값으로 계산)
  - W1·W2는 Redshift, W3은 BigQuery가 가장 싸다. 미국과 서울 모두 같다.
  - T1 판정(±50% 민감도)은 Task 6에서 한다.

## 위험과 대응
| 위험 | 대응 |
|---|---|
| 실제 가격이 Phase 0 확인값과 다름 | Task 2·3의 실제 조회 단계에서 보고한다. 가격 변동은 Phase 2의 E1 이벤트 후보다. Task 2(AWS)와 Task 3(Azure) 모두 값이 같았다 |
| AWS 파일의 선결제 항목이 단가로 섞임 | usagetype 접미어를 정확히 맞추고, 함정을 넣은 테스트로 막는다. 실제 데이터에서도 걸러지는 것을 확인했다 |
| Azure의 0원 체험·POC SKU, 클래식 SKU, 스토리지 구간이 섞임 | 상품명·SKU명·구간 조건을 정확히 맞추고, 함정을 넣은 테스트로 막는다 |
| 수동 가격을 잘못 입력 | `confirmed_on`이 없으면 실행이 멈춘다. 실제 가격표에서 게이트가 동작하는 것도 확인했다(BigQuery 2행째에서 중단) |
| 단위 변환 실수(GiB-시간 → GiB-월, GB ↔ GiB, TB ↔ GB) | 730시간/월, 1GiB = 1.073741824GB, 1TB = 1000GB로 고정하고, 테스트로 확인한다(`test_gib_storage_is_converted_from_gb`) |
| 가정 하나가 결론을 바꿈 | ±50% 민감도 라벨을 붙이고(Task 6), 가정 전체를 화면에 공개한다 |
| plotly 7.0 설치 (계획은 5.x 기준) | 필요한 API의 호환성을 확인했다 |

## 완료 기준 (게이트)
- pytest 28개 통과
- 사용자가 `site/index.html`을 확인
- CLAUDE.md 갱신
- 위 세 가지가 끝나면 Phase 2 코드 단위 계획을 작성하고 승인을 받는다

## 진행 기록
- **2026-09-11 Task 1 완료:** venv, git init, 공통 스키마를 만들었다. 테스트 3개가 통과했다. 첫 커밋 `d5930d1`은 이 저장소 전용 noreply 이메일로 했다.
- **2026-09-11 Phase별 진행계획 문서화:** 이 파일을 포함해 `docs/phases/` 6개 파일을 만들었다(커밋 `6e8c670`).
- **2026-09-11 Task 2 완료** (커밋 `0c5b6c9`)
  - 순서: 테스트 작성 → 실패 확인(`collectors` 모듈 없음) → `collectors/aws_prices.py` 구현
  - 테스트: Task 2의 3개 통과, 누적 6개 통과
  - 실제 AWS 조회값이 Phase 0 확인값과 같다 [확인].

    | | 미국 | 서울 |
    |---|---|---|
    | 서버리스 RPU (RPU-시간) | $0.375 | $0.438 |
    | 관리형 스토리지 (GB-월) | $0.024 | $0.0261 |
  - 선결제 항목(`-CR-1YR-AU`, "RPU-시간당 $2,430"으로 표기)이 실제 데이터에서도 걸러졌다.
- **2026-09-11 Task 3 완료** (커밋 `4e2ef6c`)
  - 순서: 테스트 작성 → 실패 확인(`collectors.azure_prices` ImportError) → `collectors/azure_prices.py` 구현
  - 테스트: Task 3의 3개 통과, 누적 9개 통과
  - 실제 Azure 조회값이 Phase 0 확인값과 같다 [확인].

    | | 미국 (eastus) | 서울 (koreacentral) |
    |---|---|---|
    | Databricks 서버리스 SQL (DBU-시간) | $0.70 | $0.95 |
    | ADLS Gen2 Hot LRS 첫 구간 (GB-월) | $0.0208 | $0.02 |
  - 0원 체험·POC SKU, 클래식 SQL SKU($0.22), 51,200GB 이상 스토리지 구간이 테스트로 걸러진다.
- **2026-09-11 Task 4 코드 완료** (커밋 `c8da16f`)
  - 순서: 테스트 작성 → 실패 확인(ImportError) → `collectors/manual_prices.py`와 가격표 2개 작성
  - 테스트: Task 4의 4개 통과, 누적 13개 통과
  - 사용자 확인 결과
    - Snowflake: Enterprise 크레딧 $3.00 / $4.05, 스토리지 $23 / $25(TB-월). 모두 맞다.
    - BigQuery 스토리지: 페이지값 $0.000027397 / $0.000031507(GiB-시간)에 730을 곱해 $0.02 / $0.023(GiB-월). 맞다.
  - BigQuery 컴퓨트 4행은 아직 확인하지 않아서 `confirmed_on`을 비워 두었다. 실제 가격표를 읽으면 이 행에서 게이트가 멈추는 것을 확인했다.
- **2026-09-11 Task 5 코드 완료**
  - 순서: `workloads.yaml`, 공통 픽스처(`tests/conftest.py`), 테스트 작성 → 실패 확인(ImportError) → `model/tco.py` 구현
  - 테스트: Task 5의 7개 통과, 누적 20개 통과
  - 테스트로 검증한 것
    - W1 Snowflake 손계산($1,320 + $230 = $1,550)
    - W3 BigQuery 온디맨드(20TiB × $6.25)
    - W3 용량형 플랫폼의 스캔량 → 시간 환산
    - GiB 변환
    - 가격이 빠지면 오류 메시지에 빠진 항목이 나오는지
  - 미리보기 결과: W1·W2는 Redshift, W3은 BigQuery가 가장 싸다(미국·서울 모두).
  - 사용자 가정 검토를 기다린다.
