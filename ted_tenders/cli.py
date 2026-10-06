"""CLI: cerca bandi TED e genera report.

Esempi:
    python -m ted_tenders.cli search --days-back 30 --countries IT,FR,DE
    python -m ted_tenders.cli search --dry-run
    python -m ted_tenders.cli report
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from . import config
from .classify import categorize
from .client import TedApiError, TedClient
from .models import Notice
from .query_builder import build_query
from .report import write_report
from .storage import append_notices

DEFAULT_CSV = Path("data/notices.csv")
DEFAULT_REPORT = Path("data/report.md")


def _parse_countries(value: str | None) -> list[str]:
    if not value:
        return []
    return [c.strip().upper() for c in value.split(",") if c.strip()]


def cmd_search(args: argparse.Namespace) -> int:
    date_to = dt.date.today()
    date_from = date_to - dt.timedelta(days=args.days_back)
    countries = _parse_countries(args.countries)

    query = build_query(
        mode=args.mode,
        date_from=date_from,
        date_to=date_to,
        countries=countries,
    )

    print(f"Query TED ({args.mode}):\n  {query}\n")

    if args.dry_run:
        print("(--dry-run: nessuna richiesta HTTP inviata)")
        return 0

    client = TedClient()
    try:
        raw_notices = list(
            client.search_all(query, page_size=args.page_size, max_pages=args.max_pages)
        )
    except TedApiError as exc:
        print(f"Errore nella ricerca TED: {exc}", file=sys.stderr)
        return 1

    notices = []
    for raw in raw_notices:
        n = Notice.from_raw(raw)
        n.category = categorize(n.title)
        notices.append(n)

    added = append_notices(args.out, notices)
    print(f"Bandi trovati: {len(notices)} — nuovi salvati in {args.out}: {added}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    report = write_report(args.input, args.out, top_n=args.top)
    print(report)
    print(f"Report salvato in {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ted_tenders",
        description="Analizza i bandi pubblici europei (TED) per calzature "
        "vigili del fuoco, polizia e soccorso.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="cerca nuovi bandi su TED e li salva su CSV")
    p_search.add_argument("--days-back", type=int, default=config.DEFAULTS.days_back)
    p_search.add_argument(
        "--countries",
        default="",
        help="lista separata da virgole di codici paese ISO (es. IT,FR,DE); vuoto = tutti",
    )
    p_search.add_argument("--mode", choices=["broad", "strict"], default=config.DEFAULTS.mode)
    p_search.add_argument("--page-size", type=int, default=config.DEFAULTS.page_size)
    p_search.add_argument("--max-pages", type=int, default=config.DEFAULTS.max_pages)
    p_search.add_argument("--out", type=Path, default=DEFAULT_CSV)
    p_search.add_argument(
        "--dry-run", action="store_true", help="mostra solo la query, senza chiamare l'API"
    )
    p_search.set_defaults(func=cmd_search)

    p_report = sub.add_parser("report", help="genera un report dai bandi salvati")
    p_report.add_argument("--input", type=Path, default=DEFAULT_CSV)
    p_report.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    p_report.add_argument("--top", type=int, default=10)
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
