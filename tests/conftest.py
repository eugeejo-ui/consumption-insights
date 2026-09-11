import pytest

from common.schema import PriceRecord

# 로직 검증용 테스트 가격이다. 실제 가격표(data/manual, 수집기)와 다를 수 있다.
# 예: BigQuery 스토리지는 여기서 논리 단가를 쓰지만, 실제 가격표는 물리 단가를 쓴다(2026-09-11 가정 검토).
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
