"""Small local persistence helpers for user-authored insight notes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

NOTES_COLUMNS = ["id", "created_at_utc", "title", "note", "source"]


def load_notes(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=NOTES_COLUMNS)
    notes = pd.read_csv(path, dtype="string", keep_default_na=False)
    for column in NOTES_COLUMNS:
        if column not in notes.columns:
            notes[column] = ""
    return notes[NOTES_COLUMNS]


def save_note(path: Path, title: str, note: str, source: str = "User note") -> pd.DataFrame:
    title = title.strip()
    note = note.strip()
    if not title or not note:
        raise ValueError("Both a title and note are required.")
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_notes(path)
    entry = pd.DataFrame(
        [
            {
                "id": str(uuid4()),
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "title": title,
                "note": note,
                "source": source,
            }
        ]
    )
    updated = pd.concat([existing, entry], ignore_index=True)
    updated.to_csv(path, index=False)
    return updated


def export_notes(notes: pd.DataFrame, path: Path, format: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if format == "csv":
        notes.to_csv(path, index=False)
    elif format == "txt":
        lines = [
            f"{row.title} ({row.created_at_utc})\n{row.note}\nSource: {row.source}"
            for row in notes.itertuples(index=False)
        ]
        path.write_text("\n\n".join(lines), encoding="utf-8")
    else:
        raise ValueError("Export format must be 'csv' or 'txt'.")
    return path


def notes_as_text(notes: pd.DataFrame) -> str:
    return "\n\n".join(
        f"{row.title} ({row.created_at_utc})\n{row.note}\nSource: {row.source}"
        for row in notes.itertuples(index=False)
    )
