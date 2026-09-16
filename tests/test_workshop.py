from __future__ import annotations

import sys
import unittest
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from generate_booking_log import (  # noqa: E402
    ACTIVITY,
    ANOMALY_TYPES,
    CASE_ID,
    TIMESTAMP,
    generate_event_log,
)


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events, cls.answers = generate_event_log(seed=42)

    def test_dataset_shape_and_schema(self):
        self.assertEqual(self.events[CASE_ID].nunique(), 160)
        self.assertEqual(self.answers[CASE_ID].nunique(), 15)
        self.assertTrue({CASE_ID, ACTIVITY, TIMESTAMP}.issubset(self.events.columns))
        self.assertFalse(any("anomaly" in column.lower() for column in self.events.columns))
        self.assertEqual(set(self.events["booking_period"]), {"baseline", "monitoring"})

    def test_each_anomaly_category_has_three_cases(self):
        counts = self.answers["planted_anomaly"].value_counts().to_dict()
        self.assertEqual(counts, {kind: 3 for kind in ANOMALY_TYPES})

    def test_timestamps_are_ordered_within_cases(self):
        ordered = self.events.groupby(CASE_ID)[TIMESTAMP].apply(
            lambda values: values.is_monotonic_increasing
        )
        self.assertTrue(ordered.all())

    def test_generation_is_deterministic(self):
        second_events, second_answers = generate_event_log(seed=42)
        pd.testing.assert_frame_equal(self.events, second_events)
        pd.testing.assert_frame_equal(self.answers, second_answers)


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.learner = nbformat.read(ROOT / "process_mining_workshop.ipynb", as_version=4)
        cls.solution = nbformat.read(ROOT / "process_mining_workshop_solutions.ipynb", as_version=4)

    def test_notebooks_have_matching_structure(self):
        self.assertEqual(len(self.learner.cells), len(self.solution.cells))
        self.assertEqual(
            [cell.cell_type for cell in self.learner.cells],
            [cell.cell_type for cell in self.solution.cells],
        )

    def test_learner_code_is_syntactically_valid(self):
        for index, cell in enumerate(self.learner.cells):
            if cell.cell_type == "code":
                compile(cell.source, f"learner-cell-{index}", "exec")

    def test_every_learner_exercise_has_a_solution(self):
        learner_exercises = [
            cell for cell in self.learner.cells if "exercise" in cell.metadata.get("tags", [])
        ]
        solution_exercises = [
            cell
            for cell in self.solution.cells
            if "exercise-solution" in cell.metadata.get("tags", [])
        ]
        self.assertGreater(len(learner_exercises), 0)
        self.assertEqual(len(learner_exercises), len(solution_exercises))

    def test_solution_code_and_stored_outputs_contain_no_errors(self):
        for index, cell in enumerate(self.solution.cells):
            if cell.cell_type == "code":
                compile(cell.source, f"solution-cell-{index}", "exec")
        errors = [
            output
            for cell in self.solution.cells
            if cell.cell_type == "code"
            for output in cell.get("outputs", [])
            if output.output_type == "error"
        ]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
