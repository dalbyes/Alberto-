import pytest
import requests

from ted_tenders.client import TedApiError, TedClient


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append(json)
        return self.responses.pop(0)


def test_search_all_paginates_until_empty_page():
    pages = [
        FakeResponse({"notices": [{"ND": "1"}, {"ND": "2"}], "totalNoticeCount": 3}),
        FakeResponse({"notices": [{"ND": "3"}], "totalNoticeCount": 3}),
        FakeResponse({"notices": [], "totalNoticeCount": 3}),
    ]
    session = FakeSession(pages)
    client = TedClient(session=session, max_retries=1)

    results = list(client.search_all("some query", page_size=2, max_pages=10))
    assert [r["ND"] for r in results] == ["1", "2", "3"]
    assert len(session.calls) == 2  # stops once total count reached, no 3rd call needed


def test_search_all_respects_max_pages():
    pages = [
        FakeResponse({"notices": [{"ND": "1"}], "totalNoticeCount": 100}),
        FakeResponse({"notices": [{"ND": "2"}], "totalNoticeCount": 100}),
    ]
    session = FakeSession(pages)
    client = TedClient(session=session, max_retries=1)

    results = list(client.search_all("q", page_size=1, max_pages=2))
    assert [r["ND"] for r in results] == ["1", "2"]


def test_post_retries_then_raises_on_persistent_failure():
    class AlwaysFailSession:
        def __init__(self):
            self.calls = 0

        def post(self, url, json, timeout):
            self.calls += 1
            raise requests.exceptions.ConnectionError("boom")

    session = AlwaysFailSession()
    client = TedClient(session=session, max_retries=3, retry_backoff=0)

    with pytest.raises(TedApiError):
        client.search_page("q", page=1, page_size=10)
    assert session.calls == 3
