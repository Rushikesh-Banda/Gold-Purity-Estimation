"""
preprocessing.py
----------------
Loading, cleaning, splitting and the preprocessing pipeline.

Data-leakage rule: the imputer and scaler live INSIDE the scikit-learn Pipeline,
so they are fitted on the training rows only. The same fitted pipeline is saved
and reused by the GUI, so prediction uses exactly the same preprocessing.
"""

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src import config
from src.validation import find_invalid_rows


def load_dataset(path=None):
    """Load the CSV dataset. Raises a clear error if the file is missing."""
    path = path or config.DATASET_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Generate it first with:  python -m src.main generate")
    return pd.read_csv(path)


def clean_dataset(df):
    """
    Clean the raw dataset. Returns (clean_df, report_dict).
      - keeps only the required columns
      - converts values to numbers (bad text becomes NaN)
      - removes duplicate rows
      - removes rows with a missing target
      - removes rows with negative / impossible values
    Missing FEATURE values are kept; the pipeline imputes them (train-median).
    """
    required = config.FEATURE_COLUMNS + [config.TARGET_COLUMN]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    report = {"rows_in": int(len(df))}
    df = df[required].apply(pd.to_numeric, errors="coerce")

    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = int(before - len(df))

    before = len(df)
    df = df.dropna(subset=[config.TARGET_COLUMN])
    report["missing_target_removed"] = int(before - len(df))

    before = len(df)
    df = df[~find_invalid_rows(df)]
    report["invalid_rows_removed"] = int(before - len(df))

    report["missing_feature_values_to_impute"] = int(df[config.FEATURE_COLUMNS].isna().sum().sum())
    report["rows_out"] = int(len(df))
    return df.reset_index(drop=True), report


def split_features_target(df):
    """Separate the input features (X) from the target purity (y)."""
    return df[config.FEATURE_COLUMNS], df[config.TARGET_COLUMN]


def split_train_test(X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE):
    """80/20 split with a fixed random_state so results can be repeated."""
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def build_pipeline(model):
    """
    Preprocessing + model in one object:
      1. SimpleImputer  - fills missing numbers with the training median
      2. StandardScaler - scales features (needed by Linear Regression)
      3. the regression model
    """
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", model),
    ])


class DataPreprocessor:
    """Thin wrapper that groups the preprocessing steps (used in the UML class diagram)."""

    def load(self, path=None):
        return load_dataset(path)

    def clean(self, df):
        return clean_dataset(df)

    def split(self, df):
        X, y = split_features_target(df)
        return split_train_test(X, y)

    def build_pipeline(self, model):
        return build_pipeline(model)
