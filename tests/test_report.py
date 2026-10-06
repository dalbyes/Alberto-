import datetime as dt

from ted_tenders.report import build_report


def _row(id_, category="vigili_del_fuoco", country="IT", buyer="Comune X", deadline=None, title="t"):
    return {
        "id": id_,
        "title": title,
        "buyer": buyer,
        "country": country,
        "cpv_codes": "",
        "publication_date": "",
        "deadline_date": deadline or "",
        "value": "",
        "currency": "",
        "category": category,
        "url": f"https://ted.europa.eu/udl?uri=TED:NOTICE:{id_}",
    }


def test_report_counts_by_category_and_country():
    rows = [
        _row("1", category="vigili_del_fuoco", country="IT"),
        _row("2", category="polizia", country="FR"),
        _row("3", category="vigili_del_fuoco", country="IT"),
    ]
    report = build_report(rows)
    assert "Totale bandi in archivio: **3**" in report
    assert "vigili_del_fuoco: 2" in report
    assert "polizia: 1" in report
    assert "IT: 2" in report
    assert "FR: 1" in report


def test_report_lists_only_future_deadlines_sorted():
    future1 = (dt.date.today() + dt.timedelta(days=10)).isoformat()
    future2 = (dt.date.today() + dt.timedelta(days=5)).isoformat()
    past = (dt.date.today() - dt.timedelta(days=5)).isoformat()
    rows = [
        _row("1", deadline=future1, title="Later"),
        _row("2", deadline=future2, title="Sooner"),
        _row("3", deadline=past, title="Expired"),
    ]
    report = build_report(rows)
    assert "Expired" not in report
    sooner_idx = report.index("Sooner")
    later_idx = report.index("Later")
    assert sooner_idx < later_idx


def test_report_handles_empty_input():
    report = build_report([])
    assert "Totale bandi in archivio: **0**" in report
    assert "nessuna scadenza futura" in report
