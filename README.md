# CAPSTONE 66 — AI Data Storytelling Dashboard

A Streamlit application that turns the public Our World in Data (OWID) CO₂ dataset
into exploratory questions, interactive visualizations, transparent calculations,
and a structured, human-checkable data story.

## Run locally

Python 3.12 or later is recommended for the current dependency versions.

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Or install `requirements.txt` in an existing environment and run:

```text
streamlit run app.py
```

On first run the app attempts the requested Grapher CSV URL, then transparently
falls back to the official OWID CO₂ repository if the Grapher URL is unavailable.
The downloaded source is saved as `data/co2.csv`; the cleaned copy is
`data/cleaned_co2.csv`. The original is never overwritten by cleaning. If both
downloads fail, the application explains the issue and offers CSV upload instead.

The default public source is a wide OWID table with `country`, `year`, `iso_code`,
and many measures. The app discovers the available CO₂ column and prefers `co2`.
The unfiltered total and trend use the dataset's reported `World` series when
available; otherwise they sum country rows. Country rankings and selected-country
comparisons exclude `OWID_` codes and, when ISO codes exist, rows without a code
(the current repository export represents aggregates with missing codes). CO₂
values in the source are expressed in million tonnes. Missing measurements are not
filled with zero. The verification page flags a difference between the World
aggregate and the sum of coded-country rows without treating it as an arithmetic
failure or inferring its cause.

## Features

- Dataset download or CSV upload, preview, schema, missingness, duplicate counts,
  conservative cleaning, before/after comparison, and CSV export.
- Rule-based question suggestions grouped by trends, comparisons, distributions,
  and relationships. Ten reusable prompts are included. Optional Gemini-generated
  suggestions are labeled as AI output.
- Persistent custom/finding notes with CSV and TXT exports.
- Interactive total-emissions trends, country rankings, country comparisons, and
  year/country filters.
- A structured data story with exact supporting calculations and no causal claims.
- Independent checks for totals, rankings, year-over-year changes, and chart totals.
- Locally persisted insight notes with CSV/TXT exports.
- Prompt library and academic presentation/video deliverables.

## Optional Gemini API

Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in the environment. Never commit a key.
Gemini requests are user-triggered and send only column names, aggregate summaries,
or verified findings—not the raw dataset. Local statistical analysis and
rule-based suggestions work without an API key.

```powershell
$env:GOOGLE_API_KEY = "your-key"
.venv\Scripts\python.exe -m streamlit run app.py
```

## Tests

```powershell
.venv\Scripts\python.exe -m unittest discover -v
```

The tests cover conservative cleaning, metric selection, KPI/ranking/change
calculations, chart aggregation and verification, question generation, story shape,
aggregate exclusion, and notes persistence/export.

## Academic deliverables

See `verification_report.md`, `before_after_analysis.md`, `insight_notes.md`,
`prompt_library.md`, `ai_tool_usage_log.md`, `presentation_outline.md`,
`video_walkthrough_script.md`, `final_demo_checklist.md`, and
`project_architecture.md`. The AI-tool log is an evidence template; it does not
claim that external tools were used.

## Source attribution

- Requested OWID Grapher export: https://ourworldindata.org/grapher/co2.csv
- Official OWID data repository fallback: https://github.com/owid/co2-data

See `data/source.txt` for the actual download URL and retrieval date.
