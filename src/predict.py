"""
predict.py
----------
Prediction system. It only LOADS the saved model - it never retrains.

Classes (they match the UML entities):
  FireAssayReference - the reference purity value (from the dataset or typed by the user)
  MLModel            - the saved preprocessing + regression pipeline
  Prediction         - the result of one prediction
  PredictionHistory  - CSV store for saved predictions

NOTE: "fire assay reference" here only means the reference purity value that
belongs to a sample. This software does NOT perform a fire assay.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import joblib
import pandas as pd

from src import config
from src.validation import Validator, GoldSample


class ModelNotFoundError(FileNotFoundError):
    """Raised when models/best_model.pkl does not exist yet."""


@dataclass
class FireAssayReference:
    """Reference purity (%) used only for comparison with the prediction."""
    purity: float


class MLModel:
    """Wrapper around the saved pipeline (imputer + scaler + best regressor)."""

    def __init__(self, pipeline, model_name, feature_columns, training_ranges=None):
        self.pipeline = pipeline
        self.model_name = model_name
        self.feature_columns = feature_columns
        self.training_ranges = training_ranges or {}

    @classmethod
    def load(cls, path=None):
        """Load the model saved by train_model.py."""
        path = path or config.MODEL_PATH
        if not path.exists():
            raise ModelNotFoundError(
                f"Trained model not found: {path}\n"
                "Train it first with:  python -m src.main train")
        bundle = joblib.load(path)
        return cls(bundle["pipeline"], bundle["model_name"],
                   bundle["feature_columns"], bundle.get("training_ranges"))

    def predict(self, sample: GoldSample):
        """Predict purity (%) for one validated sample. Result is limited to 0-100 %."""
        frame = sample.to_frame()[self.feature_columns]   # same column order as training
        value = float(self.pipeline.predict(frame)[0])
        return min(max(value, 0.0), 100.0)

    def unusual_inputs(self, sample: GoldSample):
        """Warnings for inputs outside the range the model saw during training."""
        notes = []
        for name, (low, high) in self.training_ranges.items():
            value = sample.to_dict()[name]
            if value < low or value > high:
                label = config.FIELD_RULES[name].label
                notes.append(f"{label} = {value:g} is outside the training range "
                             f"({low:.2f} to {high:.2f}); the estimate may be unreliable.")
        return notes


@dataclass
class Prediction:
    """Result of one prediction."""
    sample: GoldSample
    predicted_purity: float
    model_name: str
    reference: Optional[FireAssayReference] = None
    warnings: list = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def reference_purity(self):
        return self.reference.purity if self.reference else None

    @property
    def difference(self):
        """Absolute difference between predicted and reference purity (or None)."""
        if self.reference is None:
            return None
        return abs(self.predicted_purity - self.reference.purity)


def run_prediction(raw_inputs, reference_raw=None, model=None):
    """
    Full prediction flow used by the GUI:
      raw text -> Validator -> MLModel (same preprocessing as training) -> Prediction
    Raises InputValidationError for bad input and ModelNotFoundError if no model is saved.
    """
    validator = Validator()
    sample = validator.validate_sample(raw_inputs)
    reference_value = validator.validate_reference(reference_raw)
    model = model or MLModel.load()

    predicted = model.predict(sample)
    reference = FireAssayReference(reference_value) if reference_value is not None else None
    return Prediction(sample=sample, predicted_purity=predicted, model_name=model.model_name,
                      reference=reference, warnings=model.unusual_inputs(sample))


# ------------------------------------------------------------------ history
HISTORY_COLUMNS = ["Date/Time", "Density", "Copper %", "Silver %", "Zinc %", "Nickel %",
                   "XRF Reading", "Temperature", "Weight", "Predicted Purity",
                   "Reference Purity", "Difference", "Model Used"]


class PredictionHistory:
    """Saves and reads predictions in data/prediction_history.csv."""

    def __init__(self, path=None):
        self.path = path or config.HISTORY_PATH

    def save(self, prediction: Prediction):
        s = prediction.sample
        row = {
            "Date/Time": prediction.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Density": s.density, "Copper %": s.copper_percent, "Silver %": s.silver_percent,
            "Zinc %": s.zinc_percent, "Nickel %": s.nickel_percent,
            "XRF Reading": s.xrf_gold_reading, "Temperature": s.temperature, "Weight": s.weight,
            "Predicted Purity": round(prediction.predicted_purity, 2),
            "Reference Purity": "" if prediction.reference_purity is None else round(prediction.reference_purity, 2),
            "Difference": "" if prediction.difference is None else round(prediction.difference, 2),
            "Model Used": prediction.model_name,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists() or self.path.stat().st_size == 0
        pd.DataFrame([row], columns=HISTORY_COLUMNS).to_csv(
            self.path, mode="a", header=write_header, index=False)

    def load(self):
        """Return the history as a DataFrame (empty if the file does not exist yet)."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return pd.DataFrame(columns=HISTORY_COLUMNS)
        return pd.read_csv(self.path)


def get_random_test_sample(path=None, rng=None):
    """
    Pick a random held-out row (saved by the training script) so the user can try
    the model with a sample that has a reference purity. Returns (inputs, reference).
    """
    path = path or config.TEST_SAMPLES_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Sample file not found: {path}\n"
            "Train the model first with:  python -m src.main train")
    rows = pd.read_csv(path)
    if rows.empty:
        raise ValueError("The sample file contains no rows.")
    index = (rng or random).randrange(len(rows))
    row = rows.iloc[index]
    inputs = {name: float(row[name]) for name in config.FEATURE_COLUMNS}
    return inputs, float(row[config.TARGET_COLUMN])
