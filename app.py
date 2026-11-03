"""AI Data Storytelling Dashboard — Streamlit entry point."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from data_storytelling.ai import (
    gemini_available,
    generate_gemini_text,
    question_prompt,
)
from data_storytelling.analysis import (
    aggregate_by_year,
    build_story,
    country_ranking,
    generate_questions,
    total_by_year,
    verify_analysis,
)
from data_storytelling.data import (
    CLEANED_DATA_PATH,
    DEFAULT_DATA_PATH,
    clean_dataset,
    get_entity_rows,
    load_dataset,
    metric_unit,
    select_emissions_metric,
)
from data_storytelling.notes import load_notes, notes_as_text, save_note
from data_storytelling.prompts import PROMPTS

st.set_page_config(
    page_title="AI Data Storytelling | CO₂ Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --ink: #172b4d;
        --body: #344054;
        --muted: #526277;
        --navy: #102a43;
        --navy-raised: #183b5b;
        --teal: #087f8c;
        --teal-hover: #066873;
        --border: #cbd5e1;
        --canvas: #f5f7fa;
        --surface: #ffffff;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        color: var(--body) !important;
        background: var(--canvas) !important;
    }
    [data-testid="stHeader"] {
        color: var(--ink) !important;
        background: var(--canvas) !important;
    }
    [data-testid="stToolbar"] { background: transparent !important; }
    [data-testid="stMainBlockContainer"] { padding-top: 2rem; }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--ink) !important;
    }
    p, li, label, [data-testid="stCaptionContainer"],
    [data-testid="stMarkdownContainer"] {
        color: var(--body);
    }
    a { color: #056b8b !important; }
    a:hover { color: #034f69 !important; }

    [data-testid="stSidebar"] {
        color: #f8fafc !important;
        background: var(--navy) !important;
        border-right: 1px solid #294763;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #d4dfeb !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
        border-radius: 8px;
        padding: .2rem .35rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
        background: #1d4263;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        color: #f8fafc !important;
        background: var(--navy-raised) !important;
        border: 1px dashed #91a8bd !important;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        color: #ffffff !important;
        background: var(--teal) !important;
        border-color: var(--teal) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: var(--navy-raised) !important;
        border: 1px solid #365874 !important;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p {
        color: #f8fafc !important;
    }

    .hero {
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        color: #ffffff !important;
        background: linear-gradient(110deg, #123a52, #087f8c);
        margin-bottom: 1.1rem;
        box-shadow: 0 8px 24px #102a431a;
    }
    .hero h1 { margin: 0 0 .35rem; color: #ffffff !important; font-size: 1.9rem; }
    .hero p { margin: 0; color: #e7f5f5 !important; }

    [data-testid="stMetric"] {
        color: var(--ink) !important;
        background: var(--surface) !important;
        border: 1px solid #d9e2ec !important;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 3px 12px #18364b0d;
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stMetric"] [data-testid="stMetricLabel"] *,
    [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetric"] [data-testid="stMetricValue"] *,
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: var(--ink) !important;
        opacity: 1 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        font-weight: 600;
    }

    [data-testid="stMain"] input:not([type="checkbox"]):not([type="radio"]),
    [data-testid="stMain"] textarea,
    [data-testid="stMain"] [data-baseweb="select"] > div {
        color: #1f2937 !important;
        background: #ffffff !important;
        border-color: var(--border) !important;
    }
    [data-testid="stMain"] input::placeholder,
    [data-testid="stMain"] textarea::placeholder {
        color: #66758a !important;
        opacity: 1;
    }
    [data-testid="stMain"] [data-baseweb="select"] *,
    [data-testid="stMain"] [role="combobox"] {
        color: #1f2937 !important;
    }
    [data-testid="stMain"] [data-baseweb="tag"] {
        color: #123a52 !important;
        background: #e5f3f4 !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [role="listbox"] {
        color: #1f2937 !important;
        background: #ffffff !important;
        border-color: var(--border) !important;
    }
    [role="option"] { color: #1f2937 !important; }
    [role="option"]:hover,
    [aria-selected="true"][role="option"] {
        color: var(--ink) !important;
        background: #e8f2f5 !important;
    }
    [data-testid="stMain"] [data-testid="stCheckbox"] label,
    [data-testid="stMain"] [data-testid="stRadio"] label {
        color: var(--body) !important;
    }

    [data-testid="stMain"] .stButton > button,
    [data-testid="stMain"] [data-testid="stDownloadButton"] > button,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button {
        color: #ffffff !important;
        background: var(--teal) !important;
        border: 1px solid var(--teal) !important;
        border-radius: 8px;
        font-weight: 600;
        transition: background-color .15s ease, box-shadow .15s ease;
    }
    [data-testid="stMain"] .stButton > button:hover,
    [data-testid="stMain"] [data-testid="stDownloadButton"] > button:hover,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover {
        color: #ffffff !important;
        background: var(--teal-hover) !important;
        border-color: var(--teal-hover) !important;
        box-shadow: 0 2px 8px #087f8c33;
    }
    [data-testid="stMain"] button:focus-visible,
    [data-testid="stSidebar"] button:focus-visible,
    [data-testid="stMain"] input:focus-visible,
    [data-testid="stMain"] textarea:focus-visible {
        outline: 3px solid #45b7c1 !important;
        outline-offset: 2px;
    }

    [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
        color: var(--body) !important;
        background: #ffffff !important;
        border: 1px dashed #8a9bad !important;
        border-radius: 10px;
    }
    [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] * {
        color: var(--body) !important;
    }
    [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] button {
        color: #ffffff !important;
        background: var(--teal) !important;
        border-color: var(--teal) !important;
    }

    [data-testid="stMain"] [data-testid="stExpander"],
    [data-testid="stMain"] [data-testid="stForm"],
    [data-testid="stMain"] [data-testid="stDataFrame"],
    [data-testid="stMain"] [data-testid="stTable"] {
        color: var(--body);
        background: var(--surface) !important;
        border-color: #d9e2ec !important;
        border-radius: 10px;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary,
    [data-testid="stMain"] [data-testid="stExpander"] summary p {
        color: var(--ink) !important;
    }
    [data-testid="stMain"] [data-testid="stDataFrame"]
    button[data-testid="stBaseButton-elementToolbar"] {
        color: var(--ink) !important;
        background: #ffffff !important;
    }
    [data-testid="stMain"] [data-testid="stDataFrame"]
    button[data-testid="stBaseButton-elementToolbar"]:hover {
        color: var(--ink) !important;
        background: #edf2f7 !important;
    }
    [data-testid="stMain"] [data-testid="stCode"] pre,
    [data-testid="stMain"] [data-testid="stCode"] code {
        color: #24364b !important;
        background: #edf2f7 !important;
    }
    [data-testid="stMain"] [data-testid="stAlert"] {
        border-radius: 10px;
    }
    [data-testid="stMain"] [data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #e1e8ef;
        border-radius: 10px;
        padding: .35rem;
    }
    .caption-muted { color: var(--muted); font-size: .88rem; }

    @media (max-width: 1200px) {
        [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .75rem;
        }
        [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
        > [data-testid="stColumn"] {
            width: auto !important;
            min-width: 0 !important;
            flex: none !important;
        }
        [data-testid="stMetric"] { min-width: 0; }
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            font-size: .8rem;
            line-height: 1.3;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: clamp(1.15rem, 3vw, 1.65rem);
            line-height: 1.2;
            overflow-wrap: anywhere;
        }
    }
    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] { padding: 1rem .85rem 2rem; }
        .hero { padding: 1rem; }
        .hero h1 { font-size: 1.5rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = Path("data")
NOTES_PATH = DATA_DIR / "insight_notes.csv"
NAVIGATION = [
    "Overview",
    "Dataset & Cleaning",
    "Question Generator",
    "Data Story",
    "Verification",
    "Insight Notes",
    "Prompt Library",
    "About & Sources",
]
CHART_COLOR_SEQUENCE = ["#087F8C", "#2563EB", "#D97706", "#059669", "#7C3AED"]


@st.cache_data(show_spinner=False)
def _load_default() -> tuple[pd.DataFrame, str]:
    return load_dataset(DEFAULT_DATA_PATH)


@st.cache_data(show_spinner=False)
def _clean_cached(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    return clean_dataset(raw)


def _render_header() -> None:
    st.markdown(
        '<div class="hero"><h1>🌍 AI Data Storytelling Dashboard</h1>'
        "<p>From public CO₂ data to questions, visual evidence, and verified findings.</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def _source_data() -> tuple[pd.DataFrame, str]:
    uploaded = st.session_state.get("uploaded_data")
    if uploaded is not None:
        return uploaded, st.session_state.get("uploaded_name", "Uploaded CSV")
    return _load_default()


def _metrics(frame: pd.DataFrame) -> tuple[str, str, pd.DataFrame, list[int]]:
    metric = select_emissions_metric(frame)
    entities = get_entity_rows(frame)
    years = sorted(pd.to_numeric(entities["year"], errors="coerce").dropna().astype(int).unique())
    if not years:
        raise ValueError("No valid country-level years are available.")
    return metric, "country", entities, years


def _source_note(source: str) -> None:
    if source.startswith(("https://", "http://")):
        st.caption(
            f"Dataset source: {source}. The Grapher endpoint is attempted first; "
            "if unavailable, the official OWID repository is used."
        )
    else:
        st.caption(f"Active dataset: {source}")


def _overview(frame: pd.DataFrame, cleaned: pd.DataFrame, metric: str, years: list[int]) -> None:
    _render_header()
    st.subheader("Explore emissions over time")
    left, right = st.columns([1.2, 1])
    start, end = left.slider(
        "Year range",
        min_value=years[0],
        max_value=years[-1],
        value=(years[max(0, len(years) - 30)], years[-1]),
        key="overview_year_range",
    )
    entities = get_entity_rows(cleaned)
    entity_column = "country" if "country" in entities.columns else "entity"
    countries = sorted(entities[entity_column].dropna().astype(str).unique())
    selected = right.multiselect(
        "Countries (empty = all country rows)",
        options=countries,
        default=[],
        help=(
            "OWID aggregate rows are excluded. When ISO codes are present, "
            "rows without a code are excluded as well."
        ),
        key="overview_countries",
    )
    years_in_range = entities.loc[
        entities["year"].between(start, end), "year"
    ].dropna()
    latest = int(years_in_range.max())
    chart_data = (
        aggregate_by_year(cleaned, metric, selected)
        if selected
        else total_by_year(cleaned, metric)
    )
    chart_data = chart_data.loc[chart_data["year"].between(start, end)]
    latest_total = chart_data.loc[chart_data["year"].eq(latest), "value"]
    current_total = float(latest_total.iloc[0]) if not latest_total.empty else 0.0
    latest_ranking = country_ranking(cleaned, metric, latest, limit=1)
    if selected:
        selected_ranking = entities.loc[
            entities["year"].eq(latest) & entities[entity_column].isin(selected),
            [entity_column, metric],
        ].dropna(subset=[metric])
        selected_ranking = (
            selected_ranking.groupby(entity_column, as_index=False)[metric]
            .sum(min_count=1)
            .sort_values(metric, ascending=False, kind="stable")
        )
        top_country = (
            str(selected_ranking.iloc[0][entity_column])
            if not selected_ranking.empty
            else "Unavailable"
        )
    else:
        top_country = (
            str(latest_ranking.iloc[0]["country"])
            if not latest_ranking.empty
            else "Unavailable"
        )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Reported total · {latest}", f"{current_total:,.2f}")
    m2.metric("Latest available year", f"{years[-1]}")
    m3.metric("Top contributor · latest year", top_country)
    m4.metric("Country rows analyzed", f"{entities['country' if 'country' in entities else 'entity'].nunique():,}")
    unit = metric_unit(metric)
    trend_scope = (
        "selected-country sum"
        if selected
        else "reported World series when available; otherwise country-row sum"
    )
    st.caption(
        f"Measure: `{metric}` ({unit}). Total KPI and trend use the {trend_scope}; "
        "the top contributor is ranked from country rows. Missing values are omitted."
    )
    if chart_data.empty:
        st.warning("There are no valid observations for the selected filters.")
    else:
        st.plotly_chart(
            px.line(
                chart_data,
                x="year",
                y="value",
                markers=True,
                title=(
                    f"Selected-country {metric} emissions"
                    if selected
                    else f"Reported World {metric} emissions"
                ),
                labels={"year": "Year", "value": f"{metric} ({unit})"},
                template="plotly_white",
                color_discrete_sequence=CHART_COLOR_SEQUENCE,
            ),
            width="stretch",
        )

    rank = country_ranking(cleaned, metric, latest, limit=10)
    if not rank.empty:
        st.plotly_chart(
            px.bar(
                rank.sort_values("value"),
                x="value",
                y="country",
                orientation="h",
                title=f"Top reported contributors in {latest}",
                labels={"value": f"{metric} ({unit})", "country": ""},
                template="plotly_white",
                color="value",
                color_continuous_scale=["#8bd3d7", "#087f8c"],
            ),
            width="stretch",
        )
    with st.expander("Compare selected countries"):
        compare = selected or countries[:5]
        if compare:
            compare_rows = entities.loc[
                entities[entity_column].isin(compare)
                & entities["year"].between(start, end),
                [entity_column, "year", metric],
            ].dropna(subset=[metric])
            comparison = (
                compare_rows.groupby([entity_column, "year"], as_index=False)[metric]
                .sum(min_count=1)
                .rename(columns={entity_column: "country", metric: "value"})
            )
            st.plotly_chart(
                px.line(
                    comparison,
                    x="year",
                    y="value",
                    color="country",
                    title="Country comparison",
                    labels={"value": f"{metric} ({unit})"},
                    template="plotly_white",
                    color_discrete_sequence=CHART_COLOR_SEQUENCE,
                ),
                width="stretch",
            )


def _dataset_page(raw: pd.DataFrame, cleaned: pd.DataFrame, report: dict, source: str) -> None:
    _render_header()
    st.header("Dataset & Cleaning")
    _source_note(source)
    st.markdown("Upload another CSV to explore it. The default source file is preserved.")
    upload = st.file_uploader("Upload CSV", type=["csv"], key="dataset_upload")
    if upload is not None:
        try:
            uploaded = pd.read_csv(upload, low_memory=False)
            st.session_state["uploaded_data"] = uploaded
            st.session_state["uploaded_name"] = upload.name
            st.success(f"Loaded {upload.name}. Switch pages to analyze the uploaded file.")
            st.rerun()
        except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
            st.error(f"Could not read the uploaded CSV: {exc}")
    st.subheader("Source data preview")
    st.dataframe(raw.head(20), width="stretch", hide_index=True)
    st.subheader("Data quality profile")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows · source → cleaned", f"{report['before_shape'][0]:,} → {report['after_shape'][0]:,}")
    col2.metric("Columns · source → cleaned", f"{report['before_shape'][1]:,} → {report['after_shape'][1]:,}")
    col3.metric("Missing cells · before → after", f"{report['missing_before']:,} → {report['missing_after']:,}")
    col4.metric("Exact duplicates · before → after", f"{report['duplicates_before']:,} → {report['duplicates_after']:,}")
    st.markdown("**Cleaning operations**")
    for operation in report["operations"]:
        st.markdown(f"- {operation}")
    st.info(
        "Missing measurement values are intentionally retained. Filling every gap "
        "with zero would invent observations and bias totals."
    )
    type_table = pd.DataFrame(
        {"column": cleaned.columns, "dtype": cleaned.dtypes.astype(str).values}
    )
    st.subheader("Column types")
    st.dataframe(type_table, width="stretch", hide_index=True)
    st.subheader("Cleaned data preview")
    st.dataframe(cleaned.head(20), width="stretch", hide_index=True)
    csv = cleaned.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download cleaned CSV",
        csv,
        file_name="cleaned_dataset.csv",
        mime="text/csv",
        width="stretch",
    )
    if st.session_state.get("uploaded_data") is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(CLEANED_DATA_PATH, index=False)


def _question_page(frame: pd.DataFrame, metric: str) -> None:
    _render_header()
    st.header("Question Generator")
    if gemini_available():
        st.success("Gemini API key detected. Rule-based questions are always available.")
    else:
        st.info("Rule-based questions use dataset columns and observed year coverage. No AI API key is configured.")
    questions = generate_questions(frame, metric)
    selected_questions: list[str] = []
    for category, items in questions.items():
        st.subheader(category)
        for index, question in enumerate(items):
            if st.checkbox(question, value=True, key=f"question_{category}_{index}"):
                selected_questions.append(f"- [{category}] {question}")
    all_questions = "\n".join(
        selected_questions
    )
    st.markdown("**Copyable analysis prompt**")
    st.code(
        f"Analyze the Our World in Data dataset using metric `{metric}`.\n"
        "Answer only questions supported by the supplied observations. Cite exact "
        "years, units, and aggregation methods. Do not infer causation.\n\n"
        f"{all_questions or 'No questions selected.'}",
        language="text",
    )
    if gemini_available() and st.button("Generate AI question suggestions with Gemini"):
        entities = get_entity_rows(frame)
        summary = {
            "rows": int(len(frame)),
            "year_min": int(frame["year"].min()),
            "year_max": int(frame["year"].max()),
            "distinct_entities": int(entities["country" if "country" in entities else "entity"].nunique()),
            "metric": metric,
        }
        try:
            result = generate_gemini_text(question_prompt(list(frame.columns), summary))
            st.markdown("**Gemini-generated suggestions**")
            st.write(result)
            st.caption("AI-generated output; validate each question against the data before use.")
        except Exception as exc:
            st.error(f"Gemini request failed: {exc}")


def _story_page(frame: pd.DataFrame, metric: str, years: list[int]) -> None:
    _render_header()
    st.header("Data Story")
    year = st.select_slider("Story year", options=years, value=years[-1])
    story = build_story(frame, metric, int(year))
    st.markdown("### Introduction")
    st.write(story["introduction"])
    st.markdown("### Key findings")
    for finding in story["findings"]:
        st.markdown(f"- {finding}")
    st.markdown("### Visual evidence")
    ranking = country_ranking(frame, metric, int(year), limit=10)
    if not ranking.empty:
        st.plotly_chart(
            px.bar(
                ranking.sort_values("value"),
                x="value",
                y="country",
                orientation="h",
                title=f"Reported country-level {metric}, {year}",
                labels={"value": f"{metric} ({metric_unit(metric)})", "country": ""},
                template="plotly_white",
                color="value",
                color_continuous_scale=["#8bd3d7", "#087f8c"],
            ),
            width="stretch",
        )
    st.markdown("### Conclusion")
    st.write(story["conclusion"])
    st.caption("Story text above is generated from deterministic local calculations.")
    if gemini_available() and st.button("Ask Gemini for a plain-language explanation"):
        prompt = (
            "Explain these verified statistics in plain language. Do not introduce "
            "causal explanations, unsupported facts, or new numbers. Distinguish "
            "observations from possible hypotheses and note limitations.\n\n"
            f"{story}"
        )
        try:
            generated = generate_gemini_text(prompt)
            st.markdown("### Gemini-generated explanation")
            st.write(generated)
            st.warning("AI-generated explanation—not independently verified. Check it against the figures above.")
        except Exception as exc:
            st.error(f"Gemini request failed: {exc}")
    else:
        st.caption("Gemini explanation is optional and requires GOOGLE_API_KEY or GEMINI_API_KEY.")
    if st.button("Save key findings to Insight Notes"):
        try:
            save_note(
                NOTES_PATH,
                f"{metric} findings for {year}",
                "\n".join(story["findings"]),
                source="Verified local calculations",
            )
            st.success("Findings saved locally.")
        except (OSError, ValueError) as exc:
            st.error(f"Could not save this finding: {exc}")


def _verification_page(frame: pd.DataFrame, metric: str, years: list[int]) -> None:
    _render_header()
    st.header("Number Verification")
    year = int(st.select_slider("Verification year", options=years, value=years[-1]))
    chart_data = total_by_year(frame, metric)
    result = verify_analysis(frame, metric, year, chart_data)
    if result["all_passed"]:
        st.success("All independent verification checks passed.")
    else:
        st.error("One or more verification checks failed. Do not present affected values.")
    for label, passed in result["checks"].items():
        st.write(f"{'✅' if passed else '❌'} {label}")
    st.markdown("**Calculation methodology**")
    st.write(result["methodology"])
    comparison = result["aggregate_comparison"]
    if comparison and not comparison["matches"]:
        st.warning(
            f"Reported World total ({comparison['world_total']:,.3f} "
            f"{metric_unit(metric)}) differs from the sum of coded country rows "
            f"({comparison['country_total']:,.3f} {metric_unit(metric)}) "
            f"by {comparison['difference']:+,.3f} {metric_unit(metric)}. "
            "This is a source-aggregation discrepancy, not a failed arithmetic check."
        )
    st.write(
        f"Direct recomputed total: **{result['direct_total']:,.6f}** "
        f"{metric_unit(metric)} in {year}."
    )
    st.dataframe(result["ranking"], width="stretch", hide_index=True)
    st.caption(
        "Year-over-year change follows the reported World series when available; "
        "otherwise it uses summed country-level annual totals. "
        "Values not in the source are not imputed. Ranking ties follow stable source ordering."
    )


def _notes_page() -> None:
    _render_header()
    st.header("Insight Notes")
    with st.form("add_insight_note", clear_on_submit=True):
        title = st.text_input("Title")
        note = st.text_area("Finding or custom note", height=140)
        submitted = st.form_submit_button("Save note")
    if submitted:
        try:
            save_note(NOTES_PATH, title, note)
            st.success("Note saved.")
        except (OSError, ValueError) as exc:
            st.error(f"Could not save note: {exc}")
    notes = load_notes(NOTES_PATH)
    if notes.empty:
        st.info("No notes have been saved yet.")
    else:
        for row in notes.iloc[::-1].itertuples(index=False):
            with st.container(border=True):
                st.markdown(f"**{row.title}**")
                st.write(row.note)
                st.caption(f"{row.created_at_utc} · {row.source}")
        csv_bytes = notes.to_csv(index=False).encode("utf-8")
        txt_bytes = notes_as_text(notes).encode("utf-8")
        c1, c2 = st.columns(2)
        c1.download_button("Export notes as CSV", csv_bytes, "insight_notes.csv", "text/csv")
        c2.download_button("Export notes as TXT", txt_bytes, "insight_notes.txt", "text/plain")


def _prompt_page() -> None:
    _render_header()
    st.header("AI Prompt Library")
    st.write("Select a reusable prompt and copy it using the code block's copy control.")
    for title, prompt in PROMPTS.items():
        with st.expander(title):
            st.code(prompt, language="text")


def _about_page(source: str) -> None:
    _render_header()
    st.header("About, Sources & Responsible AI")
    st.markdown(
        """
        **Project:** CAPSTONE 66 — AI Data Storytelling Dashboard  
        **Purpose:** Explore public CO₂ observations with transparent calculations,
        charts, and optional AI assistance.

        **Primary requested source:** [Our World in Data Grapher CO₂ CSV](https://ourworldindata.org/grapher/co2.csv).  
        **Official fallback source:** [Our World in Data CO₂ data repository](https://github.com/owid/co2-data),
        used only when the Grapher CSV is unavailable. The exact source URL is recorded
        beside the downloaded file in `data/source.txt`.

        The OWID repository includes country and aggregate rows. Unfiltered totals
        use the reported World series when available. Country-level calculations
        exclude `OWID_` aggregate codes and, when ISO codes are present, rows with
        missing codes (the current export uses missing codes for aggregates).
        The default `co2` measure is in million tonnes; uploaded dataset units are
        shown as supplied. No causality is inferred from correlations.

        **AI disclosure:** Rule-based questions and deterministic statistics work
        without an API key. Gemini calls are optional, user-triggered, and require
        `GOOGLE_API_KEY` or `GEMINI_API_KEY`. AI text is labeled and requires human
        verification. ChatGPT, Claude, Canva AI, and CapCut AI are not integrated by
        this application.

        **Responsible use:** Missing values are retained, not silently imputed.
        Country/year coverage and measurement scope affect comparisons. Rankings
        are not causal explanations. Cite the source and verify claims independently.
        """
    )
    st.caption(f"Current source location: {source}")


def main() -> None:
    st.sidebar.title("CAPSTONE 66")
    st.sidebar.caption("AI Data Storytelling")
    page = st.sidebar.radio("Navigate", NAVIGATION, label_visibility="collapsed")
    upload = st.sidebar.file_uploader("Upload a CSV dataset", type=["csv"], key="sidebar_upload")
    if upload is not None:
        try:
            st.session_state["uploaded_data"] = pd.read_csv(upload, low_memory=False)
            st.session_state["uploaded_name"] = upload.name
        except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
            st.sidebar.error(f"Could not read the CSV: {exc}")

    try:
        raw, source = _source_data()
        cleaned, report = _clean_cached(raw)
        metric, _, entities, years = _metrics(cleaned)
    except (RuntimeError, ValueError, OSError, pd.errors.ParserError) as exc:
        st.title("AI Data Storytelling Dashboard")
        st.error(str(exc))
        st.info(
            "Upload a CSV with a country/entity field, a year field, and a numeric "
            "CO₂ emissions column to continue. The app will not substitute fabricated data."
        )
        st.link_button(
            "Open the requested OWID Grapher CSV",
            "https://ourworldindata.org/grapher/co2.csv",
        )
        return

    if page == "Overview":
        _overview(raw, cleaned, metric, years)
    elif page == "Dataset & Cleaning":
        _dataset_page(raw, cleaned, report, source)
    elif page == "Question Generator":
        _question_page(cleaned, metric)
    elif page == "Data Story":
        _story_page(cleaned, metric, years)
    elif page == "Verification":
        _verification_page(cleaned, metric, years)
    elif page == "Insight Notes":
        _notes_page()
    elif page == "Prompt Library":
        _prompt_page()
    else:
        _about_page(source)

    with st.sidebar.expander("Current data profile"):
        st.write(f"Source: {source}")
        st.write(f"Cleaned rows: {len(cleaned):,}")
        st.write(f"Measure: {metric}")
        st.write(f"Years: {years[0]}–{years[-1]}")
    _source_note(source)


if __name__ == "__main__":
    main()
