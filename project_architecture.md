# Project Architecture

```text
app.py                         Streamlit pages, filters, charts, and interactions
data_storytelling/
  data.py                      Download, schema validation, cleaning, row selection
  analysis.py                  Metrics, rankings, questions, story, verification
  ai.py                        Optional user-triggered Gemini integration
  notes.py                     Local note persistence and text/CSV exports
  prompts.py                   Reusable responsible prompt library
data/
  co2.csv                      Preserved public source dataset
  cleaned_co2.csv              Conservative cleaned copy
  source.txt                   Actual source URL and retrieval date
tests/
  test_data_storytelling.py    Unit tests for calculation and persistence helpers
```

## Data flow

The app loads the local preserved source or downloads the requested OWID Grapher
CSV. If that endpoint is unavailable, it tries the official OWID data repository
and records the actual source. A schema check rejects invalid responses. Cleaning
normalizes entity/year keys, removes invalid keys and exact duplicate records, and
retains missing measurement values. Country rankings exclude `OWID_` aggregate
codes and, when ISO codes are present, rows without an ISO code (aggregate rows in
the current export). Unfiltered totals use the reported `World` series when it has
observations; selected-country charts and rankings use country rows.

Chart, KPI, question, story, and verification calculations live in importable
Python modules rather than Streamlit callbacks. The verification page independently
recalculates the displayed total, ranking, annual change, and chart aggregation.
Notes are stored locally in `data/insight_notes.csv`; users can download CSV/TXT
copies. User-uploaded files remain in memory for the active Streamlit session.

Gemini is an optional presentation layer for generated questions or explanations.
Requests are made only after a user action, using an environment key and aggregate
metadata/findings rather than uploading raw rows. Deterministic calculations and
rule-based questions do not require an API key.

## Limitations

Country reporting coverage and definitions vary by year. The default emissions
measure is chosen from the dataset's available CO₂ columns. A reported World
aggregate can differ from sums of countries when reporting coverage differs. No
missing measurements are imputed, and no causal claims are generated from
observational patterns.
