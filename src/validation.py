"""
validation.py
-------------
Two kinds of validation live here:

1. INPUT validation  - checks what the user types in the GUI (class Validator).
2. DATASET validation - checks the rows of the CSV before training.

Invalid input never reaches the ML model.
"""

import math
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from src import config


class InputValidationError(Exception):
    """Raised when user input is invalid. `errors` holds one message per problem."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


@dataclass
class GoldSample:
    """One validated gold sample (the 8 input features)."""
    density: float
    copper_percent: float
    silver_percent: float
    zinc_percent: float
    nickel_percent: float
    xrf_gold_reading: float
    temperature: float
    weight: float

    def to_dict(self):
        return asdict(self)

    def to_frame(self):
        """One-row DataFrame with the columns in the same order used for training."""
        return pd.DataFrame([self.to_dict()], columns=config.FEATURE_COLUMNS)


class Validator:
    """Checks raw user input and turns it into a GoldSample."""

    @staticmethod
    def parse_number(raw, rule):
        """Convert raw text/number to float. Returns (value, error_message)."""
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            return None, f"{rule.label} is required. Please enter a value."
        try:
            value = float(str(raw).strip())
        except ValueError:
            return None, f"Please enter a valid numeric value for {rule.label}."
        if not math.isfinite(value):
            return None, f"Please enter a valid numeric value for {rule.label}."
        return value, None

    @staticmethod
    def check_range(value, rule):
        """Return an error message if `value` breaks the rule, else None."""
        if rule.must_be_positive and value <= 0:
            return f"{rule.label} must be greater than 0."
        if value < 0:
            return f"{rule.label} cannot be negative."
        if value > rule.maximum:
            unit = f" {rule.unit}" if rule.unit else ""
            return f"{rule.label} must not be more than {rule.maximum:g}{unit}."
        return None

    def validate_sample(self, raw_inputs):
        """
        raw_inputs: dict {feature_name: text or number}.
        Returns a GoldSample, or raises InputValidationError with all problems.
        """
        errors, values = [], {}
        for name in config.FEATURE_COLUMNS:
            rule = config.FIELD_RULES[name]
            value, error = self.parse_number(raw_inputs.get(name), rule)
            if error is None:
                error = self.check_range(value, rule)
            if error:
                errors.append(error)
            else:
                values[name] = value

        # Cross-check: the four alloy metals cannot add up to more than 100 %.
        if not errors:
            alloy_total = sum(values[c] for c in config.ALLOY_COLUMNS)
            if alloy_total > 100:
                errors.append("Gold purity inputs must be within the allowed range: "
                              "copper + silver + zinc + nickel cannot exceed 100 %.")
        if errors:
            raise InputValidationError(errors)
        return GoldSample(**values)

    def validate_reference(self, raw):
        """Reference purity is optional. Returns a float, or None if left empty."""
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            return None
        rule = config.PURITY_RULE
        value, error = self.parse_number(raw, rule)
        if error is None:
            error = self.check_range(value, rule)
        if error:
            raise InputValidationError([error])
        return value


# Small helper functions so other modules/tests can call the validator easily.
def validate_sample(raw_inputs):
    return Validator().validate_sample(raw_inputs)


def validate_reference_purity(raw):
    return Validator().validate_reference(raw)


# ------------------------------------------------------------------------
# Dataset validation
# ------------------------------------------------------------------------
def find_invalid_rows(df):
    """
    Boolean Series: True for rows with negative, zero-where-not-allowed or
    unrealistic values. Missing values (NaN) are NOT flagged here; they are
    counted separately and imputed later inside the pipeline.
    """
    invalid = pd.Series(False, index=df.index)
    rules = dict(config.FIELD_RULES)
    rules[config.TARGET_COLUMN] = config.PURITY_RULE
    for column, rule in rules.items():
        values = df[column]
        too_low = values <= 0 if rule.must_be_positive else values < 0
        invalid |= (too_low | (values > rule.maximum)).fillna(False)

    alloy_total = df[config.ALLOY_COLUMNS].sum(axis=1, skipna=True)
    invalid |= alloy_total > 100
    return invalid


def summarize_dataset_quality(df):
    """Return a dict describing missing, duplicate and invalid values."""
    return {
        "rows": int(len(df)),
        "missing_values": {c: int(v) for c, v in df.isna().sum().items() if v > 0},
        "duplicate_rows": int(df.duplicated().sum()),
        "negative_values": int((df.select_dtypes(include=[np.number]) < 0).sum().sum()),
        "invalid_or_unrealistic_rows": int(find_invalid_rows(df).sum()),
    }
