"""Costruisce la "expert query" da inviare all'API TED v3 a partire da
codici CPV, parole chiave, intervallo di date e paesi.
"""

from __future__ import annotations

import datetime as dt

from . import config


def _cpv_clause(cpv_codes: list[str]) -> str:
    codes = ", ".join(c.split("-")[0] for c in cpv_codes)
    return f"{config.FIELD_CPV} IN ({codes})"


def _keyword_clause(keywords: list[str]) -> str:
    parts = [f'{config.FIELD_FULLTEXT} ~ "{kw}"' for kw in keywords]
    return "(" + " OR ".join(parts) + ")"


def _flatten_keywords(keyword_groups: dict[str, list[str]]) -> list[str]:
    seen: set[str] = set()
    flat: list[str] = []
    for group in keyword_groups.values():
        for kw in group:
            if kw not in seen:
                seen.add(kw)
                flat.append(kw)
    return flat


def build_query(
    mode: str = config.DEFAULTS.mode,
    cpv_codes: list[str] | None = None,
    keyword_groups: dict[str, list[str]] | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    countries: list[str] | None = None,
) -> str:
    """Compone la query esperta TED.

    mode="broad"  -> (CPV) OR (parole chiave)   [massima copertura]
    mode="strict" -> (CPV) AND (parole chiave)  [meno falsi positivi]
    """
    if mode not in ("broad", "strict"):
        raise ValueError(f"mode non valido: {mode!r} (attesi: 'broad', 'strict')")

    cpv_codes = cpv_codes if cpv_codes is not None else list(config.CPV_CODES)
    keyword_groups = keyword_groups if keyword_groups is not None else config.KEYWORDS
    keywords = _flatten_keywords(keyword_groups)

    if not cpv_codes and not keywords:
        raise ValueError("servono almeno codici CPV o parole chiave")

    clauses = []
    if cpv_codes and keywords:
        joiner = " OR " if mode == "broad" else " AND "
        clauses.append(f"({_cpv_clause(cpv_codes)}{joiner}{_keyword_clause(keywords)})")
    elif cpv_codes:
        clauses.append(_cpv_clause(cpv_codes))
    else:
        clauses.append(_keyword_clause(keywords))

    if date_from is not None:
        clauses.append(f"{config.FIELD_PUBLICATION_DATE} >= {date_from:%Y%m%d}")
    if date_to is not None:
        clauses.append(f"{config.FIELD_PUBLICATION_DATE} <= {date_to:%Y%m%d}")

    if countries:
        country_list = ", ".join(countries)
        clauses.append(f"{config.FIELD_COUNTRY} IN ({country_list})")

    return " AND ".join(clauses)


def build_request_payload(
    query: str,
    page: int = 1,
    page_size: int = config.DEFAULTS.page_size,
    fields: list[str] | None = None,
) -> dict:
    return {
        "query": query,
        "fields": fields if fields is not None else list(config.RESPONSE_FIELDS),
        "page": page,
        "limit": page_size,
        "scope": "ALL",
    }
