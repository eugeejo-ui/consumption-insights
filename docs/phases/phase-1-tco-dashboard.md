# Phase 1: 가격 수집 + TCO 모델 + 정적 대시보드

| 항목 | 내용 |
|---|---|
| 상태 | **진행 중**: Task 1~3 완료, Task 4 대기 (2026-09-11) |
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

| 플랫폼 | 가격 출처 | 방식 | US / 서울 (Phase 0 확인값) |
|---|---|---|---|
| Redshift | AWS 가격 파일 | 자동 | RPU-시간 $0.375 / $0.438, 스토리지 GB-월 $0.024 / $0.0261 (Task 2에서 실제 조회로 재확인) |
| Databricks | Azure Retail API | 자동 | 서버리스 SQL DBU $0.70 / $0.95, ADLS GB-월 $0.0208 / $0.02 (Task 3에서 실제 조회로 재확인) |
| Snowflake | 서비스 소비표 PDF | 수동(사용자 확인) | Enterprise 크레딧 $3.00 / $4.05, 스토리지 TB-월 $23 / $25 |
| BigQuery | 가격 페이지 | 수동(사용자 확인) | Enterprise 슬롯-시간 $0.06 / $0.0765, 온디맨드 TiB $6.25 / $7.50, 스토리지 GiB-월 $0.02 / $0.023 |

## 진행 과정
| Task | 작업 | 담당 | 산출물 | 완료 기준 | 상태 |
|---|---|---|---|---|---|
| 1 | 뼈대 + 공통 스키마 | C | `requirements.txt`, `pytest.ini`, `.gitignore`, `common/schema.py` | 테스트 3개 통과, 첫 커밋 | **완료** (`d5930d1`) |
| 2 | AWS Redshift 수집기 | C | `collectors/aws_prices.py`, 픽스처 | 테스트 3개 통과, 실제 조회값이 Phase 0 값과 같음 | **완료** (`0c5b6c9`) |
| 3 | Azure 수집기 (Databricks, ADLS) | C | `collectors/azure_prices.py`, 픽스처 | 테스트 3개 통과, 실제 조회값 확인 | **완료** |
| 4 | 수동 가격표 + 확인 게이트 | C+U | `collectors/manual_prices.py`, `data/manual/*_prices.csv` | 테스트 4개 통과, 사용자가 `confirmed_on` 입력 | **다음** |
| 5 | 워크로드 가정 + 월 비용 계산 | C+U | `data/manual/workloads.yaml`, `model/tco.py` | 테스트 7개 통과(W1 손계산 $1,550 포함), 사용자 가정 검토 | 대기 |
| 6 | T1·T2 판정 | C | `config/thresholds.yaml`, 판정 함수 | 테스트 6개 통과 | 대기 |
| 7 | 정적 대시보드 | C | `publish/render_site.py`, `templates/site/index.html.j2` | 테스트 1개 통과 | 대기 |
| 8 | 파이프라인 + 실제 실행 | C+U | `pipeline.py`, 첫 가격 스냅샷 | 전체 테스트 28개 통과, 사용자 화면 확인 | 대기 |

Task마다 순서는 같다: 테스트 작성 → 실패 확인 → 구현 → 통과 확인 → 로컬 커밋.

## 사용자가 할 일 (시점별)
| 시점 | 할 일 |
|---|---|
| Task 4 | 본인 브라우저로 Snowflake 소비표 PDF(서울 행)와 BigQuery 가격 페이지(스토리지)를 확인하고 `confirmed_on`에 날짜를 적는다 |
| Task 5 | `workloads.yaml`의 가정을 검토한다: small 1단위의 정의, 시나리오 시간, 에디션 |
| Task 8 | `site/index.html` 화면을 확인하고, 자동 수집한 가격 3개를 공식 페이지와 대조한다 |

## 핵심 가정 (결과를 좌우한다)
- **small 1단위:**
  - Snowflake 시간당 2크레딧
  - Databricks 시간당 12 DBU
  - Redshift 8 RPU
  - BigQuery 100슬롯
- **시나리오:**
  - W1: small×1로 월 220시간
  - W2: small×2로 월 60시간
  - W3: 월 20TiB를 스캔한다
- **스토리지:** 10TB
- **제외 항목:** 네트워크 송출, 무료 등급, 최소 과금 단위, 약정 할인
- **예상 결과:** W1·W2에서는 Redshift, W3에서는 BigQuery가 가장 싸다. 다만 W1은 가정을 흔들면 1위가 바뀌는 "민감"으로 나올 것이다.

## 위험과 대응
| 위험 | 대응 |
|---|---|
| 실제 가격이 Phase 0 확인값과 다름 | Task 2·3의 실제 조회 단계에서 보고한다. 가격 변동은 Phase 2의 E1 이벤트 후보다. Task 2(AWS)와 Task 3(Azure) 모두 값이 같았다 |
| AWS 파일의 선결제 항목이 단가로 섞임 | usagetype 접미어를 정확히 맞추고, 함정을 넣은 테스트로 막는다. 실제 데이터에서도 걸러지는 것을 확인했다 |
| Azure의 0원 체험·POC SKU, 클래식 SKU, 스토리지 구간이 섞임 | 상품명·SKU명·구간 조건을 정확히 맞추고, 함정을 넣은 테스트로 막는다 |
| 수동 가격을 잘못 입력 | `confirmed_on`이 없으면 실행이 멈춘다 |
| 가정 하나가 결론을 바꿈 | ±50% 민감도 라벨을 붙이고, 가정 전체를 화면에 공개한다 |
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
- **2026-09-11 Task 3 완료**
  - 순서: 테스트 작성 → 실패 확인(`collectors.azure_prices` ImportError) → `collectors/azure_prices.py` 구현
  - 테스트: Task 3의 3개 통과, 누적 9개 통과
  - 실제 Azure 조회값이 Phase 0 확인값과 같다 [확인].

    | | 미국 (eastus) | 서울 (koreacentral) |
    |---|---|---|
    | Databricks 서버리스 SQL (DBU-시간) | $0.70 | $0.95 |
    | ADLS Gen2 Hot LRS 첫 구간 (GB-월) | $0.0208 | $0.02 |
  - 0원 체험·POC SKU, 클래식 SQL SKU($0.22), 51,200GB 이상 스토리지 구간이 테스트로 걸러진다.
