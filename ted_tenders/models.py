"""Modello dati per un bando (notice) TED, normalizzato dai campi grezzi
restituiti dall'API.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

CSV_COLUMNS = [
    "id",
    "title",
    "buyer",
    "country",
    "cpv_codes",
    "publication_date",
    "deadline_date",
    "value",
    "currency",
    "category",
    "url",
]


def _first(value):
    """L'API TED a volte restituisce liste (es. titolo multilingua)."""
    if isinstance(value, list):
        return value[0] if value else ""
    return value if value is not None else ""


@dataclass
class Notice:
    id: str
    title: str = ""
    buyer: str = ""
    country: str = ""
    cpv_codes: str = ""
    publication_date: str = ""
    deadline_date: str = ""
    value: str = ""
    currency: str = ""
    category: str = ""
    url: str = ""

    @classmethod
    def from_raw(cls, raw: dict) -> "Notice":
        notice_id = str(_first(raw.get("ND", "")))
        cpv = raw.get("classification-cpv", [])
        if isinstance(cpv, str):
            cpv = [cpv]
        return cls(
            id=notice_id,
            title=str(_first(raw.get("TI", ""))),
            buyer=str(_first(raw.get("OL", ""))),
            country=str(_first(raw.get("CY", ""))),
            cpv_codes=";".join(str(c) for c in cpv),
            publication_date=str(_first(raw.get("PD", ""))),
            deadline_date=str(_first(raw.get("DD", ""))),
            value=str(_first(raw.get("val-total", ""))),
            currency=str(_first(raw.get("val-total-currency", ""))),
            url=f"https://ted.europa.eu/udl?uri=TED:NOTICE:{notice_id}" if notice_id else "",
        )

    def to_csv_row(self) -> dict:
        return {col: getattr(self, col) for col in CSV_COLUMNS}


assert {f.name for f in fields(Notice)} >= set(CSV_COLUMNS)
