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
