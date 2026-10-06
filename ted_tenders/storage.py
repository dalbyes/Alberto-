"""Lettura/scrittura del CSV dei bandi, con deduplica per id."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import CSV_COLUMNS, Notice


def load_existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["id"] for row in reader if row.get("id")}


def load_notices(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def append_notices(path: Path, notices: list[Notice]) -> int:
    """Aggiunge i bandi non ancora presenti nel CSV (dedup per id).

    Ritorna il numero di righe effettivamente aggiunte.
    """
    existing_ids = load_existing_ids(path)
    new_rows = [n.to_csv_row() for n in notices if n.id and n.id not in existing_ids]
    if not new_rows:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)
    return len(new_rows)
