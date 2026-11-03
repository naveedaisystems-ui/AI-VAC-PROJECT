"""Generate dataset-specific academic reports from the preserved local source."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_storytelling.analysis import (
    build_story,
    total_by_year,
    total_series_scope,
    verify_analysis,
)
from data_storytelling.data import (
    DEFAULT_DATA_PATH,
    clean_dataset,
    load_dataset,
    metric_unit,
    select_emissions_metric,
)


def main() -> int:
    try:
        raw, source = load_dataset(DEFAULT_DATA_PATH)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Dataset not available; reports were not replaced: {exc}", file=sys.stderr)
        return 1

    cleaned, report = clean_dataset(raw)
    metric = select_emissions_metric(cleaned)
    years = sorted(cleaned["year"].dropna().astype(int).unique())
    year = years[-1]
    verification = verify_analysis(
        cleaned, metric, year, total_by_year(cleaned, metric)
    )
    cleaned.to_csv(ROOT / "data" / "cleaned_co2.csv", index=False)
    if source.startswith(("https://", "http://")):
        (ROOT / "data" / "source.txt").write_text(
            f"Source URL: {source}\nRetrieved: {date.today().isoformat()}\n",
            encoding="utf-8",
        )
    (ROOT / "before_after_analysis.md").write_text(
        _before_after(report, source), encoding="utf-8"
    )
    (ROOT / "verification_report.md").write_text(
        _verification(
            verification,
            report,
            metric,
            source,
            total_series_scope(cleaned, metric),
        ),
        encoding="utf-8",
    )
    (ROOT / "insight_notes.md").write_text(
        _insight_template(source, build_story(cleaned, metric, year)["findings"]),
        encoding="utf-8",
    )
    print(
        f"Generated reports from {source}: "
        f"{len(raw):,} source rows, {len(cleaned):,} cleaned rows; "
        f"verification={'PASS' if verification['all_passed'] else 'FAIL'}."
    )
    return 0


def _before_after(report: dict, source: str) -> str:
    before, after = report["before_shape"], report["after_shape"]
    operations = "\n".join(f"- {operation}" for operation in report["operations"])
    return f"""# Before/After Data Cleaning Analysis

Source: {source}

| Measure | Before cleaning | After cleaning |
|---|---:|---:|
| Rows | {before[0]:,} | {after[0]:,} |
| Columns | {before[1]:,} | {after[1]:,} |
| Missing cells | {report['missing_before']:,} | {report['missing_after']:,} |
| Exact duplicate rows | {report['duplicates_before']:,} | {report['duplicates_after']:,} |

## Cleaning operations

{operations}

Invalid entity/year rows removed: {report['invalid_keys_removed']:,}. Exact duplicates
removed: {report['duplicates_removed']:,}. Measurement gaps were retained rather than
imputed. Removing duplicate records prevents repeat counting; preserving gaps avoids
inventing measurements. These operations do not correct source coverage or reporting
method differences.
"""


def _verification(
    result: dict, report: dict, metric: str, source: str, scope: str
) -> str:
    checks = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} — {label}"
        for label, passed in result["checks"].items()
    )
    ranking = "| country | value |\n|---|---:|\n" + "\n".join(
        f"| {row.country} | {row.value:,.6f} |"
        for row in result["ranking"].itertuples(index=False)
    )
    return f"""# Verification Report

Source: {source}  
Dataset rows after cleaning: {report['after_shape'][0]:,}  
Measure: `{metric}`  
Verification year: {result['year']}

## Independent checks

{checks}

Recomputed {scope}: **{result['direct_total']:,.6f}** {metric_unit(metric)}.  
Dashboard KPI total: **{result['kpi_total']:,.6f}** {metric_unit(metric)}.

## Top country-level values

{ranking}

## Aggregate comparison

{_aggregate_comparison(result, metric)}

## Methodology

{result['methodology']} Year-over-year changes follow the same selected total
series. Chart data and KPI values are reconciled to the cleaned dataset. A passing
arithmetic check does not establish causation or validate the source's definitions.
"""


def _aggregate_comparison(result: dict, metric: str) -> str:
    comparison = result["aggregate_comparison"]
    if comparison is None:
        return "No reported World aggregate is available for this dataset/year."
    if comparison["matches"]:
        return "The reported World total matches the sum of coded country rows."
    return (
        f"Reported World total: {comparison['world_total']:,.6f} {metric_unit(metric)}.  \n"
        f"Sum of coded country rows: {comparison['country_total']:,.6f} "
        f"{metric_unit(metric)}.  \n"
        f"Difference (World minus country sum): **{comparison['difference']:+,.6f} "
        f"{metric_unit(metric)}**. This is flagged for review as a difference between "
        "source aggregations; it is not treated as a failed arithmetic check and no "
        "cause is inferred."
    )


def _insight_template(source: str, findings: list[str]) -> str:
    verified_findings = "\n".join(f"- {finding}" for finding in findings)
    return f"""# Insight Notes

Generated on {date.today().isoformat()} from the dataset recorded at `{source}`.
User notes are saved in `data/insight_notes.csv` and can be exported from the app.

## Dataset-derived findings

These are deterministic statistical observations from the cleaned dataset, not
AI-generated explanations. The selected-year total, ranking, annual change, and
chart aggregation checks are listed in `verification_report.md`.

{verified_findings}

## Finding template

- **Finding:** [Insert a checked observation]
- **Evidence:** [Exact values, years, and chart]
- **Method:** [Filter, aggregation, and comparison]
- **Source:** [{source}]({source})
- **Caveat:** [Missingness, coverage, or interpretation limit]
"""


if __name__ == "__main__":
    raise SystemExit(main())
