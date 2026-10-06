"""Client HTTP minimale per l'API di ricerca di TED (Tenders Electronic Daily).

L'API pubblica di ricerca notizie non richiede autenticazione per le query
di base. Vedi https://docs.ted.europa.eu/api/latest/index.html per i dettagli
aggiornati (endpoint, paginazione, limiti di frequenza).
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import requests

from . import config
from .query_builder import build_request_payload


class TedApiError(RuntimeError):
    pass


class TedClient:
    def __init__(
        self,
        base_url: str = config.TED_API_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.session = session or requests.Session()

    def _post(self, payload: dict) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(self.base_url, json=payload, timeout=self.timeout)
                if resp.status_code == 429:
                    raise TedApiError(f"rate limited (429): {resp.text[:300]}")
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, TedApiError) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * attempt)
        raise TedApiError(f"richiesta TED fallita dopo {self.max_retries} tentativi: {last_exc}")

    def search_page(self, query: str, page: int, page_size: int, fields: list[str] | None = None) -> dict:
        payload = build_request_payload(query, page=page, page_size=page_size, fields=fields)
        return self._post(payload)

    def search_all(
        self,
        query: str,
        page_size: int = config.DEFAULTS.page_size,
        max_pages: int = config.DEFAULTS.max_pages,
        fields: list[str] | None = None,
    ) -> Iterator[dict]:
        """Itera su tutte le notizie, pagina per pagina, fino a max_pages o
        all'esaurimento dei risultati.
        """
        for page in range(1, max_pages + 1):
            data = self.search_page(query, page=page, page_size=page_size, fields=fields)
            notices = data.get("notices") or []
            if not notices:
                return
            yield from notices
            total = data.get("totalNoticeCount")
            if total is not None and page * page_size >= total:
                return
