import pytest

from publish.sheets_log import HEADER, append_rows, baseline_rows, rows_from_events


class FakeResponse:
    def __init__(self, rows=0, ok=True, status=200, text=""):
        self.rows, self.ok, self.status_code, self.text = rows, ok, status, text

    def json(self):
        return {"updates": {"updatedRows": self.rows}}


class FakeSession:
    def __init__(self, response=None):
        self.calls = []
        self.response = response

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.response or FakeResponse(len(kw["json"]["values"]))


def test_rows_from_events_one_row_per_price_change():
    events = {"day": "2026-09-12", "compared_to": "2026-09-11", "price_changes": [
        {"platform": "redshift", "service": "compute", "sku": "serverless-rpu", "region": "us",
         "before": 0.375, "after": 0.4, "change_pct": 6.7}]}
    assert rows_from_events(events, "https://example.invalid/commit/abc") == [
        ["2026-09-12", "2026-09-11", "redshift", "compute", "serverless-rpu", "us", 0.375, 0.4, 6.7,
         "https://example.invalid/commit/abc"]]


def test_append_posts_raw_values_to_first_sheet():
    s = FakeSession()
    assert append_rows([["a", 1]], "SHEET_ID", s) == 1
    url, kw = s.calls[0]
    assert url == "https://sheets.googleapis.com/v4/spreadsheets/SHEET_ID/values/A%3AJ:append"
    assert kw["params"] == {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
    assert kw["json"] == {"values": [["a", 1]]}
    assert append_rows([], "SHEET_ID", s) == 0 and len(s.calls) == 1   # 적재할 행이 없으면 호출하지 않는다


def test_append_failure_shows_the_google_message():
    denied = FakeResponse(ok=False, status=403, text='{"error": {"message": "The caller does not have permission"}}')
    with pytest.raises(SystemExit, match="The caller does not have permission"):
        append_rows([["a"]], "SHEET_ID", FakeSession(denied))


def test_baseline_starts_with_header_and_lists_every_price(price_records):
    rows = baseline_rows("2026-09-11", price_records)
    assert rows[0] == HEADER and len(rows) == 1 + len(price_records)
    assert rows[1][:2] == ["2026-09-11", "기준선"] and rows[1][6] == ""
