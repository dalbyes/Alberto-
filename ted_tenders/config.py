"""Parametri di default per la ricerca: codici CPV, parole chiave multilingua,
paesi coperti da TED e categorie per la classificazione dei risultati.

IMPORTANTE: i codici CPV sotto sono quelli notoriamente associati a calzature
e abbigliamento protettivo/antinfortunistico nel vocabolario CPV UE. Prima di
un uso "in produzione" verificali sull'elenco ufficiale CPV
(https://simap.ted.europa.eu/web/simap/cpv) perche' alcune sotto-voci possono
essere state aggiornate. Per questo la ricerca non si basa SOLO sui CPV ma
anche su un set ampio di parole chiave full-text, cosi' da non perdere bandi
classificati con codici generici (es. 18800000-7 "Calzature") o testuali.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- Codici CPV rilevanti -----------------------------------------------

CPV_CODES: dict[str, str] = {
    "18800000-7": "Calzature (voce generica)",
    "18810000-0": "Calzature diverse da quelle sportive o protettive",
    "18830000-6": "Calzature protettive (voce generica)",
    "18831000-3": "Calzature con puntale rinforzato / varie protettive",
    "18833000-7": "Calzature con puntale metallico",
    "18834000-4": "Calzature in gomma",
    "18835000-1": "Calzature impermeabili",
    "35113400-3": "Indumenti di protezione e di sicurezza",
    "35113440-5": "Indumenti antincendio",
}

# --- Parole chiave multilingua, raggruppate per categoria ---------------

KEYWORDS: dict[str, list[str]] = {
    "vigili_del_fuoco": [
        "stivali vigili del fuoco",
        "calzature antincendio",
        "calzature vigili del fuoco",
        "firefighter boots",
        "fire fighting boots",
        "fire-fighters boots",
        "bottes sapeurs-pompiers",
        "bottes pompiers",
        "feuerwehrstiefel",
        "botas de bomberos",
        "calcado de bombeiros",
    ],
    "polizia": [
        "scarpe polizia",
        "calzature polizia",
        "calzature forze dell'ordine",
        "police footwear",
        "police boots",
        "chaussures de police",
        "bottes de police",
        "polizeischuhe",
        "polizeistiefel",
        "calzado policial",
        "calcado policial",
    ],
    "soccorso": [
        "calzature soccorso",
        "stivali soccorso",
        "calzature protezione civile",
        "rescue boots",
        "rescue footwear",
        "bottes de secours",
        "rettungsstiefel",
        "botas de rescate",
        "calcado de salvamento",
    ],
    "antinfortunistica_generica": [
        "calzature antinfortunistiche",
        "scarpe antinfortunistiche",
        "safety footwear",
        "safety boots",
        "protective footwear",
        "chaussures de securite",
        "sicherheitsschuhe",
        "calzado de seguridad",
    ],
}

# --- Paesi coperti da TED (codici ISO a 2 lettere) -----------------------
# Elenco indicativo: UE + alcuni paesi EFTA/SEE che pubblicano su TED.
# Lascia vuota la lista nella CLI (--countries "") per non filtrare per paese.

TED_COUNTRIES: list[str] = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "IS", "LI", "NO", "CH",
]


@dataclass(frozen=True)
class SearchDefaults:
    days_back: int = 30
    page_size: int = 100
    max_pages: int = 20
    mode: str = "broad"  # "broad" (CPV OR keyword) oppure "strict" (CPV AND keyword)
    countries: list[str] = field(default_factory=list)


DEFAULTS = SearchDefaults()

TED_API_BASE_URL = "https://api.ted.europa.eu/v3/notices/search"

# Nomi dei campi usati nella "expert query" dell'API TED v3.
# ATTENZIONE: verificali sulla documentazione ufficiale
# (https://docs.ted.europa.eu/api/latest/index.html) prima dell'uso: i nomi
# dei campi dell'API possono differire leggermente da quanto assunto qui,
# dato che questo modulo e' stato scritto senza accesso di rete diretto
# all'API nell'ambiente in cui e' stato creato.
FIELD_PUBLICATION_DATE = "publication-date"
FIELD_CPV = "classification-cpv"
FIELD_COUNTRY = "buyer-country"
FIELD_FULLTEXT = "FT"

# Campi richiesti nella risposta (da passare come "fields" nella richiesta).
RESPONSE_FIELDS = [
    "ND",  # notice document number (id)
    "TI",  # titolo
    "PD",  # data di pubblicazione
    "DD",  # scadenza (deadline)
    "CY",  # paese
    "OL",  # organo aggiudicatore / buyer name
    "classification-cpv",
    "val-total",
    "val-total-currency",
]
