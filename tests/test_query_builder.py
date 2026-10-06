import datetime as dt

import pytest

from ted_tenders.query_builder import build_query, build_request_payload


def test_broad_query_contains_cpv_and_keywords():
    q = build_query(mode="broad", cpv_codes=["18830000-6"], keyword_groups={"x": ["stivali pompieri"]})
    assert "classification-cpv IN (18830000)" in q
    assert 'FT ~ "stivali pompieri"' in q
    assert " OR " in q


def test_strict_query_uses_and_between_cpv_and_keywords():
    q = build_query(mode="strict", cpv_codes=["18830000-6"], keyword_groups={"x": ["stivali pompieri"]})
    assert "classification-cpv IN (18830000)" in q
    assert 'FT ~ "stivali pompieri"' in q
    assert q.count(" AND ") >= 1


def test_date_range_and_countries_are_appended():
    q = build_query(
        cpv_codes=["18830000-6"],
        keyword_groups={},
        date_from=dt.date(2025, 1, 1),
        date_to=dt.date(2025, 2, 1),
        countries=["IT", "FR"],
    )
    assert "publication-date >= 20250101" in q
    assert "publication-date <= 20250201" in q
    assert "buyer-country IN (IT, FR)" in q


def test_keywords_only_when_no_cpv():
    q = build_query(cpv_codes=[], keyword_groups={"x": ["abc"]})
    assert "classification-cpv" not in q
    assert 'FT ~ "abc"' in q


def test_requires_cpv_or_keywords():
    with pytest.raises(ValueError):
        build_query(cpv_codes=[], keyword_groups={})


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        build_query(mode="nope", cpv_codes=["18830000-6"], keyword_groups={})


def test_request_payload_shape():
    payload = build_request_payload("some query", page=2, page_size=50)
    assert payload["query"] == "some query"
    assert payload["page"] == 2
    assert payload["limit"] == 50
    assert isinstance(payload["fields"], list) and payload["fields"]
