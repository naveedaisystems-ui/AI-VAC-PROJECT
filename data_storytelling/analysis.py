"""Deterministic calculations used by dashboard charts and verification."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .data import get_entity_rows, metric_unit


def aggregate_by_year(
    frame: pd.DataFrame, metric: str, countries: list[str] | None = None
) -> pd.DataFrame:
    rows = get_entity_rows(frame)
    if countries:
        rows = rows.loc[rows[_entity_column(rows)].isin(countries)]
    return (
        rows.groupby(_year_column(rows), as_index=False)[metric]
        .sum(min_count=1)
        .rename(columns={_year_column(rows): "year", metric: "value"})
        .sort_values("year")
        .reset_index(drop=True)
    )


def world_aggregate_by_year(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Return the dataset's explicit World series, if one is available."""
    entity = _entity_column(frame)
    year = _year_column(frame)
    world_rows = frame.loc[
        frame[entity].astype("string").str.strip().str.casefold().eq("world"),
        [year, metric],
    ]
    if world_rows.empty:
        return pd.DataFrame(columns=["year", "value"])
    return (
        world_rows.groupby(year, as_index=False)[metric]
        .sum(min_count=1)
        .rename(columns={year: "year", metric: "value"})
        .sort_values("year")
        .reset_index(drop=True)
    )


def total_by_year(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Use a reported World series when available; otherwise sum country rows."""
    world = world_aggregate_by_year(frame, metric)
    return world if world["value"].notna().any() else aggregate_by_year(frame, metric)


def total_series_scope(frame: pd.DataFrame, metric: str) -> str:
    if world_aggregate_by_year(frame, metric)["value"].notna().any():
        return "reported World total"
    return "summed reported country-level total"


def compare_world_and_country_totals(
    frame: pd.DataFrame, metric: str, year: int
) -> dict[str, Any] | None:
    world = world_aggregate_by_year(frame, metric)
    if world.empty:
        return None
    world_values = world.loc[world["year"].eq(year), "value"]
    countries = aggregate_by_year(frame, metric)
    country_values = countries.loc[countries["year"].eq(year), "value"]
    if (
        world_values.empty
        or country_values.empty
        or pd.isna(world_values.iloc[0])
        or pd.isna(country_values.iloc[0])
    ):
        return None
    world_total = float(world_values.iloc[0])
    country_total = float(country_values.iloc[0])
    difference = world_total - country_total
    return {
        "world_total": world_total,
        "country_total": country_total,
        "difference": difference,
        "matches": bool(np.isclose(world_total, country_total, rtol=1e-10, atol=1e-10)),
    }


def country_ranking(
    frame: pd.DataFrame, metric: str, year: int, limit: int = 10
) -> pd.DataFrame:
    rows = get_entity_rows(frame)
    entity = _entity_column(rows)
    selected = rows.loc[rows[_year_column(rows)].eq(year), [entity, metric]]
    result = (
        selected.dropna(subset=[metric])
        .groupby(entity, as_index=False)[metric]
        .sum(min_count=1)
        .sort_values(metric, ascending=False, kind="stable")
        .head(limit)
        .reset_index(drop=True)
    )
    return result.rename(columns={entity: "country", metric: "value"})


def country_year_series(frame: pd.DataFrame, metric: str, country: str) -> pd.DataFrame:
    rows = get_entity_rows(frame)
    entity = _entity_column(rows)
    selected = rows.loc[rows[entity].eq(country), [_year_column(rows), metric]]
    return (
        selected.dropna(subset=[metric])
        .groupby(_year_column(rows), as_index=False)[metric]
        .sum(min_count=1)
        .rename(columns={_year_column(rows): "year", metric: "value"})
        .sort_values("year")
        .reset_index(drop=True)
    )


def annual_change_extremes(frame: pd.DataFrame, metric: str) -> dict[str, dict | None]:
    """Find the largest positive/negative changes across adjacent observed years."""
    annual = total_by_year(frame, metric)
    if len(annual) < 2:
        return {"increase": None, "decrease": None}
    changes = annual.copy()
    changes["previous_year"] = changes["year"].shift(1)
    changes["previous_value"] = changes["value"].shift(1)
    changes["change"] = changes["value"] - changes["previous_value"]
    changes = changes.loc[
        changes["year"].sub(changes["previous_year"]).eq(1)
        & changes["change"].notna()
    ]
    increases = changes.loc[changes["change"].gt(0)]
    decreases = changes.loc[changes["change"].lt(0)]

    def extreme(rows: pd.DataFrame, largest: bool) -> dict | None:
        if rows.empty:
            return None
        row = rows.loc[rows["change"].idxmax() if largest else rows["change"].idxmin()]
        return {
            "previous_year": int(row["previous_year"]),
            "year": int(row["year"]),
            "change": float(row["change"]),
        }

    return {
        "increase": extreme(increases, largest=True),
        "decrease": extreme(decreases, largest=False),
    }


def calculate_kpis(frame: pd.DataFrame, metric: str, year: int) -> dict[str, Any]:
    yearly = total_by_year(frame, metric)
    selected = yearly.loc[yearly["year"].eq(year), "value"]
    ranking = country_ranking(frame, metric, year, limit=1)
    previous = yearly.loc[yearly["year"].eq(year - 1), "value"]
    total = float(selected.iloc[0]) if not selected.empty else float("nan")
    previous_total = float(previous.iloc[0]) if not previous.empty else float("nan")
    change = (
        total - previous_total
        if np.isfinite(total) and np.isfinite(previous_total)
        else None
    )
    percent_change = (
        change / previous_total * 100
        if change is not None and previous_total != 0
        else None
    )
    return {
        "year": int(year),
        "total": total,
        "previous_year": int(year - 1) if not previous.empty else None,
        "previous_total": previous_total if not previous.empty else None,
        "change": change,
        "percent_change": percent_change,
        "top_country": str(ranking.iloc[0]["country"]) if not ranking.empty else None,
        "top_country_value": (
            float(ranking.iloc[0]["value"]) if not ranking.empty else None
        ),
    }


def generate_questions(frame: pd.DataFrame, metric: str) -> dict[str, list[str]]:
    years = pd.to_numeric(frame[_year_column(frame)], errors="coerce").dropna()
    first_year = int(years.min()) if not years.empty else "available"
    last_year = int(years.max()) if not years.empty else "available"
    entity = _entity_column(frame)
    entities = get_entity_rows(frame)[entity].dropna().nunique()
    questions = {
        "Trends": [
            f"How did total {metric} emissions change from {first_year} to {last_year}?",
            f"In which year did annual {metric} emissions reach their highest observed total?",
            f"Which year-to-year interval had the largest observed increase in {metric}?",
            f"How did {metric} emissions for the leading contributor change over time?",
        ],
        "Comparisons": [
            f"Which five countries had the highest {metric} emissions in {last_year}?",
            f"How do {metric} emissions compare among countries in {last_year}?",
            f"Which countries changed rank the most between {first_year} and {last_year}?",
            f"How does the selected country's {metric} total compare with the dataset total?",
        ],
        "Distributions": [
            f"How concentrated were {metric} emissions across reporting countries in {last_year}?",
            f"What is the median country-level {metric} value in {last_year}?",
            f"Which countries are statistical outliers in {metric} emissions in {last_year}?",
        ],
        "Relationships": [
            f"Across {entities:,} entities, how is {metric} associated with population?",
            f"How do per-capita {metric} emissions differ from total emissions rankings?",
            "Are observations missing more often in particular years or for particular countries?",
        ],
    }
    if "population" not in frame.columns:
        questions["Relationships"] = [
            question
            for question in questions["Relationships"]
            if "population" not in question
        ]
    return questions


def build_story(frame: pd.DataFrame, metric: str, year: int) -> dict[str, Any]:
    kpis = calculate_kpis(frame, metric, year)
    ranking = country_ranking(frame, metric, year, limit=5)
    yearly = total_by_year(frame, metric)
    if yearly.empty:
        raise ValueError("No valid annual total observations are available.")

    first = yearly.iloc[0]
    last = yearly.iloc[-1]
    trend = (
        float(last["value"]) - float(first["value"])
        if pd.notna(first["value"]) and pd.notna(last["value"])
        else None
    )
    if kpis["change"] is None:
        change_text = f"No prior-year comparison is available for {year}."
    else:
        direction = "increased" if kpis["change"] > 0 else "decreased"
        change_text = (
            f"From {year - 1} to {year}, the {total_series_scope(frame, metric)} "
            f"{direction} by {abs(kpis['change']):,.3f} {metric_unit(metric)} "
            f"({kpis['percent_change']:+.2f}% where defined)."
        )

    findings = [
        f"In {year}, the {total_series_scope(frame, metric)} for {metric} was "
        f"{kpis['total']:,.3f} {metric_unit(metric)}.",
        change_text,
    ]
    if not ranking.empty:
        leaders = ", ".join(
            f"{row.country} ({row.value:,.3f})"
            for row in ranking.itertuples(index=False)
        )
        findings.append(
            f"The five largest reported country totals in {year} were: {leaders}."
        )
    aggregate_comparison = compare_world_and_country_totals(frame, metric, year)
    if aggregate_comparison and not aggregate_comparison["matches"]:
        findings.append(
            f"In {year}, the reported World total differs from the sum of coded "
            f"country rows by {aggregate_comparison['difference']:+,.3f} "
            f"{metric_unit(metric)}. These are distinct source aggregations; "
            "the difference is flagged for review, not explained causally."
        )
    findings.append(
        f"Between the first and last years with {total_series_scope(frame, metric)} "
        f"({int(first['year'])}–{int(last['year'])}), this series "
        f"{'increased' if trend is not None and trend > 0 else 'decreased' if trend is not None and trend < 0 else 'did not change'}"
        + (
            f" by {abs(trend):,.3f} {metric_unit(metric)}."
            if trend is not None
            else "."
        )
    )
    extremes = annual_change_extremes(frame, metric)
    if extremes["increase"]:
        peak = extremes["increase"]
        findings.append(
            f"The largest observed increase between adjacent available years was "
            f"{peak['change']:,.3f} {metric_unit(metric)} from "
            f"{peak['previous_year']} to {peak['year']}."
        )
    if extremes["decrease"]:
        trough = extremes["decrease"]
        findings.append(
            f"The largest observed decrease between adjacent available years was "
            f"{abs(trough['change']):,.3f} {metric_unit(metric)} from "
            f"{trough['previous_year']} to {trough['year']}."
        )
    return {
        "introduction": (
            f"This story examines {metric} in the cleaned dataset for "
            f"{int(first['year'])}–{int(last['year'])}. It summarizes the "
            f"{total_series_scope(frame, metric)} where available; it does not "
            "infer causes."
        ),
        "findings": findings,
        "supporting_numbers": {
            "latest_year": int(year),
            "latest_total": kpis["total"],
            "previous_year_change": kpis["change"],
            "previous_year_percent_change": kpis["percent_change"],
            "top_countries": ranking.to_dict(orient="records"),
        },
        "conclusion": (
            "These calculations describe the selected measure and the available "
            "observations only. Trends and associations do not establish causation; "
            "review the source, missingness, and chart before presenting conclusions."
        ),
        "aggregate_comparison": aggregate_comparison,
    }


def verify_analysis(
    frame: pd.DataFrame, metric: str, year: int, chart_data: pd.DataFrame | None = None
) -> dict[str, Any]:
    """Independently cross-check totals, ranking, year changes, and chart aggregation."""
    rows = get_entity_rows(frame)
    year_column = _year_column(rows)
    entity_column = _entity_column(rows)
    selected = rows.loc[rows[year_column].eq(year), [entity_column, metric]].dropna(
        subset=[metric]
    )
    manual_total = float(selected[metric].sum(min_count=1))
    kpis = calculate_kpis(frame, metric, year)
    grouped = (
        selected.groupby(entity_column)[metric]
        .sum(min_count=1)
        .sort_values(ascending=False, kind="stable")
    )
    expected_ranking = grouped.head(10)
    observed_ranking = country_ranking(frame, metric, year, limit=10)
    ranking_matches = (
        expected_ranking.index.tolist() == observed_ranking["country"].tolist()
        and np.allclose(
            expected_ranking.to_numpy(dtype=float),
            observed_ranking["value"].to_numpy(dtype=float),
            rtol=1e-10,
            atol=1e-10,
        )
    )
    annual = total_by_year(frame, metric)
    world_rows = world_aggregate_by_year(frame, metric)
    if not world_rows.empty:
        entity_column = _entity_column(frame)
        source_rows = frame.loc[
            frame[entity_column].astype("string").str.strip().str.casefold().eq("world")
            & frame[_year_column(frame)].eq(year),
            metric,
        ].dropna()
        manual_total = float(source_rows.sum()) if not source_rows.empty else float("nan")
    else:
        manual_total = float(selected[metric].sum(min_count=1))
    annual_for_year = annual.loc[annual["year"].eq(year), "value"]
    manual_chart_total = float(annual_for_year.iloc[0]) if not annual_for_year.empty else float("nan")
    chart_matches = True
    if chart_data is not None and not chart_data.empty and "year" in chart_data.columns:
        chart_year_total = chart_data.loc[chart_data["year"].eq(year), "value"]
        chart_matches = bool(
            chart_year_total.empty
            or np.isclose(
                float(chart_year_total.iloc[0]), manual_chart_total, rtol=1e-10, atol=1e-10
            )
        )
    checks = {
        "KPI total matches direct source sum": bool(
            np.isclose(kpis["total"], manual_total, rtol=1e-10, atol=1e-10)
        ),
        "Country ranking matches independent grouping": bool(ranking_matches),
        "Year-over-year change matches annual totals": bool(
            kpis["change"] is None
            or np.isclose(
                kpis["change"],
                manual_chart_total
                - float(
                    annual.loc[annual["year"].eq(year - 1), "value"].iloc[0]
                ),
                rtol=1e-10,
                atol=1e-10,
            )
        ),
        "Chart annual totals match source aggregation": bool(chart_matches),
    }
    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "year": year,
        "metric": metric,
        "direct_total": manual_total,
        "kpi_total": kpis["total"],
        "ranking": observed_ranking,
        "aggregate_comparison": compare_world_and_country_totals(
            frame, metric, year
        ),
        "methodology": (
            "The unfiltered total/time series uses the dataset's explicit World "
            "aggregate when it has observations; otherwise it sums country rows. "
            "Country rankings and selected-country comparisons exclude OWID_ "
            "aggregate codes and, when ISO codes are present, rows with missing "
            "ISO codes. Missing metric values are excluded, not imputed."
        ),
    }


def _entity_column(frame: pd.DataFrame) -> str:
    for column in frame.columns:
        if str(column).strip().lower() in {"country", "entity"}:
            return str(column)
    raise ValueError("No country/entity column is available.")


def _year_column(frame: pd.DataFrame) -> str:
    for column in frame.columns:
        if str(column).strip().lower() == "year":
            return str(column)
    raise ValueError("No year column is available.")
