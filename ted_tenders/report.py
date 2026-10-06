"""Genera un riepilogo testuale/markdown a partire dai bandi salvati."""

from __future__ import annotations

import datetime as dt
from collections import Counter
from pathlib import Path

from .storage import load_notices


def _parse_date(value: str) -> dt.date | None:
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def build_report(rows: list[dict], top_n: int = 10) -> str:
    total = len(rows)
    by_category = Counter(r.get("category", "altro") or "altro" for r in rows)
    by_country = Counter(r.get("country", "") or "n/d" for r in rows)
    by_buyer = Counter(r.get("buyer", "") or "n/d" for r in rows)

    today = dt.date.today()
    upcoming = []
    for r in rows:
        deadline = _parse_date(r.get("deadline_date", ""))
        if deadline and deadline >= today:
            upcoming.append((deadline, r))
    upcoming.sort(key=lambda t: t[0])

    lines = [
        "# Report bandi TED — calzature vigili del fuoco / polizia / soccorso",
        "",
        f"Totale bandi in archivio: **{total}**",
        "",
        "## Per categoria",
    ]
    for category, count in by_category.most_common():
        lines.append(f"- {category}: {count}")

    lines += ["", f"## Primi {top_n} paesi per numero di bandi"]
    for country, count in by_country.most_common(top_n):
        lines.append(f"- {country}: {count}")

    lines += ["", f"## Primi {top_n} enti aggiudicatori"]
    for buyer, count in by_buyer.most_common(top_n):
        lines.append(f"- {buyer}: {count}")

    lines += ["", f"## Prossime scadenze (max {top_n})"]
    if not upcoming:
        lines.append("- nessuna scadenza futura in archivio")
    for deadline, r in upcoming[:top_n]:
        lines.append(
            f"- {deadline.isoformat()} — {r.get('title', '')} "
            f"({r.get('country', '')}, {r.get('buyer', '')}) — {r.get('url', '')}"
        )

    return "\n".join(lines) + "\n"


def write_report(csv_path: Path, report_path: Path, top_n: int = 10) -> str:
    rows = load_notices(csv_path)
    report = build_report(rows, top_n=top_n)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report
