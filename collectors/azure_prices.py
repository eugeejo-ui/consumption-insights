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
