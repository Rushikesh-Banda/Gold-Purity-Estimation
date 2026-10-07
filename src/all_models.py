"""Load all three trained regression pipelines for live sample comparison."""
from pathlib import Path
import joblib
import pandas as pd

from src import config, preprocessing
from src.train_model import get_models

ALL_MODELS_PATH = config.MODELS_DIR / "all_models.pkl"


def train_and_save_all_models(path=None):
    """Train the same three project models on the project's fixed train split and save them."""
    raw = preprocessing.load_dataset(path)
    df, _ = preprocessing.clean_dataset(raw)
    X, y = preprocessing.split_features_target(df)
    X_train, _, y_train, _ = preprocessing.split_train_test(X, y)
    fitted = {}
    for name, model in get_models().items():
        pipe = preprocessing.build_pipeline(model)
        pipe.fit(X_train, y_train)
        fitted[name] = pipe
    ALL_MODELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"models": fitted, "feature_columns": config.FEATURE_COLUMNS}, ALL_MODELS_PATH)
    return fitted


def load_all_models():
    if not ALL_MODELS_PATH.exists():
        train_and_save_all_models()
    bundle = joblib.load(ALL_MODELS_PATH)
    return bundle["models"]


def predict_all(raw_inputs):
    """Validate once and return a prediction from every trained model."""
    from src.validation import Validator
    sample = Validator().validate_sample(raw_inputs)
    frame = sample.to_frame()[config.FEATURE_COLUMNS]
    models = load_all_models()
    return {name: float(max(0.0, min(100.0, pipe.predict(frame)[0]))) for name, pipe in models.items()}
