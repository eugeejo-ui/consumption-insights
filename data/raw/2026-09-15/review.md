> **시뮬레이션:** 검증용 가짜 변동(Redshift 미국 RPU +5%)이다. 머지하지 말고 닫는다.

# 중간 검토 보고서 · 2026-09-15

> **파이프라인은 여기서 멈춰 있습니다.** 아래 내용을 확인하고 판단해 주세요.
> - **컨펌:** GitHub 검토 PR이면 **Merge**. 로컬이면 `.venv\Scripts\python.exe pipeline.py --confirm 2026-09-15` → 화면 생성, 승인 기록(`approved.txt`) → 스냅샷 커밋
> - **반려:** GitHub 검토 PR이면 **Close**. 로컬이면 `data/raw/2026-09-15/` 폴더를 커밋하지 말고 지운 뒤, 원인을 고쳐 `pipeline.py`를 다시 실행

## 1. 요약
- 수집 가격: 18행 (aws 4, azure 4, manual 10)
- 이전 승인 스냅샷 대비: 변화 1건
- 글 초안(E1): 있음 (post.md)
- T1 (미국): 기각
- T1 (서울): 기각
- T2: 채택 (최대-최소 차이 39.5%p)

## 2. 수집 가격
| 플랫폼 | 항목 | SKU | 리전 | 단가(USD) | 단위 | 수집·확인일 | 출처 |
|---|---|---|---|---|---|---|---|
| bigquery | compute | enterprise-slot | seoul | 0.0765 | slot-hour | 2026-09-11 | https://cloud.google.com/bigquery/pricing |
| bigquery | compute | enterprise-slot | us | 0.06 | slot-hour | 2026-09-11 | https://cloud.google.com/bigquery/pricing |
| bigquery | scan | on-demand | seoul | 7.5 | TiB | 2026-09-11 | https://cloud.google.com/bigquery/pricing |
| bigquery | scan | on-demand | us | 6.25 | TiB | 2026-09-11 | https://cloud.google.com/bigquery/pricing |
| bigquery | storage | active-physical | seoul | 0.052 | GiB-month | 2026-09-11 | https://cloud.google.com/bigquery/pricing |
| bigquery | storage | active-physical | us | 0.04 | GiB-month | 2026-09-11 | https://cloud.google.com/bigquery/pricing |
| databricks | compute | sql-serverless-dbu | seoul | 0.95 | DBU-hour | 2026-09-15 | https://prices.azure.com/api/retail/prices |
| databricks | compute | sql-serverless-dbu | us | 0.7 | DBU-hour | 2026-09-15 | https://prices.azure.com/api/retail/prices |
| databricks | storage | adls-hot-lrs | seoul | 0.02 | GB-month | 2026-09-15 | https://prices.azure.com/api/retail/prices |
| databricks | storage | adls-hot-lrs | us | 0.0208 | GB-month | 2026-09-15 | https://prices.azure.com/api/retail/prices |
| redshift | compute | serverless-rpu | seoul | 0.438 | RPU-hour | 2026-09-15 | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRedshift/20260911124505/ap-northeast-2/index.json |
| redshift | compute | serverless-rpu | us | 0.39375 | RPU-hour | 2026-09-15 | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRedshift/20260911124505/us-east-1/index.json (simulated) |
| redshift | storage | managed-storage | seoul | 0.0261 | GB-month | 2026-09-15 | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRedshift/20260911124505/ap-northeast-2/index.json |
| redshift | storage | managed-storage | us | 0.024 | GB-month | 2026-09-15 | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRedshift/20260911124505/us-east-1/index.json |
| snowflake | compute | enterprise-credit | seoul | 4.05 | credit | 2026-09-11 | https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf |
| snowflake | compute | enterprise-credit | us | 3.0 | credit | 2026-09-11 | https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf |
| snowflake | storage | on-demand-storage | seoul | 25.0 | TB-month | 2026-09-11 | https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf |
| snowflake | storage | on-demand-storage | us | 23.0 | TB-month | 2026-09-11 | https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf |

## 3. 이전 승인 스냅샷 대비 변화
| 플랫폼 | 항목 | SKU | 리전 | 이전 | 현재 | 변동률 |
|---|---|---|---|---|---|---|
| redshift | compute | serverless-rpu | us | 0.375 | 0.39375 | +5.0% |

## 4. 월 비용 순위 (USD/월, 낮은 순서, 가정을 세워 모델로 추정한 값)
| 시나리오 | 리전 | 1위 | 2위 | 3위 | 4위 |
|---|---|---|---|---|---|
| W1 | 미국 | redshift 933 | snowflake 1,550 | bigquery 1,693 | databricks 2,056 |
| W1 | 서울 | redshift 1,032 | snowflake 2,032 | bigquery 2,167 | databricks 2,708 |
| W2 | 미국 | redshift 618 | snowflake 950 | bigquery 1,093 | databricks 1,216 |
| W2 | 서울 | redshift 681 | snowflake 1,222 | bigquery 1,402 | databricks 1,568 |
| W3 | 미국 | redshift 366 | snowflake 470 | bigquery 498 | databricks 544 |
| W3 | 서울 | redshift 401 | snowflake 574 | bigquery 634 | databricks 656 |

## 5. 가설 검증 결과
| 가설 | 결과 | 근거 |
|---|---|---|
| T1 (미국) 월 비용 1위는 워크로드마다 다르다 | 기각 | W1: redshift (민감), W2: redshift (민감), W3: redshift (민감) |
| T1 (서울) 월 비용 1위는 워크로드마다 다르다 | 기각 | W1: redshift (견고), W2: redshift (견고), W3: redshift (견고) |
| T2 서울 프리미엄은 서비스마다 다르다 | 채택 | 최대-최소 차이 39.5%p |

괄호 안의 견고·민감은 플랫폼 하나의 용량 가정을 ±50% 조정했을 때 1위가 유지되는지를 뜻합니다.

## 6. 확인 체크리스트
- [ ] 수집 가격이 공식 페이지 값과 맞는가 (자동 수집 AWS·Azure 8행. 수동 가격표는 확인일 참고)
- [ ] 이전 대비 변화가 있다면 설명할 수 있는가
- [ ] 월 비용 순위와 판정이 가정(`data/manual/workloads.yaml`)에 비추어 타당한가
- [ ] 0, 극단값, 단위 오류 같은 이상한 값이 없는가
