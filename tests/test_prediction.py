"""Tests for training results, model saving/loading, prediction, history and report."""

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src import config
from src.evaluation import calculate_mae, calculate_mse, calculate_r2, calculate_rmse, select_best_model
from src.predict import (HISTORY_COLUMNS, MLModel, ModelNotFoundError, PredictionHistory,
                         get_random_test_sample, run_prediction)
from src.report_generator import generate_pdf_report
from src.validation import InputValidationError
from tests.helpers import VALID_INPUT, build_test_artifacts


class TestMetricFunctions(unittest.TestCase):
    def test_known_values(self):
        y_true, y_pred = [10, 20, 30], [12, 18, 30]
        self.assertAlmostEqual(calculate_mae(y_true, y_pred), 4 / 3)
        self.assertAlmostEqual(calculate_mse(y_true, y_pred), 8 / 3)
        self.assertAlmostEqual(calculate_rmse(y_true, y_pred), (8 / 3) ** 0.5)
        self.assertAlmostEqual(calculate_r2(y_true, y_true), 1.0)

    def test_best_model_selection_uses_lowest_rmse(self):
        results = {"A": {"rmse": 2.0, "r2": 0.9}, "B": {"rmse": 1.0, "r2": 0.8}, "C": {"rmse": 3.0, "r2": 0.7}}
        self.assertEqual(select_best_model(results), "B")


class TestTrainedModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.tmp.name)
        cls.paths = build_test_artifacts(cls.folder, make_graphs=True)
        cls.model = MLModel.load(cls.paths["model"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # --- training outputs -------------------------------------------------
    def test_three_models_trained_with_real_metrics(self):
        models = self.paths["result"]["models"]
        self.assertEqual(set(models), {"Linear Regression", "Decision Tree Regressor", "Random Forest Regressor"})
        for m in models.values():
            self.assertTrue({"mae", "mse", "rmse", "r2"} <= set(m))
            self.assertGreater(m["rmse"], 0)

    def test_best_model_is_the_one_with_lowest_test_rmse(self):
        models = self.paths["result"]["models"]
        lowest = min(models, key=lambda n: models[n]["rmse"])
        self.assertEqual(self.paths["result"]["best_model"], lowest)
        self.assertEqual(self.model.model_name, lowest)

    def test_metrics_json_and_files_saved(self):
        saved = json.loads(self.paths["metrics"].read_text())
        self.assertEqual(saved["best_model"], self.paths["result"]["best_model"])
        for key in ("model", "comparison", "test_samples"):
            self.assertTrue(self.paths[key].exists(), key)
        for graph in ("model_comparison.png", "actual_vs_predicted.png",
                      "residuals.png", "purity_distribution.png"):
            self.assertTrue((self.paths["graphs"] / graph).exists(), graph)

    # --- model loading -----------------------------------------------------
    def test_missing_model_file(self):
        with self.assertRaises(ModelNotFoundError):
            MLModel.load(self.folder / "nope.pkl")

    # --- prediction ---------------------------------------------------------
    def test_valid_prediction(self):
        result = run_prediction(VALID_INPUT, model=self.model)
        self.assertTrue(0 <= result.predicted_purity <= 100)
        self.assertIsNone(result.difference)
        self.assertEqual(result.model_name, self.model.model_name)

    def test_prediction_is_not_hard_coded(self):
        high = run_prediction(VALID_INPUT, model=self.model).predicted_purity
        low_input = dict(VALID_INPUT, density="12.0", xrf_gold_reading="45", copper_percent="30",
                         silver_percent="20", zinc_percent="4", nickel_percent="1")
        low = run_prediction(low_input, model=self.model).predicted_purity
        self.assertGreater(high - low, 20)

    def test_reference_difference_is_absolute(self):
        result = run_prediction(VALID_INPUT, "90", model=self.model)
        self.assertAlmostEqual(result.difference, abs(result.predicted_purity - 90.0))
        self.assertEqual(result.reference_purity, 90.0)

    def test_invalid_input_never_reaches_model(self):
        for bad in (dict(VALID_INPUT, density="abc"), dict(VALID_INPUT, weight="-2"), dict(VALID_INPUT, zinc_percent="")):
            with self.assertRaises(InputValidationError):
                run_prediction(bad, model=self.model)
        with self.assertRaises(InputValidationError):
            run_prediction(VALID_INPUT, "not a number", model=self.model)

    def test_unusual_input_gives_warning(self):
        result = run_prediction(dict(VALID_INPUT, weight="900"), model=self.model)
        self.assertTrue(any("Weight" in w for w in result.warnings))

    def test_random_test_sample_can_be_predicted(self):
        inputs, reference = get_random_test_sample(self.paths["test_samples"])
        result = run_prediction(inputs, reference, model=self.model)
        self.assertLess(result.difference, 15)       # sanity: model is roughly right

    # --- history -------------------------------------------------------------
    def test_history_missing_file_then_save_and_load(self):
        history = PredictionHistory(self.folder / "history.csv")
        empty = history.load()
        self.assertTrue(empty.empty)
        self.assertEqual(list(empty.columns), HISTORY_COLUMNS)

        history.save(run_prediction(VALID_INPUT, "95", model=self.model))
        history.save(run_prediction(VALID_INPUT, model=self.model))       # no reference
        table = history.load()
        self.assertEqual(len(table), 2)
        self.assertEqual(list(table.columns), HISTORY_COLUMNS)
        self.assertTrue(pd.isna(table.loc[1, "Reference Purity"]))

    # --- report ---------------------------------------------------------------
    def test_pdf_report_created(self):
        prediction = run_prediction(VALID_INPUT, "95", model=self.model)
        metrics = json.loads(self.paths["metrics"].read_text())
        path = generate_pdf_report(prediction, metrics, self.folder / "reports")
        self.assertTrue(path.exists())
        self.assertEqual(path.read_bytes()[:4], b"%PDF")


if __name__ == "__main__":
    unittest.main()
