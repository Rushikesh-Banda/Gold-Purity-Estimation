"""Tests for dataset loading, cleaning, splitting and the preprocessing pipeline."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src import config
from src.dataset_generator import generate_dataset
from src.preprocessing import (build_pipeline, clean_dataset, load_dataset,
                               split_features_target, split_train_test)


class TestDatasetGenerator(unittest.TestCase):
    def test_default_dataset_has_at_least_1000_records(self):
        df = generate_dataset()
        self.assertGreaterEqual(len(df), 1000)
        self.assertEqual(list(df.columns), config.FEATURE_COLUMNS + [config.TARGET_COLUMN])

    def test_reproducible_with_seed(self):
        pd.testing.assert_frame_equal(generate_dataset(200, seed=1), generate_dataset(200, seed=1))

    def test_target_is_not_a_copy_of_an_input(self):
        df = generate_dataset(500)
        for column in config.FEATURE_COLUMNS:
            self.assertFalse(np.allclose(df[column], df["purity"]), column)
        self.assertGreater(df["purity"].std(), 5)      # real variation


class TestLoadAndClean(unittest.TestCase):
    def test_load_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "d.csv"
            generate_dataset(120).to_csv(path, index=False)
            self.assertEqual(len(load_dataset(path)), 120)

    def test_missing_file_gives_clear_error(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            load_dataset(Path("does_not_exist.csv"))
        self.assertIn("python -m src.main generate", str(ctx.exception))

    def test_clean_removes_duplicates_and_bad_rows(self):
        df = generate_dataset(100)
        dirty = pd.concat([df, df.iloc[[0, 1]]], ignore_index=True)   # 2 duplicates
        dirty.loc[5, "weight"] = -1                                    # negative
        dirty.loc[6, "purity"] = np.nan                                # missing target
        dirty.loc[7, "temperature"] = 999                              # unrealistic
        dirty.loc[8, "copper_percent"] = np.nan                        # missing feature (kept)
        clean, report = clean_dataset(dirty)
        self.assertEqual(report["duplicates_removed"], 2)
        self.assertEqual(report["missing_target_removed"], 1)
        self.assertEqual(report["invalid_rows_removed"], 2)
        self.assertEqual(report["missing_feature_values_to_impute"], 1)
        self.assertEqual(len(clean), 97)   # 102 rows - 2 duplicates - 1 missing target - 2 invalid

    def test_missing_column_error(self):
        with self.assertRaises(ValueError):
            clean_dataset(generate_dataset(20).drop(columns=["density"]))

    def test_text_values_become_missing(self):
        df = generate_dataset(30).astype(object)
        df.loc[0, "density"] = "abc"
        clean, report = clean_dataset(df)
        self.assertEqual(report["missing_feature_values_to_impute"], 1)


class TestSplitAndPipeline(unittest.TestCase):
    def setUp(self):
        self.df = generate_dataset(500)
        self.X, self.y = split_features_target(self.df)

    def test_split_is_80_20_and_repeatable(self):
        X_train, X_test, y_train, y_test = split_train_test(self.X, self.y)
        self.assertEqual(len(X_train), 400)
        self.assertEqual(len(X_test), 100)
        again = split_train_test(self.X, self.y)
        pd.testing.assert_frame_equal(X_train, again[0])

    def test_scaler_uses_training_data_only(self):
        """No data leakage: the fitted scaler must reflect the TRAIN rows, not all rows."""
        X_train, X_test, y_train, _ = split_train_test(self.X, self.y)
        pipeline = build_pipeline(LinearRegression()).fit(X_train, y_train)
        scaler = pipeline.named_steps["scaler"]
        np.testing.assert_allclose(scaler.mean_, X_train.mean().values)
        self.assertFalse(np.allclose(scaler.mean_, self.X.mean().values, atol=1e-9))

    def test_pipeline_imputes_missing_values(self):
        X_train, X_test, y_train, _ = split_train_test(self.X, self.y)
        pipeline = build_pipeline(LinearRegression()).fit(X_train, y_train)
        row = X_test.iloc[[0]].copy()
        row.iloc[0, 0] = np.nan
        self.assertTrue(np.isfinite(pipeline.predict(row)[0]))


if __name__ == "__main__":
    unittest.main()
