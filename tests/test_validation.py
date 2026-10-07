"""Tests for input validation and dataset validation."""

import unittest

import numpy as np
import pandas as pd

from src import config
from src.dataset_generator import generate_dataset
from src.validation import (InputValidationError, Validator, find_invalid_rows,
                            summarize_dataset_quality, validate_sample)
from tests.helpers import VALID_INPUT


class TestInputValidation(unittest.TestCase):
    def errors_for(self, **changes):
        data = dict(VALID_INPUT, **changes)
        with self.assertRaises(InputValidationError) as ctx:
            validate_sample(data)
        return ctx.exception.errors

    def test_valid_input_returns_gold_sample(self):
        sample = validate_sample(VALID_INPUT)
        self.assertAlmostEqual(sample.density, 19.10)
        self.assertEqual(list(sample.to_frame().columns), config.FEATURE_COLUMNS)

    def test_empty_field(self):
        self.assertTrue(any("required" in e for e in self.errors_for(density="")))

    def test_missing_field(self):
        data = dict(VALID_INPUT)
        del data["weight"]
        with self.assertRaises(InputValidationError):
            validate_sample(data)

    def test_non_numeric(self):
        errors = self.errors_for(copper_percent="abc")
        self.assertIn("Please enter a valid numeric value for Copper %.", errors)

    def test_nan_and_inf_rejected(self):
        self.assertTrue(self.errors_for(density="nan"))
        self.assertTrue(self.errors_for(weight="inf"))

    def test_negative_value(self):
        self.assertIn("Silver % cannot be negative.", self.errors_for(silver_percent="-1"))

    def test_density_must_be_positive(self):
        self.assertIn("Density must be greater than 0.", self.errors_for(density="0"))

    def test_unreasonable_range(self):
        self.assertTrue(any("must not be more than" in e for e in self.errors_for(density="50")))
        self.assertTrue(any("must not be more than" in e for e in self.errors_for(xrf_gold_reading="150")))

    def test_alloy_total_over_100(self):
        errors = self.errors_for(copper_percent="60", silver_percent="60", zinc_percent="0")
        self.assertTrue(any("cannot exceed 100" in e for e in errors))

    def test_all_errors_reported_together(self):
        errors = self.errors_for(density="", zinc_percent="x", weight="-5")
        self.assertEqual(len(errors), 3)

    def test_reference_purity(self):
        v = Validator()
        self.assertIsNone(v.validate_reference(""))
        self.assertIsNone(v.validate_reference(None))
        self.assertAlmostEqual(v.validate_reference("96.5"), 96.5)
        for bad in ("abc", "-4", "0", "150"):
            with self.assertRaises(InputValidationError):
                v.validate_reference(bad)


class TestDatasetValidation(unittest.TestCase):
    def test_generated_data_is_valid(self):
        df = generate_dataset(300)
        self.assertEqual(int(find_invalid_rows(df).sum()), 0)
        report = summarize_dataset_quality(df)
        self.assertEqual(report["duplicate_rows"], 0)
        self.assertEqual(report["missing_values"], {})

    def test_detects_bad_rows(self):
        df = generate_dataset(50)
        df.loc[0, "density"] = -3            # negative
        df.loc[1, "xrf_gold_reading"] = 500  # unrealistic
        df.loc[2, "purity"] = 0              # impossible purity
        df.loc[3, "density"] = np.nan        # missing (not "invalid", handled by imputer)
        invalid = find_invalid_rows(df)
        self.assertEqual(list(invalid[:4]), [True, True, True, False])
        self.assertEqual(summarize_dataset_quality(df)["missing_values"], {"density": 1})


if __name__ == "__main__":
    unittest.main()
