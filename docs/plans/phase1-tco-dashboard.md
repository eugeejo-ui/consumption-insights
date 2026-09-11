# Phase 1: 가격 수집 + TCO 모델 + 정적 대시보드 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로컬에서 명령 한 번으로 4개 플랫폼 × 2개 리전 가격을 모으고, 워크로드 3개의 월 비용을 추정해 `site/index.html` 대시보드를 만든다.

**Architecture:**
- 수집기 3종이 모두 같은 `PriceRecord` 형식으로 가격을 모아 날짜별 CSV 스냅샷에 저장한다. 수집기 3종은 AWS API, Azure API, 사람이 확인한 수동 가격표다.
- `model/tco.py`가 스냅샷과 `workloads.yaml`(가정)로 월 비용, T1(순위·민감도), T2(서울 프리미엄)를 계산한다.
- `publish/render_site.py`가 결과를 Jinja2 + Plotly로 정적 HTML로 만든다.

**Tech Stack:** Python 3.11 (프로젝트 venv), requests, PyYAML, Jinja2, plotly, pytest

**Spec:** `CLAUDE.md` Phase 1, `docs/01_plan_v2.md` §2~3, `docs/02_phase0_report.md`

## 진행 현황과 재개 계획 (2026-09-11 갱신)
- **현재 Phase:** Phase 1 (가격 수집 + TCO 모델 + 정적 대시보드)
- **현재 Task:** Task 1. 7단계 중 6단계를 완료했고, 남은 것은 7단계 첫 커밋이다.
- **진행 원칙:** CLAUDE.md 규칙 10(한 번에 Task 하나만 하고, 끝나면 보고 후 대기)과 규칙 11(개인정보가 기록되는 행동은 먼저 확인)을 따른다.

### 이번 작업: Task 1의 7단계 (첫 커밋)
| 순서 | 할 일 | 확인 기준 |
|---|---|---|
| 1 | 이 저장소 전용 커밋 이메일을 GitHub noreply 주소로 설정한다(`git config --local user.email`). 전역 설정은 건드리지 않는다 | `--local` 값이 noreply 형식 |
| 2 | 커밋 대상 파일에서 이메일 주소와 로컬 사용자 경로를 검색한다. Anthropic 공동 작성자 표기는 예외다 | 0건 |
| 3 | 전체 테스트를 다시 실행한다 | 3 passed |
| 4 | 스테이징: `requirements.txt`, `pytest.ini`, `.gitignore`, `CLAUDE.md`, `docs/`, `common/`, `tests/test_schema.py` | `.venv` 등은 `.gitignore`로 제외된다 |
| 5 | 커밋: `chore: project skeleton and price snapshot schema` + Co-Authored-By | `git log` 1건 |
| 6 | 작성자 이메일이 noreply인지, 작업 트리가 깨끗한지 확인한다 | — |
| 7 | CLAUDE.md에 Task 1 완료를 기록한다(이 변경은 다음 Task 커밋에 포함). 보고하고 멈춘다 | — |

- **작성자 이름:** 전역 설정의 이름을 그대로 쓴다. 로컬 커밋이라 push(Phase 2) 전까지는 공개되지 않는다. 바꾸고 싶으면 push 전에 알려 주면 된다.
- **막히는 경우:** 사용자 지시에 따라 Aside CLI 사용 여부를 확인하고 보고한다. 로컬 커밋은 인증이 필요 없어서, 막힐 수 있는 지점은 커밋 신원(이름·이메일) 설정뿐이다.

### 남은 Task (각각 사용자 지시 후 하나씩)
| Task | 내용 | 사용자 할 일 |
|---|---|---|
| 2 | AWS Redshift 수집기 | — |
| 3 | Azure Databricks·ADLS 수집기 | — |
| 4 | 수동 가격표 + 확인 게이트 | 브라우저로 원본 확인 후 `confirmed_on` 입력 |
| 5 | 워크로드 가정 + 월 비용 계산 | 가정 검토 |
| 6 | T1·T2 판정 | — |
| 7 | 정적 대시보드 | — |
| 8 | 파이프라인 실행·검증 | 화면 확인, 가격 3개 대조 |

- **계획 작성 이후 달라진 점:** plotly가 7.0.0으로 설치됐다(Task 7에서 쓸 API 호환 확인). 설치된 버전 목록은 CLAUDE.md 5절에 있다.

## 한눈에 보기 (사용자용 요약)
| Task | 만드는 것 | 사용자가 할 일 |
|---|---|---|
| 1 | 프로젝트 뼈대(venv, git, 테스트), 공통 가격 스키마 | git 사용자 이름·이메일 확인(공개 저장소이므로 GitHub noreply 이메일 권장) |
| 2 | AWS Redshift 가격 수집기 (선결제 함정 방지 테스트 포함) | — |
| 3 | Azure Databricks 서버리스 SQL + ADLS 스토리지 수집기 | — |
| 4 | 수동 가격표(Snowflake, BigQuery)와 로더. **확인일이 비어 있으면 실행이 멈춘다** | **브라우저로 원본을 보고 가격을 확인한 뒤 `confirmed_on`에 날짜 입력** |
| 5 | 워크로드 가정 파일 + 월 비용 계산 | 가정값(`workloads.yaml`) 검토 |
| 6 | T1(1위 순위·민감도), T2(서울 프리미엄) 판정 | — |
| 7 | 정적 대시보드 HTML | — |
| 8 | 전체 실행 명령(`pipeline.py`), 실제 데이터로 실행 | 화면 확인, 가격 3개를 공식 페이지와 대조 |

**CLAUDE.md 계획에서 바뀐 점 (Phase 0 결과 반영)**
- 1-4 BigQuery는 자동 수집에서 **수동 가격표**로 바꾼다. 가격 페이지에 리전별 가격이 SKU 이름 없이 위치 배열로만 들어 있어서 파싱이 불안정하다 [확인]. 자동 변경 감지(가격 문자열 지문 비교)는 Phase 2-6에서 한다.
- Databricks 가격은 Azure Retail API의 **Azure Databricks 서버리스 SQL**로 자동 수집한다. AWS 직판 가격과 같은 값이다 ($0.70 / $0.95 [확인]). 스토리지는 같은 API의 ADLS Gen2 가격을 쓴다.
- S3, duckdb, pandas, pyarrow는 Phase 1에서 쓰지 않는다(YAGNI). 스냅샷은 Git에서 차이를 읽기 쉬운 CSV로 저장한다.

## Global Constraints
- Windows + PowerShell 환경이다. venv는 활성화 스크립트 대신 `.venv\Scripts\python.exe`를 직접 호출한다(실행 정책 때문에 `Activate.ps1`이 막힐 수 있다).
- Python 3.11. 콘솔에 한글을 출력할 때는 `$env:PYTHONIOENCODING='utf-8'`을 설정한다.
- 공개 저장소를 전제한다. 코드와 데이터에 이메일, 토큰, 개인정보를 넣지 않는다.
- snowflake.com, databricks.com에는 자동으로 접근하지 않는다(약관). 두 플랫폼 가격은 사람이 확인한 CSV에서만 읽는다.
- 스냅샷 컬럼은 `platform, service, sku, region, unit, price_usd, source, fetched_at` 순서로 고정한다. region 값은 `us`와 `seoul` 두 가지뿐이다.
- 가정(workloads.yaml)과 판정 기준(config/thresholds.yaml)은 코드가 아니라 파일에 둔다. 플랫폼 간 비교는 화면에 "모델 추정"으로 표시한다.
- 커밋은 로컬에만 하고 push하지 않는다(원격 저장소는 Phase 2). 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`을 붙인다.

## File Structure
```
requirements.txt, pytest.ini, .gitignore
pipeline.py                      # Task 8: 수집 → 스냅샷 → TCO → site/
common/schema.py                 # Task 1: PriceRecord, write_snapshot, read_snapshot
collectors/aws_prices.py         # Task 2: Redshift Serverless RPU, 관리형 스토리지
collectors/azure_prices.py       # Task 3: Databricks 서버리스 SQL DBU, ADLS Hot LRS
collectors/manual_prices.py      # Task 4: data/manual/*_prices.csv 로더 (확인일 필수)
data/manual/snowflake_prices.csv # Task 4
data/manual/bigquery_prices.csv  # Task 4
data/manual/workloads.yaml       # Task 5: 시나리오·용량 환산 [가정]
config/thresholds.yaml           # Task 6: T1 민감도, T2 기준
model/tco.py                     # Task 5~6
publish/render_site.py           # Task 7
templates/site/index.html.j2     # Task 7
tests/conftest.py                # 공통 픽스처 (가격표, 워크로드)
tests/fixtures/aws_redshift_offer.json, tests/fixtures/azure_items.json
tests/test_*.py
```
`common/`, `collectors/`, `model/`, `publish/`에는 빈 `__init__.py`를 둔다.

---

### Task 1: 프로젝트 뼈대 + 공통 가격 스키마 (CLAUDE.md 1-0, 1-5)

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `.gitignore`, `common/__init__.py`, `common/schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces: `PriceRecord(platform, service, sku, region, unit, price_usd, source, fetched_at)` (frozen dataclass), `REGIONS = ("us", "seoul")`, `FIELDS`, `write_snapshot(records, day, name, root=Path("data/raw")) -> Path`, `read_snapshot(path) -> list[PriceRecord]`

- [ ] **Step 1: 뼈대 파일 작성**

`requirements.txt`
```
requests>=2.31
PyYAML>=6.0
Jinja2>=3.1
plotly>=5.9
pytest>=7.4
```
`pytest.ini`
```ini
[pytest]
pythonpath = .
testpaths = tests
```
`.gitignore`
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
site/
*.duckdb
.env
```

- [ ] **Step 2: venv 생성과 의존성 설치, git 초기화**

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
git init -b main
git config user.name; git config user.email
```
Expected: 설치 성공. git 사용자 설정이 비어 있으면 사용자에게 알린다. 공개 저장소이므로 GitHub noreply 이메일을 권장한다.

- [ ] **Step 3: 실패하는 테스트 작성** — `tests/test_schema.py`

```python
import pytest

from common.schema import PriceRecord, read_snapshot, write_snapshot


def rec(**kw):
    base = dict(platform="redshift", service="compute", sku="serverless-rpu", region="us",
                unit="RPU-hour", price_usd=0.375, source="https://example", fetched_at="2026-09-11")
    base.update(kw)
    return PriceRecord(**base)


def test_rejects_unknown_region():
    with pytest.raises(ValueError):
        rec(region="eu")


def test_rejects_zero_price():
    with pytest.raises(ValueError):
        rec(price_usd=0)


def test_roundtrip_is_sorted_and_lossless(tmp_path):
    path = write_snapshot([rec(region="seoul", price_usd=0.438), rec()], "2026-09-11", "aws", root=tmp_path)
    assert path == tmp_path / "2026-09-11" / "aws.csv"
    back = read_snapshot(path)
    assert [r.region for r in back] == ["seoul", "us"]
    assert back[0].price_usd == 0.438
```

- [ ] **Step 4: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_schema.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'common'`)

- [ ] **Step 5: 구현** — `common/__init__.py`(빈 파일), `common/schema.py`

```python
"""가격 스냅샷 공통 스키마: 모든 수집기가 이 형식으로 저장한다."""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

REGIONS = ("us", "seoul")
FIELDS = ["platform", "service", "sku", "region", "unit", "price_usd", "source", "fetched_at"]


@dataclass(frozen=True)
class PriceRecord:
    platform: str
    service: str
    sku: str
    region: str
    unit: str
    price_usd: float
    source: str
    fetched_at: str

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise ValueError(f"unknown region: {self.region}")
        if not self.price_usd > 0:
            raise ValueError(f"price must be positive: {self.sku} {self.region} {self.price_usd}")


def write_snapshot(records: list[PriceRecord], day: str, name: str, root: Path = Path("data/raw")) -> Path:
    out = Path(root) / day / f"{name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted((asdict(r) for r in records), key=lambda r: (r["platform"], r["service"], r["sku"], r["region"]))
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return out


def read_snapshot(path: Path) -> list[PriceRecord]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return [PriceRecord(**{**row, "price_usd": float(row["price_usd"])}) for row in csv.DictReader(f)]
```

- [ ] **Step 6: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_schema.py -v`
Expected: 3 passed

- [ ] **Step 7: 커밋** (기존 문서 포함 첫 커밋)

```powershell
git add requirements.txt pytest.ini .gitignore CLAUDE.md docs common tests/test_schema.py
git commit -m "chore: project skeleton and price snapshot schema" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: AWS Redshift 가격 수집기 (CLAUDE.md 1-2)

**Files:**
- Create: `collectors/__init__.py`, `collectors/aws_prices.py`, `tests/fixtures/aws_redshift_offer.json`
- Test: `tests/test_aws_prices.py`

**Interfaces:**
- Consumes: `PriceRecord`
- Produces: `collect(fetched_at: str, fetch=fetch_json) -> list[PriceRecord]`. 결과는 platform=`redshift`인 `serverless-rpu`(compute, RPU-hour)와 `managed-storage`(storage, GB-month)이고, 각각 us·seoul 값을 가진다.

- [ ] **Step 1: 픽스처 작성** — `tests/fixtures/aws_redshift_offer.json`. Phase 0-2에서 본 함정을 그대로 넣는다.

```json
{
  "products": {
    "SKU_OD": {"productFamily": "Serverless", "attributes": {"usagetype": "APN2-Redshift:ServerlessUsage"}},
    "SKU_CR_AU": {"productFamily": "Serverless", "attributes": {"usagetype": "APN2-Redshift:ServerlessUsage-CR-1YR-AU"}},
    "SKU_CR_NU": {"productFamily": "Serverless", "attributes": {"usagetype": "APN2-Redshift:ServerlessUsage-CR-1YR-NU"}},
    "SKU_RMS": {"productFamily": "Redshift Managed Storage", "attributes": {"usagetype": "APN2-RMS:ra3.4xlarge"}}
  },
  "terms": {
    "OnDemand": {
      "SKU_OD": {"T1": {"priceDimensions": {"D1": {"unit": "RPU-Hr", "pricePerUnit": {"USD": "0.4380000000"}}}}},
      "SKU_CR_AU": {"T2": {"priceDimensions": {"D2": {"unit": "RPU-Hr", "pricePerUnit": {"USD": "2839.0000000000"}}}}},
      "SKU_CR_NU": {"T3": {"priceDimensions": {"D3": {"unit": "RPU-Hr", "pricePerUnit": {"USD": "0.3420000000"}}}}},
      "SKU_RMS": {"T4": {"priceDimensions": {"D4": {"unit": "GB-Mo", "pricePerUnit": {"USD": "0.0261000000"}}}}}
    }
  }
}
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_aws_prices.py`

```python
import json
from pathlib import Path

import pytest

from collectors.aws_prices import collect, extract_redshift

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "aws_redshift_offer.json").read_text(encoding="utf-8"))


def test_picks_on_demand_rpu_and_ignores_capacity_reservations():
    recs = {r.sku: r for r in extract_redshift(FIXTURE, "seoul", "2026-09-11", "src")}
    assert recs["serverless-rpu"].price_usd == 0.438  # 2839(선결제)나 0.342(예약)가 아니어야 한다
    assert recs["serverless-rpu"].unit == "RPU-hour"
    assert recs["managed-storage"].price_usd == 0.0261


def test_fails_loudly_when_sku_missing():
    with pytest.raises(ValueError):
        extract_redshift({"products": {}, "terms": {"OnDemand": {}}}, "us", "2026-09-11", "src")


def test_collect_fetches_region_index_then_region_files():
    calls = []

    def fake_fetch(url):
        calls.append(url)
        if url.endswith("region_index.json"):
            return {"regions": {"us-east-1": {"currentVersionUrl": "/x/us-east-1/index.json"},
                                "ap-northeast-2": {"currentVersionUrl": "/x/ap-northeast-2/index.json"}}}
        return FIXTURE

    recs = collect("2026-09-11", fetch=fake_fetch)
    assert {r.region for r in recs} == {"us", "seoul"}
    assert any(u.endswith("/x/ap-northeast-2/index.json") for u in calls)
```

- [ ] **Step 3: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_aws_prices.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'collectors'`)

- [ ] **Step 4: 구현** — `collectors/__init__.py`(빈 파일), `collectors/aws_prices.py`

```python
"""AWS 대량 가격 파일에서 Redshift Serverless 단가를 수집한다 (인증 불필요)."""
from __future__ import annotations

from typing import Callable

import requests

from common.schema import PriceRecord

BASE = "https://pricing.us-east-1.amazonaws.com"
REGION_CODES = {"us": "us-east-1", "seoul": "ap-northeast-2"}
# (sku, service, usagetype 접미어, AWS 단위, 저장 단위)
TARGETS = [
    ("serverless-rpu", "compute", "Redshift:ServerlessUsage", "RPU-Hr", "RPU-hour"),
    ("managed-storage", "storage", "RMS:ra3.4xlarge", "GB-Mo", "GB-month"),
]


def fetch_json(url: str) -> dict:
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    return resp.json()


def region_offer_url(region_code: str, fetch: Callable[[str], dict] = fetch_json) -> str:
    index = fetch(f"{BASE}/offers/v1.0/aws/AmazonRedshift/current/region_index.json")
    return BASE + index["regions"][region_code]["currentVersionUrl"]


def extract_redshift(offer: dict, region: str, fetched_at: str, source: str) -> list[PriceRecord]:
    records = []
    for sku_name, service, suffix, aws_unit, unit in TARGETS:
        prices = set()
        for sku, product in offer["products"].items():
            usagetype = product.get("attributes", {}).get("usagetype", "")
            # 접미어가 정확히 일치해야 한다. '-CR-1YR-AU' 같은 선결제·예약 항목을 거른다 (Phase 0-2).
            if not usagetype.endswith(suffix):
                continue
            for term in offer["terms"]["OnDemand"].get(sku, {}).values():
                for dim in term["priceDimensions"].values():
                    if dim["unit"] == aws_unit:
                        prices.add(float(dim["pricePerUnit"]["USD"]))
        if len(prices) != 1:
            raise ValueError(f"{suffix} in {region}: expected 1 price, got {sorted(prices)}")
        records.append(PriceRecord("redshift", service, sku_name, region, unit, prices.pop(), source, fetched_at))
    return records


def collect(fetched_at: str, fetch: Callable[[str], dict] = fetch_json) -> list[PriceRecord]:
    records = []
    for region, code in REGION_CODES.items():
        url = region_offer_url(code, fetch)
        records += extract_redshift(fetch(url), region, fetched_at, url)
    return records
```

- [ ] **Step 5: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_aws_prices.py -v`
Expected: 3 passed

- [ ] **Step 6: 실제 API 확인**

Run: `.venv\Scripts\python.exe -c "from collectors.aws_prices import collect; [print(r) for r in collect('2026-09-11')]"`
Expected: us serverless-rpu 0.375, seoul 0.438, us managed-storage 0.024, seoul 0.0261 (Phase 0-2 값 [확인]). 값이 다르면 AWS 가격이 바뀐 것이니 보고한다.

- [ ] **Step 7: 커밋**

```powershell
git add collectors/__init__.py collectors/aws_prices.py tests/fixtures/aws_redshift_offer.json tests/test_aws_prices.py
git commit -m "feat: collect Redshift Serverless prices from AWS price list" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Azure Databricks + ADLS 가격 수집기 (CLAUDE.md 1-3)

**Files:**
- Create: `collectors/azure_prices.py`, `tests/fixtures/azure_items.json`
- Test: `tests/test_azure_prices.py`

**Interfaces:**
- Consumes: `PriceRecord`
- Produces: `collect(fetched_at: str, fetch=fetch_items) -> list[PriceRecord]`. 결과는 platform=`databricks`인 `sql-serverless-dbu`(compute, DBU-hour)와 `adls-hot-lrs`(storage, GB-month)이고, 각각 us·seoul 값을 가진다.

- [ ] **Step 1: 픽스처 작성** — `tests/fixtures/azure_items.json`. $0 체험·POC SKU, 클래식 SKU, 스토리지 구간을 함정으로 넣는다.

```json
[
  {"productName": "Azure Databricks Regional", "skuName": "Premium Serverless SQL", "meterName": "Premium Serverless SQL DBU", "unitOfMeasure": "1 Hour", "unitPrice": 0.95, "tierMinimumUnits": 0.0},
  {"productName": "Azure Databricks Regional", "skuName": "Premium - Free Trial Serverless SQL", "meterName": "Premium - Free Trial Serverless SQL DBU", "unitOfMeasure": "1 Hour", "unitPrice": 0.0, "tierMinimumUnits": 0.0},
  {"productName": "Azure Databricks Regional", "skuName": "POC Non-Billable Serverless SQL", "meterName": "POC Non-Billable Serverless SQL DBU", "unitOfMeasure": "1 Hour", "unitPrice": 0.0, "tierMinimumUnits": 0.0},
  {"productName": "Azure Databricks", "skuName": "Premium SQL Analytics", "meterName": "Premium SQL Analytics DBU", "unitOfMeasure": "1 Hour", "unitPrice": 0.22, "tierMinimumUnits": 0.0},
  {"productName": "Azure Data Lake Storage Gen2 Hierarchical Namespace", "skuName": "Hot LRS", "meterName": "Hot LRS Data Stored", "unitOfMeasure": "1 GB/Month", "unitPrice": 0.02, "tierMinimumUnits": 0.0},
  {"productName": "Azure Data Lake Storage Gen2 Hierarchical Namespace", "skuName": "Hot LRS", "meterName": "Hot LRS Data Stored", "unitOfMeasure": "1 GB/Month", "unitPrice": 0.0192, "tierMinimumUnits": 51200.0},
  {"productName": "Blob Storage", "skuName": "Hot LRS", "meterName": "Hot LRS Data Stored", "unitOfMeasure": "1 GB/Month", "unitPrice": 0.02, "tierMinimumUnits": 0.0}
]
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_azure_prices.py`

```python
import json
from pathlib import Path

import pytest

from collectors.azure_prices import collect, extract_databricks

ITEMS = json.loads((Path(__file__).parent / "fixtures" / "azure_items.json").read_text(encoding="utf-8"))


def test_picks_serverless_sql_and_first_storage_tier():
    recs = {r.sku: r for r in extract_databricks(ITEMS, "seoul", "2026-09-11", "src")}
    assert recs["sql-serverless-dbu"].price_usd == 0.95   # 0원 체험·POC, 클래식 0.22가 아니어야 한다
    assert recs["adls-hot-lrs"].price_usd == 0.02         # 51200GB 이상 구간(0.0192)이 아니어야 한다


def test_fails_when_serverless_sql_missing():
    items = [i for i in ITEMS if i["skuName"] != "Premium Serverless SQL"]
    with pytest.raises(ValueError):
        extract_databricks(items, "us", "2026-09-11", "src")


def test_collect_queries_both_regions_with_both_filters():
    seen = []

    def fake_fetch(expr):
        seen.append(expr)
        return ITEMS

    recs = collect("2026-09-11", fetch=fake_fetch)
    assert len(seen) == 4
    assert any("koreacentral" in e for e in seen) and any("eastus" in e for e in seen)
    assert {r.region for r in recs} == {"us", "seoul"}
```

- [ ] **Step 3: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_azure_prices.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'collectors.azure_prices'`)

- [ ] **Step 4: 구현** — `collectors/azure_prices.py`

```python
"""Azure Retail Prices API에서 Databricks 서버리스 SQL과 ADLS 스토리지 단가를 수집한다 (인증 불필요)."""
from __future__ import annotations

from typing import Callable
from urllib.parse import urlencode

import requests

from common.schema import PriceRecord

API = "https://prices.azure.com/api/retail/prices"
REGION_CODES = {"us": "eastus", "seoul": "koreacentral"}
FILTERS = [
    "serviceName eq 'Azure Databricks' and armRegionName eq '{code}' and priceType eq 'Consumption'",
    "serviceName eq 'Storage' and armRegionName eq '{code}' and skuName eq 'Hot LRS' and priceType eq 'Consumption'",
]
# (sku, service, 매칭 조건, 저장 단위)
TARGETS = [
    ("sql-serverless-dbu", "compute",
     lambda i: i["productName"] == "Azure Databricks Regional" and i["skuName"] == "Premium Serverless SQL"
     and i["unitOfMeasure"] == "1 Hour",
     "DBU-hour"),
    ("adls-hot-lrs", "storage",
     lambda i: i["productName"] == "Azure Data Lake Storage Gen2 Hierarchical Namespace"
     and i["meterName"] == "Hot LRS Data Stored" and i.get("tierMinimumUnits", 0) == 0,
     "GB-month"),
]


def fetch_items(filter_expr: str) -> list[dict]:
    url, items = f"{API}?{urlencode({'$filter': filter_expr})}", []
    while url:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        page = resp.json()
        items += page["Items"]
        url = page.get("NextPageLink")
    return items


def extract_databricks(items: list[dict], region: str, fetched_at: str, source: str) -> list[PriceRecord]:
    records = []
    for sku, service, match, unit in TARGETS:
        prices = {float(i["unitPrice"]) for i in items if match(i) and i["unitPrice"] > 0}
        if len(prices) != 1:
            raise ValueError(f"{sku} in {region}: expected 1 price, got {sorted(prices)}")
        records.append(PriceRecord("databricks", service, sku, region, unit, prices.pop(), source, fetched_at))
    return records


def collect(fetched_at: str, fetch: Callable[[str], list[dict]] = fetch_items) -> list[PriceRecord]:
    records = []
    for region, code in REGION_CODES.items():
        items = [i for f in FILTERS for i in fetch(f.format(code=code))]
        records += extract_databricks(items, region, fetched_at, API)
    return records
```

- [ ] **Step 5: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_azure_prices.py -v`
Expected: 3 passed

- [ ] **Step 6: 실제 API 확인**

Run: `.venv\Scripts\python.exe -c "from collectors.azure_prices import collect; [print(r) for r in collect('2026-09-11')]"`
Expected: us DBU 0.70, seoul 0.95, us ADLS 0.0208, seoul 0.02 (Phase 0 조회값 [확인]). 서울 스토리지가 미국보다 싼 점도 그대로 나와야 한다.

- [ ] **Step 7: 커밋**

```powershell
git add collectors/azure_prices.py tests/fixtures/azure_items.json tests/test_azure_prices.py
git commit -m "feat: collect Databricks serverless SQL and ADLS prices from Azure retail API" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: 수동 가격표 + 로더 (CLAUDE.md 1-1, 1-4 변경)

**Files:**
- Create: `collectors/manual_prices.py`, `data/manual/snowflake_prices.csv`, `data/manual/bigquery_prices.csv`
- Test: `tests/test_manual_prices.py`

**Interfaces:**
- Consumes: `PriceRecord`
- Produces: `load_manual(path) -> list[PriceRecord]` (확인일이 비면 `ValueError`), `collect(manual_dir=Path("data/manual")) -> list[PriceRecord]`. 스냅샷의 `fetched_at`에는 `confirmed_on`이 들어간다.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_manual_prices.py`

```python
import csv
from pathlib import Path

import pytest

from collectors.manual_prices import collect, load_manual

HEADER = "platform,service,sku,region,unit,price_usd,source,confirmed_on\n"
REPO = Path(__file__).resolve().parent.parent


def test_loads_confirmed_rows(tmp_path):
    p = tmp_path / "snowflake_prices.csv"
    p.write_text(HEADER + "snowflake,compute,enterprise-credit,us,credit,3.00,src,2026-09-12\n", encoding="utf-8")
    [r] = load_manual(p)
    assert r.price_usd == 3.0 and r.fetched_at == "2026-09-12"


def test_refuses_unconfirmed_rows(tmp_path):
    p = tmp_path / "snowflake_prices.csv"
    p.write_text(HEADER + "snowflake,compute,enterprise-credit,us,credit,3.00,src,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="confirmed_on"):
        load_manual(p)


def test_collect_reads_all_price_files(tmp_path):
    for name, platform in [("snowflake_prices.csv", "snowflake"), ("bigquery_prices.csv", "bigquery")]:
        (tmp_path / name).write_text(HEADER + f"{platform},compute,x,us,credit,1.0,src,2026-09-12\n", encoding="utf-8")
    (tmp_path / "workloads.yaml").write_text("ignored: true\n", encoding="utf-8")
    assert {r.platform for r in collect(tmp_path)} == {"snowflake", "bigquery"}


def test_repo_manual_files_have_expected_columns():
    for path in (REPO / "data" / "manual").glob("*_prices.csv"):
        with path.open(newline="", encoding="utf-8") as f:
            assert next(csv.reader(f)) == HEADER.strip().split(",")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_manual_prices.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'collectors.manual_prices'`)

- [ ] **Step 3: 구현** — `collectors/manual_prices.py`

```python
"""사람이 원본에서 확인한 수동 가격표(data/manual/*_prices.csv)를 읽는다.
Snowflake·Databricks 웹사이트는 약관상 자동 접근하지 않는다 (Phase 0-4)."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from common.schema import PriceRecord

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_manual(path: Path) -> list[PriceRecord]:
    records = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            confirmed = (row.pop("confirmed_on") or "").strip()
            if not DATE.match(confirmed):
                raise ValueError(f"{path}:{line_no} confirmed_on is empty or not YYYY-MM-DD "
                                 "(사람이 원본에서 확인한 날짜를 적어야 한다)")
            records.append(PriceRecord(**{**row, "price_usd": float(row["price_usd"]), "fetched_at": confirmed}))
    return records


def collect(manual_dir: Path = Path("data/manual")) -> list[PriceRecord]:
    return [r for p in sorted(Path(manual_dir).glob("*_prices.csv")) for r in load_manual(p)]
```

- [ ] **Step 4: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_manual_prices.py -v`
Expected: 4 passed

- [ ] **Step 5: 수동 가격표 작성.** 값은 Phase 0에서 모은 것이다. `confirmed_on`은 **일부러 비워 둔다**.

`data/manual/snowflake_prices.csv`
```
platform,service,sku,region,unit,price_usd,source,confirmed_on
snowflake,compute,enterprise-credit,us,credit,3.00,https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf,
snowflake,compute,enterprise-credit,seoul,credit,4.05,https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf,
snowflake,storage,on-demand-storage,us,TB-month,23.00,https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf,
snowflake,storage,on-demand-storage,seoul,TB-month,25.00,https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf,
```
`data/manual/bigquery_prices.csv`
```
platform,service,sku,region,unit,price_usd,source,confirmed_on
bigquery,compute,enterprise-slot,us,slot-hour,0.06,https://cloud.google.com/bigquery/pricing,
bigquery,compute,enterprise-slot,seoul,slot-hour,0.0765,https://cloud.google.com/bigquery/pricing,
bigquery,scan,on-demand,us,TiB,6.25,https://cloud.google.com/bigquery/pricing,
bigquery,scan,on-demand,seoul,TiB,7.50,https://cloud.google.com/bigquery/pricing,
bigquery,storage,active-logical,us,GiB-month,0.02,https://cloud.google.com/bigquery/pricing,
bigquery,storage,active-logical,seoul,GiB-month,0.023,https://cloud.google.com/bigquery/pricing,
```

- [ ] **Step 6: (U) 사용자가 원본으로 확인하고 `confirmed_on` 입력**

사용자가 **본인 브라우저**로 확인할 항목이다. Claude는 두 사이트에 접근하지 않는다.
  1. Snowflake Service Consumption Table PDF: AWS US East와 AWS Seoul 행의 Enterprise 크레딧 단가, 스토리지 단가. 서울 행은 Phase 0 텍스트 추출에서 줄이 어긋난 적이 있다.
  2. BigQuery 가격 페이지: 리전을 "US (multi-region)"와 "Seoul"로 바꿔 가며 온디맨드(TiB), Enterprise 슬롯-시간, Active logical storage를 확인한다. 스토리지 값은 페이지 데이터에서 위치로 추출한 값이라 특히 확인이 필요하다.

값이 다르면 고치고, 맞으면 해당 행의 `confirmed_on`에 확인한 날짜(YYYY-MM-DD)를 적는다.

- [ ] **Step 7: 커밋**

```powershell
git add collectors/manual_prices.py data/manual/snowflake_prices.csv data/manual/bigquery_prices.csv tests/test_manual_prices.py
git commit -m "feat: human-verified manual price tables with confirmation gate" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: 워크로드 가정 + 월 비용 계산 (CLAUDE.md 1-6 전반)

**Files:**
- Create: `data/manual/workloads.yaml`, `model/__init__.py`, `model/tco.py`, `tests/conftest.py`
- Test: `tests/test_tco.py`

**Interfaces:**
- Consumes: `PriceRecord`
- Produces: `PLATFORMS = ("snowflake", "databricks", "redshift", "bigquery")`, `CostRow(scenario, platform, region, compute_usd, storage_usd)` (속성 `total_usd`), `PriceBook(records)` (`.get(platform, service, region) -> PriceRecord`), `estimate(book, workloads, factors=None) -> list[CostRow]`

- [ ] **Step 1: 가정 파일 작성** — `data/manual/workloads.yaml`

```yaml
# 모든 값은 [가정]이다. 대시보드의 "가정 공개" 섹션에 그대로 공개된다.
storage_gb: 10000   # 공통 저장량 10TB (1TB = 1000GB로 계산)

# "small" 1단위에 해당하는 플랫폼별 시간당 사용량 [가정]
# 근거(모두 [지식], 사용자 검토 대상):
#   Snowflake Small 웨어하우스 = 2 credits/h, Databricks SQL Small = 12 DBU/h,
#   Redshift Serverless 최소 기본 용량 = 8 RPU, BigQuery = 100 slots
capacity_per_small:
  snowflake: {unit: credit, per_hour: 2}
  databricks: {unit: DBU-hour, per_hour: 12}
  redshift: {unit: RPU-hour, per_hour: 8}
  bigquery: {unit: slot-hour, per_hour: 100}

scenarios:
  W1:
    name: 소규모 BI 대시보드
    mode: capacity
    size: 1                 # small x1
    hours_per_month: 220    # 평일 10시간 x 22일
  W2:
    name: 야간 배치 ETL
    mode: capacity
    size: 2                 # small x2
    hours_per_month: 60     # 매일 2시간 x 30일
  W3:
    name: 비정기 대용량 탐색
    mode: scan
    tib_scanned_per_month: 20
    size: 4                 # 용량 기반 플랫폼은 small x4로 처리한다고 가정
    tib_per_hour: 2         # small x4가 시간당 2TiB를 스캔한다고 가정 → 10시간
```

- [ ] **Step 2: 공통 픽스처 작성** — `tests/conftest.py` (Task 5~8 공용)

```python
import pytest

from common.schema import PriceRecord

PRICES = {  # (platform, service, sku, unit): (us, seoul)
    ("snowflake", "compute", "enterprise-credit", "credit"): (3.00, 4.05),
    ("snowflake", "storage", "on-demand-storage", "TB-month"): (23.0, 25.0),
    ("databricks", "compute", "sql-serverless-dbu", "DBU-hour"): (0.70, 0.95),
    ("databricks", "storage", "adls-hot-lrs", "GB-month"): (0.0208, 0.02),
    ("redshift", "compute", "serverless-rpu", "RPU-hour"): (0.375, 0.438),
    ("redshift", "storage", "managed-storage", "GB-month"): (0.024, 0.0261),
    ("bigquery", "compute", "enterprise-slot", "slot-hour"): (0.06, 0.0765),
    ("bigquery", "scan", "on-demand", "TiB"): (6.25, 7.50),
    ("bigquery", "storage", "active-logical", "GiB-month"): (0.02, 0.023),
}


@pytest.fixture
def price_records():
    return [PriceRecord(p, s, sku, region, unit, price, "test", "2026-09-11")
            for (p, s, sku, unit), (us, seoul) in PRICES.items()
            for region, price in (("us", us), ("seoul", seoul))]


@pytest.fixture
def workloads():
    return {
        "storage_gb": 10000,
        "capacity_per_small": {
            "snowflake": {"unit": "credit", "per_hour": 2},
            "databricks": {"unit": "DBU-hour", "per_hour": 12},
            "redshift": {"unit": "RPU-hour", "per_hour": 8},
            "bigquery": {"unit": "slot-hour", "per_hour": 100},
        },
        "scenarios": {
            "W1": {"name": "소규모 BI 대시보드", "mode": "capacity", "size": 1, "hours_per_month": 220},
            "W2": {"name": "야간 배치 ETL", "mode": "capacity", "size": 2, "hours_per_month": 60},
            "W3": {"name": "비정기 대용량 탐색", "mode": "scan", "tib_scanned_per_month": 20, "size": 4, "tib_per_hour": 2},
        },
    }
```

- [ ] **Step 3: 실패하는 테스트 작성** — `tests/test_tco.py`

```python
from pathlib import Path

import pytest
import yaml

from model.tco import PLATFORMS, PriceBook, estimate

REPO = Path(__file__).resolve().parent.parent


def rows_by_key(rows):
    return {(r.scenario, r.platform, r.region): r for r in rows}


def test_w1_snowflake_matches_hand_calculation(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W1", "snowflake", "us")]
    assert r.compute_usd == pytest.approx(2 * 1 * 220 * 3.00)   # 440 credits x $3 = $1,320
    assert r.storage_usd == pytest.approx(10000 / 1000 * 23.00)  # 10TB x $23 = $230
    assert r.total_usd == pytest.approx(1550.0)


def test_w3_bigquery_uses_on_demand_scan_price(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W3", "bigquery", "us")]
    assert r.compute_usd == pytest.approx(20 * 6.25)             # 20 TiB x $6.25


def test_w3_capacity_platforms_convert_scan_to_hours(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W3", "redshift", "us")]
    assert r.compute_usd == pytest.approx(8 * 4 * (20 / 2) * 0.375)  # 320 RPU-h x $0.375


def test_gib_storage_is_converted_from_gb(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W1", "bigquery", "us")]
    assert r.storage_usd == pytest.approx(10000 / 1.073741824 * 0.02)


def test_estimate_covers_every_scenario_platform_region(price_records, workloads):
    assert len(estimate(PriceBook(price_records), workloads)) == 3 * len(PLATFORMS) * 2


def test_missing_price_names_the_gap(price_records, workloads):
    book = PriceBook([r for r in price_records if not (r.platform == "redshift" and r.region == "seoul")])
    with pytest.raises(KeyError, match="redshift"):
        estimate(book, workloads)


def test_repo_workloads_file_is_complete():
    wl = yaml.safe_load((REPO / "data" / "manual" / "workloads.yaml").read_text(encoding="utf-8"))
    assert set(wl["scenarios"]) == {"W1", "W2", "W3"}
    assert set(wl["capacity_per_small"]) == set(PLATFORMS)
```

- [ ] **Step 4: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_tco.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'model'`)

- [ ] **Step 5: 구현** — `model/__init__.py`(빈 파일), `model/tco.py`

```python
"""같은 워크로드의 플랫폼별 월 비용(TCO) 추정. 플랫폼 간 비교는 [가정] 기반 모델 추정이다."""
from __future__ import annotations

from dataclasses import dataclass

from common.schema import REGIONS, PriceRecord

PLATFORMS = ("snowflake", "databricks", "redshift", "bigquery")
GB_PER_UNIT = {"GB-month": 1.0, "TB-month": 1000.0, "GiB-month": 1.073741824}


@dataclass(frozen=True)
class CostRow:
    scenario: str
    platform: str
    region: str
    compute_usd: float
    storage_usd: float

    @property
    def total_usd(self) -> float:
        return self.compute_usd + self.storage_usd


class PriceBook:
    def __init__(self, records: list[PriceRecord]):
        self._by: dict[tuple[str, str, str], PriceRecord] = {}
        for r in records:
            key = (r.platform, r.service, r.region)
            if key in self._by and self._by[key].sku != r.sku:
                raise ValueError(f"two SKUs for {key}: {self._by[key].sku}, {r.sku}")
            self._by[key] = r

    def get(self, platform: str, service: str, region: str) -> PriceRecord:
        try:
            return self._by[(platform, service, region)]
        except KeyError:
            raise KeyError(f"missing price: {platform}/{service}/{region}") from None


def storage_cost(book: PriceBook, platform: str, region: str, storage_gb: float) -> float:
    rec = book.get(platform, "storage", region)
    return storage_gb / GB_PER_UNIT[rec.unit] * rec.price_usd


def compute_cost(book: PriceBook, platform: str, region: str, scenario: dict, capacity: dict,
                 factor: float = 1.0) -> float:
    if scenario["mode"] == "scan" and platform == "bigquery":
        # 스캔량이 곧 사용량이다. 용량 가정(factor)을 적용하지 않는다.
        return scenario["tib_scanned_per_month"] * book.get("bigquery", "scan", region).price_usd
    if scenario["mode"] == "scan":
        hours = scenario["tib_scanned_per_month"] / scenario["tib_per_hour"]
    else:
        hours = scenario["hours_per_month"]
    units = capacity[platform]["per_hour"] * scenario["size"] * hours * factor
    return units * book.get(platform, "compute", region).price_usd


def estimate(book: PriceBook, workloads: dict, factors: dict[str, float] | None = None) -> list[CostRow]:
    factors = factors or {}
    rows = []
    for sid, scenario in workloads["scenarios"].items():
        for platform in PLATFORMS:
            for region in REGIONS:
                rows.append(CostRow(
                    sid, platform, region,
                    compute_cost(book, platform, region, scenario, workloads["capacity_per_small"],
                                 factors.get(platform, 1.0)),
                    storage_cost(book, platform, region, workloads["storage_gb"]),
                ))
    return rows
```

- [ ] **Step 6: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_tco.py -v`
Expected: 7 passed

- [ ] **Step 7: 커밋**

```powershell
git add data/manual/workloads.yaml model tests/conftest.py tests/test_tco.py
git commit -m "feat: monthly TCO estimate per scenario, platform and region" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: T1 순위·민감도 + T2 서울 프리미엄 (CLAUDE.md 1-6 후반)

**Files:**
- Create: `config/thresholds.yaml`
- Modify: `model/tco.py` (함수 추가)
- Test: `tests/test_verdicts.py`

**Interfaces:**
- Consumes: `PriceBook`, `estimate`, `CostRow`, `PLATFORMS`
- Produces:
  - `ranking(rows, scenario, region) -> list[str]` (싼 순서)
  - `t1_verdict(book, workloads, sensitivity, region="us") -> {"winners": {sid: platform}, "robustness": {sid: "견고"|"민감"}, "supported": bool}`
  - `seoul_premiums(records) -> list[dict]` (키: platform, service, sku, us, seoul, premium_pct)
  - `t2_verdict(premiums, min_spread_pp) -> {"spread_pp": float, "supported": bool}`

- [ ] **Step 1: 판정 기준 파일 작성** — `config/thresholds.yaml`

```yaml
# 판정 기준 (CLAUDE.md 규칙 5: 데이터를 보기 전에 고정하고, 바꾸면 결정 로그에 기록)
t1_sensitivity: 0.5       # T1: 플랫폼 하나의 용량 가정을 ±50% 흔들어도 1위가 유지되면 '견고'
t2_min_spread_pp: 10.0    # T2: 서울 프리미엄의 최대-최소 차이가 10%p 이상이면 '서비스마다 다르다' 지지
                          # 주의: Phase 0에서 초기 신호(0~37%)를 본 뒤 정한 값이다 (CLAUDE.md 결정 로그)
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_verdicts.py`

```python
from dataclasses import replace

import pytest

from model.tco import PriceBook, estimate, ranking, seoul_premiums, t1_verdict, t2_verdict


def test_ranking_is_cheapest_first(price_records, workloads):
    rows = estimate(PriceBook(price_records), workloads)
    # 손계산(us): W1 redshift 900 < bigquery 1506.26 < snowflake 1550 < databricks 2056
    assert ranking(rows, "W1", "us") == ["redshift", "bigquery", "snowflake", "databricks"]


def test_t1_winners_differ_by_scenario(price_records, workloads):
    v = t1_verdict(PriceBook(price_records), workloads, 0.5)
    # W3: bigquery 온디맨드 125+186.26=311.26 < redshift 120+240=360
    assert v["winners"] == {"W1": "redshift", "W2": "redshift", "W3": "bigquery"}
    assert v["supported"] is True


def test_t1_marks_close_call_as_sensitive(price_records, workloads):
    # W1: bigquery 용량을 x0.5로 하면 660+186.26=846.26 < redshift 900 → 1위가 바뀐다
    assert t1_verdict(PriceBook(price_records), workloads, 0.5)["robustness"]["W1"] == "민감"


def test_t1_marks_wide_margin_as_robust(price_records, workloads):
    cheap = [replace(r, price_usd=0.01) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
             for r in price_records]
    # redshift W1 = 1760x0.01+240 = 257.6, x1.5여도 266.4. 다른 플랫폼 x0.5 중 최저는 bigquery 846.26
    assert t1_verdict(PriceBook(cheap), workloads, 0.5)["robustness"]["W1"] == "견고"


def test_seoul_premium_per_sku(price_records):
    p = {(x["platform"], x["sku"]): x for x in seoul_premiums(price_records)}
    assert p[("redshift", "serverless-rpu")]["premium_pct"] == 16.8
    assert p[("databricks", "adls-hot-lrs")]["premium_pct"] == -3.8   # 서울이 더 싸다


def test_t2_uses_spread_threshold(price_records):
    v = t2_verdict(seoul_premiums(price_records), 10.0)
    assert v["spread_pp"] == pytest.approx(39.5)   # databricks DBU +35.7 − ADLS −3.8
    assert v["supported"] is True
    assert t2_verdict(seoul_premiums(price_records), 50.0)["supported"] is False
```

- [ ] **Step 3: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_verdicts.py -v`
Expected: FAIL (`ImportError: cannot import name 'ranking'`)

- [ ] **Step 4: 구현** — `model/tco.py` 끝에 추가

```python
def ranking(rows: list[CostRow], scenario: str, region: str) -> list[str]:
    selected = sorted((r for r in rows if r.scenario == scenario and r.region == region), key=lambda r: r.total_usd)
    return [r.platform for r in selected]


def t1_verdict(book: PriceBook, workloads: dict, sensitivity: float, region: str = "us") -> dict:
    """T1: 시나리오마다 1위가 다른가. 1위가 플랫폼 하나의 용량 가정 ±sensitivity에도 유지되면 '견고'."""
    base = estimate(book, workloads)
    winners = {sid: ranking(base, sid, region)[0] for sid in workloads["scenarios"]}
    robustness = {sid: "견고" for sid in workloads["scenarios"]}
    for platform in PLATFORMS:
        for factor in (1 - sensitivity, 1 + sensitivity):
            shaken = estimate(book, workloads, {platform: factor})
            for sid in workloads["scenarios"]:
                if ranking(shaken, sid, region)[0] != winners[sid]:
                    robustness[sid] = "민감"
    return {"winners": winners, "robustness": robustness, "supported": len(set(winners.values())) > 1}


def seoul_premiums(records: list[PriceRecord]) -> list[dict]:
    by = {(r.platform, r.service, r.sku, r.region): r for r in records}
    out = []
    for (platform, service, sku, region), us in sorted(by.items()):
        seoul = by.get((platform, service, sku, "seoul"))
        if region != "us" or seoul is None:
            continue
        out.append({"platform": platform, "service": service, "sku": sku,
                    "us": us.price_usd, "seoul": seoul.price_usd,
                    "premium_pct": round((seoul.price_usd / us.price_usd - 1) * 100, 1)})
    return out


def t2_verdict(premiums: list[dict], min_spread_pp: float) -> dict:
    values = [p["premium_pct"] for p in premiums]
    spread = round(max(values) - min(values), 1)
    return {"spread_pp": spread, "supported": spread >= min_spread_pp}
```

- [ ] **Step 5: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_verdicts.py tests/test_tco.py -v`
Expected: 13 passed

- [ ] **Step 6: 커밋**

```powershell
git add config/thresholds.yaml model/tco.py tests/test_verdicts.py
git commit -m "feat: T1 ranking robustness and T2 Seoul premium verdicts" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: 정적 대시보드 렌더링 (CLAUDE.md 1-7)

**Files:**
- Create: `publish/__init__.py`, `publish/render_site.py`, `templates/site/index.html.j2`
- Test: `tests/test_render_site.py`

**Interfaces:**
- Consumes: `CostRow`, `PLATFORMS`, Task 6의 판정 dict 형식
- Produces: `render(rows, premiums, t1, t2, workloads, price_dates, built_on, out_dir=Path("site")) -> Path`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_render_site.py`

```python
from model.tco import PLATFORMS, CostRow
from publish.render_site import render


def test_render_writes_page_with_disclaimer_numbers_and_dates(tmp_path, workloads):
    rows = [CostRow(sid, p, reg, 100.0, 10.0) for sid in workloads["scenarios"] for p in PLATFORMS for reg in ("us", "seoul")]
    out = render(
        rows,
        premiums=[{"platform": "redshift", "service": "compute", "sku": "serverless-rpu",
                   "us": 0.375, "seoul": 0.438, "premium_pct": 16.8}],
        t1={"winners": {"W1": "redshift", "W2": "redshift", "W3": "bigquery"},
            "robustness": {"W1": "민감", "W2": "견고", "W3": "민감"}, "supported": True},
        t2={"spread_pp": 39.5, "supported": True},
        workloads=workloads, price_dates={"snowflake": "2026-09-12"}, built_on="2026-09-12", out_dir=tmp_path)
    html = out.read_text(encoding="utf-8")
    assert out == tmp_path / "index.html"
    assert "모델 추정" in html
    assert "110.00" in html            # 합계 = 컴퓨트 100 + 스토리지 10
    assert "+16.8%" in html
    assert "2026-09-12" in html
    assert "cdn.plot.ly" in html
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render_site.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'publish'`)

- [ ] **Step 3: 구현** — `publish/__init__.py`(빈 파일), `publish/render_site.py`

```python
"""TCO 결과를 정적 HTML(site/index.html)로 만든다. 차트는 Plotly(CDN)."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs_version

from model.tco import PLATFORMS, CostRow

TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "site"


def cost_chart(rows: list[CostRow], scenario: str) -> str:
    fig = go.Figure()
    for region in ("us", "seoul"):
        selected = {r.platform: r for r in rows if r.scenario == scenario and r.region == region}
        fig.add_bar(name=region, x=list(PLATFORMS), y=[round(selected[p].total_usd, 2) for p in PLATFORMS])
    fig.update_layout(barmode="group", yaxis_title="USD / month", height=320, margin=dict(l=40, r=10, t=30, b=30))
    return fig.to_html(full_html=False, include_plotlyjs=False)


def render(rows: list[CostRow], premiums: list[dict], t1: dict, t2: dict, workloads: dict,
           price_dates: dict[str, str], built_on: str, out_dir: Path = Path("site")) -> Path:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]))
    html = env.get_template("index.html.j2").render(
        rows=rows, premiums=premiums, t1=t1, t2=t2, workloads=workloads,
        charts={sid: cost_chart(rows, sid) for sid in workloads["scenarios"]},
        price_dates=price_dates, built_on=built_on,
        plotly_cdn=f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js",
    )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
```

- [ ] **Step 4: 템플릿 작성** — `templates/site/index.html.j2`

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>데이터 플랫폼 월 비용 비교</title>
<script src="{{ plotly_cdn }}"></script>
<style>
  body { font-family: system-ui, -apple-system, "Malgun Gothic", sans-serif; max-width: 960px; margin: 0 auto; padding: 24px; color: #1f2328; }
  .notice { background: #fff8e1; border-left: 4px solid #f5a623; padding: 12px 16px; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0 24px; }
  th, td { border-bottom: 1px solid #d0d7de; padding: 6px 8px; text-align: right; }
  th:first-child, td:first-child { text-align: left; }
  .verdict { font-weight: 600; }
</style>
</head>
<body>
<h1>데이터 플랫폼 월 비용(TCO) 비교</h1>
<p>빌드일 {{ built_on }}</p>
<p class="notice">플랫폼 간 비교는 <strong>가정 기반 모델 추정</strong>입니다. 모든 가정은 맨 아래에 공개합니다.</p>

<h2>가설 판정</h2>
<table>
  <tr><th>가설</th><th>판정</th><th>근거</th></tr>
  <tr><td>T1 월 비용 1위는 워크로드마다 다르다 (미국 리전)</td>
      <td class="verdict">{{ "지지" if t1.supported else "기각" }}</td>
      <td>{% for sid, p in t1.winners.items() %}{{ sid }}: {{ p }} ({{ t1.robustness[sid] }}){% if not loop.last %}, {% endif %}{% endfor %}</td></tr>
  <tr><td>T2 서울 프리미엄은 서비스마다 다르다</td>
      <td class="verdict">{{ "지지" if t2.supported else "기각" }}</td>
      <td>최대-최소 차이 {{ t2.spread_pp }}%p</td></tr>
</table>

{% for sid, sc in workloads.scenarios.items() %}
<h2>{{ sid }} · {{ sc.name }}</h2>
{{ charts[sid] | safe }}
<table>
  <tr><th>플랫폼</th><th>리전</th><th>컴퓨트</th><th>스토리지</th><th>합계 (USD/월)</th></tr>
  {% for r in rows if r.scenario == sid %}
  <tr><td>{{ r.platform }}</td><td>{{ r.region }}</td><td>{{ "%.2f"|format(r.compute_usd) }}</td>
      <td>{{ "%.2f"|format(r.storage_usd) }}</td><td>{{ "%.2f"|format(r.total_usd) }}</td></tr>
  {% endfor %}
</table>
{% endfor %}

<h2>서울 프리미엄 (공시 단가 기준)</h2>
<table>
  <tr><th>플랫폼 / 항목</th><th>미국</th><th>서울</th><th>프리미엄</th></tr>
  {% for p in premiums %}
  <tr><td>{{ p.platform }} / {{ p.service }} ({{ p.sku }})</td><td>{{ p.us }}</td><td>{{ p.seoul }}</td>
      <td>{{ "%+.1f"|format(p.premium_pct) }}%</td></tr>
  {% endfor %}
</table>

<h2>가정 공개</h2>
<ul>
  <li>공통 저장량: {{ workloads.storage_gb }} GB</li>
  {% for p, c in workloads.capacity_per_small.items() %}<li>{{ p }}: small 1단위 = 시간당 {{ c.per_hour }} {{ c.unit }}</li>{% endfor %}
  {% for sid, sc in workloads.scenarios.items() %}<li>{{ sid }} {{ sc.name }}: {{ sc }}</li>{% endfor %}
  <li>제외 항목: 네트워크 송출, 무료 등급, 최소 과금 단위, 약정 할인</li>
</ul>

<h2>가격 확인일</h2>
<ul>{% for p, d in price_dates.items() %}<li>{{ p }}: {{ d }}</li>{% endfor %}</ul>
</body>
</html>
```

- [ ] **Step 5: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render_site.py -v`
Expected: 1 passed

- [ ] **Step 6: 커밋**

```powershell
git add publish templates tests/test_render_site.py
git commit -m "feat: static TCO dashboard page with assumptions and verdicts" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: 파이프라인 + 실제 실행 + 검증 (CLAUDE.md 1-8)

**Files:**
- Create: `pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: 모든 수집기의 `collect`, `write_snapshot`/`read_snapshot`, `PriceBook`, `estimate`, `seoul_premiums`, `t1_verdict`, `t2_verdict`, `render`
- Produces: `main(argv=None) -> Path`. `--offline DAY`를 주면 수집 없이 `data/raw/DAY/*.csv`로 계산한다.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_pipeline.py`

```python
import shutil
from pathlib import Path

from common.schema import write_snapshot
from pipeline import main

REPO = Path(__file__).resolve().parent.parent


def test_offline_pipeline_builds_site(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    write_snapshot(price_records, "2026-09-11", "all")
    (tmp_path / "data" / "manual").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "data" / "manual" / "workloads.yaml", tmp_path / "data" / "manual" / "workloads.yaml")
    (tmp_path / "config").mkdir()
    shutil.copy(REPO / "config" / "thresholds.yaml", tmp_path / "config" / "thresholds.yaml")

    out = main(["--offline", "2026-09-11"])

    assert out == Path("site") / "index.html"
    assert "W3" in out.read_text(encoding="utf-8")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_pipeline.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'pipeline'`)

- [ ] **Step 3: 구현** — `pipeline.py`

```python
"""Phase 1 파이프라인: 수집 → 스냅샷 → TCO → site/ 생성.

실행:  .venv\\Scripts\\python.exe pipeline.py             (오늘 날짜로 수집)
       .venv\\Scripts\\python.exe pipeline.py --offline 2026-09-11   (저장된 스냅샷으로만 계산)
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import yaml

from collectors import aws_prices, azure_prices, manual_prices
from common.schema import read_snapshot, write_snapshot
from model.tco import PriceBook, estimate, seoul_premiums, t1_verdict, t2_verdict
from publish.render_site import render


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", metavar="DAY", help="수집하지 않고 data/raw/DAY 스냅샷으로 계산한다")
    args = parser.parse_args(argv)

    if args.offline:
        day = args.offline
        records = [r for p in sorted(Path("data/raw", day).glob("*.csv")) for r in read_snapshot(p)]
    else:
        day = dt.date.today().isoformat()
        records = []
        for name, collected in [("aws", aws_prices.collect(day)),
                                ("azure", azure_prices.collect(day)),
                                ("manual", manual_prices.collect())]:
            write_snapshot(collected, day, name)
            records += collected

    workloads = load_yaml("data/manual/workloads.yaml")
    thresholds = load_yaml("config/thresholds.yaml")
    book = PriceBook(records)
    premiums = seoul_premiums(records)
    price_dates: dict[str, str] = {}
    for r in records:
        price_dates[r.platform] = max(price_dates.get(r.platform, ""), r.fetched_at)

    out = render(estimate(book, workloads), premiums,
                 t1_verdict(book, workloads, thresholds["t1_sensitivity"]),
                 t2_verdict(premiums, thresholds["t2_min_spread_pp"]),
                 workloads, price_dates, built_on=day)
    print(f"site written: {out}")
    return out


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 통과 확인 (전체 테스트)**

Run: `.venv\Scripts\python.exe -m pytest -v`
Expected: 모두 통과 (schema 3, aws 3, azure 3, manual 4, tco 7, verdicts 6, render 1, pipeline 1 = 28 passed)

- [ ] **Step 5: 실제 실행** (Task 4 Step 6에서 사용자가 `confirmed_on`을 채운 뒤)

Run: `$env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe pipeline.py`
Expected: `site written: site\index.html`. `data/raw/<오늘>/`에 aws.csv, azure.csv, manual.csv가 생긴다. `confirmed_on`이 비어 있으면 `ValueError`로 멈추는 것이 정상이다.

- [ ] **Step 6: (C+U) 검증 (CLAUDE.md 1-8)**
  1. `site\index.html`을 브라우저로 연다(사용자). 표 3개, 차트 3개, 판정표, 가정, 확인일이 보이는지 확인한다.
  2. 자동 수집 가격 3개를 사용자가 공식 페이지와 대조한다: Redshift 서울 RPU, Azure Databricks 서울 서버리스 SQL DBU, Azure ADLS 미국 스토리지.
  3. W1 손계산 대조는 `test_w1_snowflake_matches_hand_calculation`이, ±50% 민감도 라벨은 `test_t1_marks_*`가 자동으로 검증한다.
  4. 실제 결과(T1·T2 판정)를 CLAUDE.md 진행 로그에 기록한다.

- [ ] **Step 7: 커밋** (스냅샷 포함)

```powershell
git add pipeline.py tests/test_pipeline.py data/raw
git commit -m "feat: end-to-end Phase 1 pipeline and first price snapshot" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## 완료 기준 (Phase 1 게이트)
- `pytest` 28개 통과
- 실제 실행으로 `site/index.html`이 생성된다. 시나리오 3개 × 플랫폼 4개 × 리전 2개의 표·차트, T1·T2 판정, 가정, 가격 확인일이 모두 보인다.
- 사용자 화면 확인이 끝나면 CLAUDE.md의 Phase 1 체크박스와 진행 로그를 갱신하고 Phase 2 상세 계획으로 넘어간다.
