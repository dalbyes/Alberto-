from ted_tenders.classify import categorize
from ted_tenders.models import Notice


def test_notice_from_raw_basic_fields():
    raw = {
        "ND": "123456-2025",
        "TI": ["Fornitura stivali vigili del fuoco"],
        "OL": "Comune di Esempio",
        "CY": "IT",
        "PD": "2025-06-01",
        "DD": "2025-07-15",
        "classification-cpv": ["18830000-6", "35113440-5"],
        "val-total": "150000",
        "val-total-currency": "EUR",
    }
    n = Notice.from_raw(raw)
    assert n.id == "123456-2025"
    assert n.title == "Fornitura stivali vigili del fuoco"
    assert n.buyer == "Comune di Esempio"
    assert n.country == "IT"
    assert n.cpv_codes == "18830000-6;35113440-5"
    assert n.value == "150000"
    assert n.currency == "EUR"
    assert n.url.endswith("123456-2025")


def test_notice_from_raw_handles_missing_fields():
    n = Notice.from_raw({"ND": "1"})
    assert n.id == "1"
    assert n.title == ""
    assert n.url == "https://ted.europa.eu/udl?uri=TED:NOTICE:1"


def test_categorize_firefighter():
    assert categorize("Fornitura stivali vigili del fuoco per il comando regionale") == "vigili_del_fuoco"


def test_categorize_police():
    assert categorize("Procurement of police footwear for metropolitan force") == "polizia"


def test_categorize_rescue():
    assert categorize("Appalto calzature soccorso alpino") == "soccorso"


def test_categorize_generic_safety():
    assert categorize("Fornitura di scarpe antinfortunistiche per il personale") == "antinfortunistica_generica"


def test_categorize_unrelated():
    assert categorize("Fornitura di cancelleria per ufficio") == "altro"
