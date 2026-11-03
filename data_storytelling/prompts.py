"""Reusable, responsible prompts for common data storytelling tasks."""

PROMPTS = {
    "Dataset understanding": (
        "You are a careful data analyst. Review only the dataset schema and "
        "documented source I provide. Describe the observational unit, time range, "
        "units, missingness, and limitations. Separate facts from assumptions and "
        "ask for clarification when metadata is missing."
    ),
    "Analytical question generation": (
        "Using only these column names and data characteristics, suggest at least "
        "10 answerable questions. Group them into trends, comparisons, distributions, "
        "and relationships. Do not claim that any question has already been answered."
    ),
    "Data cleaning": (
        "Propose a conservative cleaning plan for this CSV. Preserve the source, "
        "identify exact duplicates and invalid keys, quantify missingness, and do "
        "not impute values without a justified method. List every proposed change."
    ),
    "Data visualization": (
        "Recommend a chart for the supplied question, data types, and aggregation. "
        "Name axes and units, identify any filtering, and describe accessibility "
        "considerations. Do not make up values."
    ),
    "Trend identification": (
        "Describe the calculated time-series values I provide. Quantify the period "
        "and change, distinguish observed trend from explanation, flag gaps or "
        "outliers for verification, and do not infer causation."
    ),
    "Insight writing": (
        "Turn only the verified statistics I provide into a concise plain-language "
        "finding. State the metric, units, geography, time period, and uncertainty. "
        "Do not add causes, unsupported context, or invented numbers."
    ),
    "Fact verification": (
        "Check each claim against the supplied source rows and calculation method. "
        "Recalculate totals and rankings independently, identify mismatches, and "
        "report 'not verifiable from supplied data' where appropriate."
    ),
    "Responsible AI evaluation": (
        "Evaluate this data analysis for hallucination risk, missing-data bias, "
        "aggregation choices, misleading comparisons, privacy concerns, and "
        "unsupported causal wording. Suggest human checks and source attribution."
    ),
    "Presentation creation": (
        "Create an 8–10 slide outline from the verified findings provided. Include "
        "source and method slides, concise chart captions, caveats, and a conclusion. "
        "Do not add unsupported facts."
    ),
    "Video narration": (
        "Write a 2–3 minute walkthrough script for the supplied working dashboard. "
        "Include demonstration actions, narration for verified results, clear "
        "transitions, and a reminder that correlation does not establish causation."
    ),
}
