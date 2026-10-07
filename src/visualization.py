"""
visualization.py
----------------
Matplotlib graphs. Every graph is drawn from real data / real model results.
The "Agg" backend is used so graphs are written to PNG files without a window.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src import config


def _save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path


def plot_purity_distribution(purity, path):
    """Histogram of the purity values in the dataset."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(purity, bins=30, color="#c9a227", edgecolor="black")
    ax.set_title("Purity Distribution (Synthetic/Simulated Sample Dataset)")
    ax.set_xlabel("Gold purity (%)")
    ax.set_ylabel("Number of samples")
    return _save(fig, path)


def plot_model_comparison(table, best_model, path):
    """Bar charts of MAE, RMSE and R2 for every model (best model highlighted)."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 5))
    colors = ["#2e7d32" if m == best_model else "#9e9e9e" for m in table["Model"]]
    labels = [m.replace(" ", "\n") for m in table["Model"]]
    for ax, metric, note in zip(axes, ["MAE", "RMSE", "R2"],
                                ["lower is better", "lower is better", "higher is better"]):
        bars = ax.bar(labels, table[metric], color=colors, edgecolor="black")
        ax.set_title(f"{metric} ({note})")
        ax.bar_label(bars, fmt="%.3f", fontsize=9)
    fig.suptitle(f"Model comparison on the test set (green = selected: {best_model})")
    return _save(fig, path)


def plot_actual_vs_predicted(y_true, y_pred, model_name, path):
    """Scatter plot: reference purity vs predicted purity."""
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(y_true, y_pred, alpha=0.6, color="#1565c0", edgecolor="white", linewidth=0.3)
    low, high = min(np.min(y_true), np.min(y_pred)), max(np.max(y_true), np.max(y_pred))
    ax.plot([low, high], [low, high], "r--", label="Perfect prediction")
    ax.set_title(f"Actual vs Predicted Purity - {model_name} (test set)")
    ax.set_xlabel("Reference purity (%)")
    ax.set_ylabel("Predicted purity (%)")
    ax.legend()
    return _save(fig, path)


def plot_residuals(y_true, y_pred, model_name, path):
    """Prediction error (residual) graphs for the selected model."""
    residuals = np.asarray(y_true) - np.asarray(y_pred)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(y_pred, residuals, alpha=0.6, color="#6a1b9a")
    axes[0].axhline(0, color="red", linestyle="--")
    axes[0].set_title("Residuals vs predicted purity")
    axes[0].set_xlabel("Predicted purity (%)")
    axes[0].set_ylabel("Actual - predicted (%)")
    axes[1].hist(residuals, bins=25, color="#6a1b9a", edgecolor="black")
    axes[1].set_title("Distribution of prediction errors")
    axes[1].set_xlabel("Actual - predicted (%)")
    axes[1].set_ylabel("Number of samples")
    fig.suptitle(f"Prediction errors - {model_name} (test set)")
    return _save(fig, path)


# File names of the graphs, shared by the training script and the GUI.
GRAPH_FILES = {
    "Model Comparison": "model_comparison.png",
    "Actual vs Predicted": "actual_vs_predicted.png",
    "Prediction Errors": "residuals.png",
    "Purity Distribution": "purity_distribution.png",
}
