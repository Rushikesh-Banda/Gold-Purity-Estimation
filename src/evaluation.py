"""
evaluation.py
-------------
Reusable regression metrics, model comparison table and best-model selection.
NOTE: R2 is a goodness-of-fit score, NOT "accuracy".
"""

import json

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src import config


def calculate_mae(y_true, y_pred):
    """Mean Absolute Error (in purity % points)."""
    return float(mean_absolute_error(y_true, y_pred))


def calculate_mse(y_true, y_pred):
    """Mean Squared Error."""
    return float(mean_squared_error(y_true, y_pred))


def calculate_rmse(y_true, y_pred):
    """Root Mean Squared Error (in purity % points)."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def calculate_r2(y_true, y_pred):
    """R-squared score (1.0 = perfect fit; 0.0 = no better than predicting the mean)."""
    return float(r2_score(y_true, y_pred))


def evaluate_predictions(y_true, y_pred):
    """All four metrics as a dict."""
    return {
        "mae": calculate_mae(y_true, y_pred),
        "mse": calculate_mse(y_true, y_pred),
        "rmse": calculate_rmse(y_true, y_pred),
        "r2": calculate_r2(y_true, y_pred),
    }


def select_best_model(results):
    """
    Choose the model with the lowest test RMSE (ties broken by higher R2).
    `results` is {model_name: {"rmse": ..., "r2": ..., ...}}.
    """
    return min(results, key=lambda name: (results[name]["rmse"], -results[name]["r2"]))


def build_comparison_table(results):
    """DataFrame with columns Model | MAE | MSE | RMSE | R2."""
    rows = [{"Model": name, "MAE": m["mae"], "MSE": m["mse"], "RMSE": m["rmse"], "R2": m["r2"]}
            for name, m in results.items()]
    return pd.DataFrame(rows)


def save_comparison_table(table, path=None):
    path = path or config.COMPARISON_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False)
    return path


def save_metrics(metrics, path=None):
    path = path or config.METRICS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return path


def load_metrics(path=None):
    """Load model_metrics.json. Raises FileNotFoundError with a helpful message."""
    path = path or config.METRICS_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Metrics file not found: {path}\n"
            "Train the model first with:  python -m src.main train")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
