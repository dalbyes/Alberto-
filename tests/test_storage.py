from pathlib import Path

from ted_tenders.models import Notice
from ted_tenders.storage import append_notices, load_existing_ids, load_notices


def _notice(id_, title="t"):
    return Notice(id=id_, title=title, country="IT")


def test_append_creates_file_and_writes_rows(tmp_path: Path):
    csv_path = tmp_path / "notices.csv"
    added = append_notices(csv_path, [_notice("1"), _notice("2")])
    assert added == 2
    rows = load_notices(csv_path)
    assert {r["id"] for r in rows} == {"1", "2"}


def test_append_dedupes_existing_ids(tmp_path: Path):
    csv_path = tmp_path / "notices.csv"
    append_notices(csv_path, [_notice("1"), _notice("2")])
    added = append_notices(csv_path, [_notice("2"), _notice("3")])
    assert added == 1
    rows = load_notices(csv_path)
    assert {r["id"] for r in rows} == {"1", "2", "3"}


def test_append_with_no_new_notices_still_creates_file_with_header(tmp_path: Path):
    csv_path = tmp_path / "notices.csv"
    added = append_notices(csv_path, [])
    assert added == 0
    assert csv_path.exists()
    assert load_notices(csv_path) == []


def test_load_existing_ids_empty_when_missing(tmp_path: Path):
    assert load_existing_ids(tmp_path / "missing.csv") == set()
