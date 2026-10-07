"""Shared helper: builds a small dataset + trained model inside a temporary folder."""

from pathlib import Path

from src import config
from src.dataset_generator import generate_dataset
from src.train_model import train_and_evaluate


def build_test_artifacts(folder: Path, n_records=400, make_graphs=False):
    """Generate data, train, and return a dict with all created paths + metrics."""
    paths = {
        "dataset": folder / "gold_dataset.csv",
        "model": folder / "best_model.pkl",
        "metrics": folder / "model_metrics.json",
        "comparison": folder / "model_comparison.csv",
        "test_samples": folder / "test_samples.csv",
        "graphs": folder / "graphs",
    }
    generate_dataset(n_records).to_csv(paths["dataset"], index=False)
    paths["result"] = train_and_evaluate(
        dataset_path=paths["dataset"], model_path=paths["model"],
        metrics_path=paths["metrics"], comparison_path=paths["comparison"],
        test_samples_path=paths["test_samples"], graphs_dir=paths["graphs"],
        make_graphs=make_graphs, verbose=False)
    return paths


# A typical valid input (example values from the project brief)
VALID_INPUT = {
    "density": "19.10", "copper_percent": "3.50", "silver_percent": "2.10",
    "zinc_percent": "0.10", "nickel_percent": "0.50", "xrf_gold_reading": "94.20",
    "temperature": "25", "weight": "10",
}
