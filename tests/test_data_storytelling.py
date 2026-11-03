from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_storytelling.analysis import (
    aggregate_by_year,
    annual_change_extremes,
    build_story,
    calculate_kpis,
    country_ranking,
    generate_questions,
    total_by_year,
    verify_analysis,
)
from data_storytelling.data import clean_dataset, load_dataset, select_emissions_metric, validate_dataset
from data_storytelling.notes import export_notes, load_notes, notes_as_text, save_note


class DataCleaningTests(unittest.TestCase):
    def test_removes_duplicate_and_invalid_keys_but_preserves_missing_measurements(self) -> None:
        raw = pd.DataFrame(
            {
                "country": ["A", "A", "", "B"],
                "year": [2000, 2000, 2001, None],
                "co2": [1.0, 1.0, 2.0, None],
            }
        )
        cleaned, report = clean_dataset(raw)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["country"], "A")
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(report["invalid_keys_removed"], 2)

    def test_selects_observed_emissions_measure(self) -> None:
        frame = pd.DataFrame({"year": [2000], "co2": [1.0]})
        self.assertEqual(select_emissions_metric(frame), "co2")

    def test_normalizes_case_variants_of_entity_year_and_iso_headers(self) -> None:
        raw = pd.DataFrame(
            {"Country": ["A"], "Year": [2000], "ISO_CODE": ["AAA"], "CO2": [1.0]}
        )
        cleaned, _ = clean_dataset(raw)
        self.assertTrue({"country", "year", "iso_code", "CO2"} <= set(cleaned.columns))
        self.assertEqual(select_emissions_metric(cleaned), "CO2")

    def test_loads_a_local_csv_without_downloading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.csv"
            pd.DataFrame({"country": ["A"], "year": [2000], "co2": [1.0]}).to_csv(
                path, index=False
            )
            frame, source = load_dataset(path)
            self.assertEqual(len(frame), 1)
            self.assertEqual(source, str(path))

    def test_rejects_missing_required_columns(self) -> None:
        with self.assertRaises(ValueError):
            validate_dataset(pd.DataFrame({"year": [2000], "co2": [1.0]}))


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "country": ["A", "B", "A", "B", "A", "B"],
                "iso_code": ["AAA", "BBB", "AAA", "BBB", "AAA", "BBB"],
                "year": [2000, 2000, 2001, 2001, 2002, 2002],
                "co2": [2.0, 3.0, 4.0, 2.0, 5.0, 1.0],
                "population": [10, 20, 10, 20, 10, 20],
            }
        )

    def test_kpis_ranking_and_year_over_year_change(self) -> None:
        kpis = calculate_kpis(self.frame, "co2", 2001)
        self.assertEqual(kpis["total"], 6.0)
        self.assertEqual(kpis["change"], 1.0)
        self.assertEqual(kpis["top_country"], "A")
        self.assertEqual(country_ranking(self.frame, "co2", 2001).iloc[0]["country"], "A")

    def test_chart_data_and_verification_agree(self) -> None:
        chart = aggregate_by_year(self.frame, "co2")
        self.assertEqual(chart["value"].tolist(), [5.0, 6.0, 6.0])
        result = verify_analysis(self.frame, "co2", 2001, chart)
        self.assertTrue(result["all_passed"], result["checks"])

    def test_largest_adjacent_year_increase_and_decrease(self) -> None:
        extremes = annual_change_extremes(self.frame, "co2")
        self.assertEqual(extremes["increase"]["year"], 2001)
        self.assertEqual(extremes["increase"]["change"], 1.0)
        self.assertIsNone(extremes["decrease"])

    def test_rule_based_question_categories_are_populated(self) -> None:
        questions = generate_questions(self.frame, "co2")
        self.assertGreaterEqual(sum(map(len, questions.values())), 10)
        self.assertTrue({"Trends", "Comparisons", "Distributions", "Relationships"} <= questions.keys())

    def test_story_contains_method_and_observations(self) -> None:
        story = build_story(self.frame, "co2", 2002)
        self.assertIn("2000–2002", story["introduction"])
        self.assertGreaterEqual(len(story["findings"]), 3)
        self.assertIn("causation", story["conclusion"])

    def test_aggregate_rows_are_not_mixed_into_country_total(self) -> None:
        frame = pd.concat(
            [
                self.frame,
                pd.DataFrame(
                    {
                        "country": ["World", "Regional group"],
                        "iso_code": [None, "OWID_REG"],
                        "year": [2002, 2002],
                        "co2": [999.0, 1000.0],
                        "population": [30, 40],
                    }
                ),
            ],
            ignore_index=True,
        )
        country_total = aggregate_by_year(frame, "co2")
        self.assertEqual(
            country_total.loc[country_total["year"].eq(2002), "value"].iloc[0], 6.0
        )
        self.assertEqual(
            country_ranking(frame, "co2", 2002).iloc[0]["country"], "A"
        )

    def test_world_series_drives_unfiltered_total_but_not_country_ranking(self) -> None:
        frame = pd.concat(
            [
                self.frame,
                pd.DataFrame(
                    {
                        "country": ["World", "World", "World"],
                        "iso_code": [None, None, None],
                        "year": [2000, 2001, 2002],
                        "co2": [100.0, 120.0, 115.0],
                        "population": [30, 30, 30],
                    }
                ),
            ],
            ignore_index=True,
        )
        self.assertEqual(total_by_year(frame, "co2")["value"].tolist(), [100, 120, 115])
        self.assertEqual(calculate_kpis(frame, "co2", 2001)["total"], 120.0)
        self.assertEqual(calculate_kpis(frame, "co2", 2001)["top_country"], "A")
        result = verify_analysis(frame, "co2", 2001, total_by_year(frame, "co2"))
        self.assertTrue(result["all_passed"], result["checks"])
        self.assertEqual(result["aggregate_comparison"]["difference"], 114.0)


class NoteTests(unittest.TestCase):
    def test_save_and_export_notes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.csv"
            saved = save_note(path, "Finding", "A verified observation.")
            self.assertEqual(len(saved), 1)
            self.assertEqual(len(load_notes(path)), 1)
            csv_path = export_notes(saved, Path(directory) / "export.csv", "csv")
            txt_path = export_notes(saved, Path(directory) / "export.txt", "txt")
            self.assertTrue(csv_path.exists())
            self.assertIn("A verified observation.", txt_path.read_text(encoding="utf-8"))
            self.assertIn("A verified observation.", notes_as_text(saved))


if __name__ == "__main__":
    unittest.main()
