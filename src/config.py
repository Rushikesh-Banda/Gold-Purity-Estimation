"""
config.py
---------
Central place for paths, constants and the allowed value range of every input.
Keeping these in one file means the dataset generator, the validator, the
training script and the GUI all agree with each other.
"""

from dataclasses import dataclass
from pathlib import Path

# ----------------------------------------------------------------- paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
GRAPHS_DIR = OUTPUTS_DIR / "graphs"
REPORTS_DIR = OUTPUTS_DIR / "reports"

DATASET_PATH = DATA_DIR / "gold_dataset.csv"
TEST_SAMPLES_PATH = DATA_DIR / "test_samples.csv"          # held-out rows (used by "Load Sample")
HISTORY_PATH = DATA_DIR / "prediction_history.csv"
MODEL_PATH = MODELS_DIR / "best_model.pkl"
METRICS_PATH = MODELS_DIR / "model_metrics.json"
COMPARISON_PATH = MODELS_DIR / "model_comparison.csv"

# ------------------------------------------------------------- ML settings
RANDOM_STATE = 42     # fixed seed -> reproducible results
TEST_SIZE = 0.2       # 80% training / 20% testing
CV_FOLDS = 5          # extra cross-validation check on the training data

FEATURE_COLUMNS = [
    "density",
    "copper_percent",
    "silver_percent",
    "zinc_percent",
    "nickel_percent",
    "xrf_gold_reading",
    "temperature",
    "weight",
]
TARGET_COLUMN = "purity"

# ------------------------------------------------------------ input ranges
@dataclass(frozen=True)
class FieldRule:
    """Allowed range of one numeric field."""
    label: str            # name shown to the user
    unit: str             # unit text (may be empty)
    minimum: float
    maximum: float
    must_be_positive: bool = False   # True -> value must be strictly > 0


FIELD_RULES = {
    "density":          FieldRule("Density", "g/cm3", 0.0, 20.0, must_be_positive=True),
    "copper_percent":   FieldRule("Copper %", "%", 0.0, 60.0),
    "silver_percent":   FieldRule("Silver %", "%", 0.0, 60.0),
    "zinc_percent":     FieldRule("Zinc %", "%", 0.0, 30.0),
    "nickel_percent":   FieldRule("Nickel %", "%", 0.0, 30.0),
    "xrf_gold_reading": FieldRule("XRF-like Gold Reading", "%", 0.0, 100.0),
    "temperature":      FieldRule("Temperature", "C", 0.0, 60.0),
    "weight":           FieldRule("Weight", "g", 0.0, 1000.0, must_be_positive=True),
}
PURITY_RULE = FieldRule("Reference Purity", "%", 0.0, 100.0, must_be_positive=True)

ALLOY_COLUMNS = ["copper_percent", "silver_percent", "zinc_percent", "nickel_percent"]

# ------------------------------------------------------------------ texts
DATASET_LABEL = "Synthetic/Simulated Sample Dataset for Academic Use"

DISCLAIMER = "Practical AI/ML project using the project dataset and trained regression models."

APP_TITLE = "AI-Based Gold Purity Estimation"
APP_SUBTITLE = "Software Simulation for Non-Destructive Gold Assaying"


def ensure_directories():
    """Create the folders the project writes into (safe to call many times)."""
    for folder in (DATA_DIR, MODELS_DIR, GRAPHS_DIR, REPORTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)
