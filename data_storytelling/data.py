"""Dataset download, inspection, and conservative cleaning utilities."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

PRIMARY_DATA_URL = "https://ourworldindata.org/grapher/co2.csv"
OFFICIAL_REPOSITORY_URL = (
    "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
)
DEFAULT_DATA_PATH = Path("data") / "co2.csv"
CLEANED_DATA_PATH = Path("data") / "cleaned_co2.csv"
SOURCE_METADATA_NAME = "source.txt"
EMISSIONS_PREFERENCE = (
    "co2",
    "co2_including_luc",
    "consumption_co2",
    "cement_co2",
    "coal_co2",
    "oil_co2",
    "gas_co2",
)
MASS_EMISSIONS_METRICS = {
    "co2",
    "co2_including_luc",
    "consumption_co2",
    "cement_co2",
    "coal_co2",
    "oil_co2",
    "gas_co2",
    "flaring_co2",
    "land_use_change_co2",
    "other_industry_co2",
}


def _read_csv_response(url: str, timeout: int = 45) -> pd.DataFrame:
    request = Request(url, headers={"User-Agent": "AI-Data-Storytelling-Dashboard/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return pd.read_csv(response, low_memory=False)


def download_dataset(destination: Path = DEFAULT_DATA_PATH) -> tuple[pd.DataFrame, str]:
    """Download the requested Grapher CSV, then an official OWID repository copy."""
    failures: list[str] = []
    for url in (PRIMARY_DATA_URL, OFFICIAL_REPOSITORY_URL):
        try:
            frame = _read_csv_response(url)
            validate_dataset(frame)
            destination.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(destination, index=False)
            (destination.parent / SOURCE_METADATA_NAME).write_text(
                f"Source URL: {url}\nRetrieved: {date.today().isoformat()}\n",
                encoding="utf-8",
            )
            return frame, url
        except (HTTPError, URLError, TimeoutError, OSError, pd.errors.ParserError, ValueError) as exc:
            failures.append(f"{url}: {exc}")

    raise RuntimeError(
        "The Our World in Data CO₂ dataset could not be downloaded. "
        "The requested Grapher URL and OWID's official repository source both failed. "
        "Upload a CSV with at least a country/entity column, a year column, and a "
        "numeric emissions column to continue. Details: "
        + " | ".join(failures)
    )


def validate_dataset(frame: pd.DataFrame) -> None:
    """Reject non-CSV responses and files without usable entity/time fields."""
    normalized = {str(column).strip().lower() for column in frame.columns}
    if not ({"country", "entity"} & normalized):
        raise ValueError("CSV must include a 'country' or 'entity' column.")
    if "year" not in normalized:
        raise ValueError("CSV must include a 'year' column.")
    if not any(
        pd.api.types.is_numeric_dtype(frame[column])
        and str(column).strip().lower() not in {"year"}
        for column in frame.columns
    ):
        raise ValueError("CSV must include at least one numeric measurement column.")


def load_dataset(path: Path = DEFAULT_DATA_PATH) -> tuple[pd.DataFrame, str]:
    """Read the preserved local source, downloading it only when it is absent."""
    if path.exists():
        frame = pd.read_csv(path, low_memory=False)
        validate_dataset(frame)
        metadata_path = path.parent / SOURCE_METADATA_NAME
        if path == DEFAULT_DATA_PATH and metadata_path.exists():
            for line in metadata_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("Source URL: "):
                    source = line.removeprefix("Source URL: ").strip()
                    if source.startswith(("https://", "http://")):
                        return frame, source
        return frame, str(path)
    return download_dataset(path)


def clean_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Remove exact duplicates and invalid entity/year keys; retain measurement gaps."""
    if raw.empty:
        raise ValueError("The uploaded dataset has no rows.")

    frame = raw.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    normalized = {column.lower(): column for column in frame.columns}
    entity_column = normalized.get("country") or normalized.get("entity")
    year_column = normalized.get("year")
    if entity_column is None or year_column is None:
        validate_dataset(frame)
        raise ValueError("Could not identify entity and year columns.")
    canonical_entity = "country" if entity_column.lower() == "country" else "entity"
    rename_columns = {
        entity_column: canonical_entity,
        year_column: "year",
    }
    iso_column = normalized.get("iso_code")
    if iso_column is not None:
        rename_columns[iso_column] = "iso_code"
    canonical_columns = [
        rename_columns.get(column, column) for column in frame.columns
    ]
    if len(canonical_columns) != len(set(canonical_columns)):
        raise ValueError(
            "Column-name normalization would create duplicate columns. "
            "Rename the conflicting headers in the CSV."
        )
    frame = frame.rename(columns=rename_columns)
    entity_column = canonical_entity
    year_column = "year"

    before_shape = frame.shape
    missing_before = int(frame.isna().sum().sum())
    duplicates_before = int(frame.duplicated().sum())
    operations: list[str] = []

    frame[entity_column] = frame[entity_column].astype("string").str.strip()
    frame[year_column] = pd.to_numeric(frame[year_column], errors="coerce")

    invalid_key = (
        frame[entity_column].isna()
        | frame[entity_column].eq("")
        | frame[year_column].isna()
    )
    invalid_count = int(invalid_key.sum())
    if invalid_count:
        frame = frame.loc[~invalid_key].copy()
        operations.append(f"Removed {invalid_count:,} rows with a missing entity or year.")

    duplicate_count = int(frame.duplicated().sum())
    if duplicate_count:
        frame = frame.drop_duplicates().copy()
        operations.append(f"Removed {duplicate_count:,} exact duplicate rows.")

    frame[year_column] = frame[year_column].astype("int64")
    frame = frame.reset_index(drop=True)
    if not operations:
        operations.append(
            "No rows were removed; measurement missing values were retained rather than imputed."
        )
    if missing_before and not any("missing values" in op for op in operations):
        operations.append(
            "Measurement values were not imputed; missing-value counts remain visible."
        )

    report: dict[str, Any] = {
        "before_shape": before_shape,
        "after_shape": frame.shape,
        "missing_before": missing_before,
        "missing_after": int(frame.isna().sum().sum()),
        "duplicates_before": duplicates_before,
        "duplicates_after": int(frame.duplicated().sum()),
        "invalid_keys_removed": invalid_count,
        "duplicates_removed": duplicate_count,
        "operations": operations,
        "entity_column": entity_column,
        "year_column": year_column,
    }
    return frame, report


def select_emissions_metric(frame: pd.DataFrame) -> str:
    """Pick a supported emissions measure based on real numeric observations."""
    numeric = {
        str(column).strip().lower(): column
        for column in frame.select_dtypes(include=np.number).columns
    }
    for preferred in EMISSIONS_PREFERENCE:
        column = numeric.get(preferred)
        if column is not None and frame[column].notna().any():
            return str(column)

    candidates = [
        column
        for column in frame.select_dtypes(include=np.number).columns
        if "co2" in str(column).lower() and "per_" not in str(column).lower()
    ]
    for column in candidates:
        if frame[column].notna().any():
            return str(column)
    raise ValueError(
        "No non-empty numeric CO₂ emissions column was found. "
        "Choose a CSV with a numeric column whose name contains 'co2'."
    )


def metric_unit(metric: str) -> str:
    """Return a known OWID unit; do not guess units for uploaded metrics."""
    if metric.strip().lower() in MASS_EMISSIONS_METRICS:
        return "million tonnes of CO₂"
    return "source units (check dataset metadata)"


def get_entity_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Exclude OWID aggregates, including rows with an empty ISO code."""
    entity_column = _entity_column(frame)
    if "iso_code" not in frame.columns:
        return frame.loc[frame[entity_column].notna()].copy()
    codes = frame["iso_code"].astype("string")
    valid_rows = frame[entity_column].notna() & ~codes.str.startswith(
        "OWID_", na=False
    )
    if codes.notna().any():
        valid_rows &= codes.notna()
    return frame.loc[valid_rows].copy()


def _entity_column(frame: pd.DataFrame) -> str:
    columns = {str(column).strip().lower(): str(column) for column in frame.columns}
    entity_column = columns.get("country") or columns.get("entity")
    if entity_column is None:
        raise ValueError("No country/entity column is available.")
    return entity_column


def _year_column(frame: pd.DataFrame) -> str:
    for column in frame.columns:
        if str(column).strip().lower() == "year":
            return str(column)
    raise ValueError("No year column is available.")
