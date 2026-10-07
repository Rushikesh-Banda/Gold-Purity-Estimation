"""
train_model.py
--------------
Trains, evaluates and compares three regression models, then saves the best one.

Workflow:  load -> validate/clean -> split 80/20 -> train 3 models -> evaluate on
the held-out test set -> pick best (lowest test RMSE) -> save pipeline + metrics
+ graphs.   Run with:  python -m src.train_model   (or  python -m src.main train)
"""

import sys
from collections import OrderedDict
from datetime import datetime

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.tree import DecisionTreeRegressor

from src import config
from src import evaluation, preprocessing, visualization


def get_models():
    """The three regression models compared in this project (fixed, simple settings)."""
    return OrderedDict([
        ("Linear Regression", LinearRegression()),
        ("Decision Tree Regressor", DecisionTreeRegressor(
            max_depth=8, min_samples_leaf=5, random_state=config.RANDOM_STATE)),
        ("Random Forest Regressor", RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2, random_state=config.RANDOM_STATE, n_jobs=-1)),
    ])


def train_and_evaluate(dataset_path=None, model_path=None, metrics_path=None,
                       comparison_path=None, test_samples_path=None,
                       graphs_dir=None, make_graphs=True, verbose=True):
    """Run the whole training workflow and return the metrics dictionary."""
    model_path = model_path or config.MODEL_PATH
    test_samples_path = test_samples_path or config.TEST_SAMPLES_PATH
    graphs_dir = graphs_dir or config.GRAPHS_DIR

    def say(text=""):
        if verbose:
            print(text)

    # 1-2. Load and validate/clean the dataset
    raw = preprocessing.load_dataset(dataset_path)
    df, clean_report = preprocessing.clean_dataset(raw)
    say(f"Dataset: {clean_report['rows_in']} rows loaded, {clean_report['rows_out']} rows after cleaning")
    say(f"Cleaning report: {clean_report}")

    # 3-4. Features/target and 80/20 split
    X, y = preprocessing.split_features_target(df)
    X_train, X_test, y_train, y_test = preprocessing.split_train_test(X, y)
    say(f"Training rows: {len(X_train)}   Test rows: {len(X_test)}")

    # 5-8. Train every model inside its own preprocessing pipeline and evaluate on the test set
    results, fitted, test_predictions = OrderedDict(), {}, {}
    cv = KFold(n_splits=config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_STATE)
    for name, model in get_models().items():
        pipeline = preprocessing.build_pipeline(model)
        # Extra check: cross-validated RMSE on the TRAINING data only (test set stays untouched)
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv,
                                    scoring="neg_root_mean_squared_error")
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        metrics = evaluation.evaluate_predictions(y_test, predictions)
        metrics["cv_rmse_mean"] = float(-cv_scores.mean())
        metrics["cv_rmse_std"] = float(cv_scores.std())
        results[name], fitted[name], test_predictions[name] = metrics, pipeline, predictions

    # 9-10. Compare and select the best model automatically (lowest test RMSE)
    table = evaluation.build_comparison_table(results)
    best_name = evaluation.select_best_model(results)
    best_by_cv = min(results, key=lambda n: results[n]["cv_rmse_mean"])
    say("\nModel comparison (test set):")
    say(table.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    say(f"\nSelected model (lowest test RMSE): {best_name}")
    if best_by_cv != best_name:
        say(f"Note: cross-validation on the training data slightly prefers {best_by_cv}.")

    # 11. Save the complete pipeline (preprocessing + model) with Joblib
    model_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "pipeline": fitted[best_name],
        "model_name": best_name,
        "feature_columns": config.FEATURE_COLUMNS,
        # Range of every feature seen in training (used to warn about unusual inputs)
        "training_ranges": {c: [float(X_train[c].min()), float(X_train[c].max())]
                            for c in config.FEATURE_COLUMNS},
    }
    joblib.dump(bundle, model_path)

    # Also save all three fitted pipelines so the web app can show a real
    # current-sample prediction from every algorithm without retraining on click.
    all_models_path = config.MODELS_DIR / "all_models.pkl"
    joblib.dump({"models": fitted, "feature_columns": config.FEATURE_COLUMNS}, all_models_path)

    # 12. Save metrics (all values come from the real run above)
    metrics_json = {
        "dataset": config.DATASET_LABEL,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "random_state": config.RANDOM_STATE,
        "test_size": config.TEST_SIZE,
        "records_loaded": clean_report["rows_in"],
        "records_used": clean_report["rows_out"],
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "feature_columns": config.FEATURE_COLUMNS,
        "target_column": config.TARGET_COLUMN,
        "cleaning_report": clean_report,
        "models": results,
        "selection_criterion": "lowest RMSE on the held-out test set (ties: higher R2)",
        "best_model": best_name,
        "best_model_by_cross_validation": best_by_cv,
        "disclaimer": config.DISCLAIMER,
    }
    evaluation.save_metrics(metrics_json, metrics_path)
    evaluation.save_comparison_table(table, comparison_path)

    # Held-out rows: lets the GUI load a sample with a reference purity the model never trained on
    test_rows = X_test.copy()
    test_rows[config.TARGET_COLUMN] = y_test
    test_samples_path.parent.mkdir(parents=True, exist_ok=True)
    test_rows.to_csv(test_samples_path, index=False)

    # 13. Graphs (from the real predictions)
    if make_graphs:
        files = visualization.GRAPH_FILES
        visualization.plot_purity_distribution(df[config.TARGET_COLUMN], graphs_dir / files["Purity Distribution"])
        visualization.plot_model_comparison(table, best_name, graphs_dir / files["Model Comparison"])
        visualization.plot_actual_vs_predicted(y_test, test_predictions[best_name], best_name,
                                               graphs_dir / files["Actual vs Predicted"])
        visualization.plot_residuals(y_test, test_predictions[best_name], best_name,
                                     graphs_dir / files["Prediction Errors"])
        say(f"Graphs saved in: {graphs_dir}")

    say(f"Model saved to: {model_path}")
    return metrics_json


def main():
    config.ensure_directories()
    try:
        train_and_evaluate()
    except FileNotFoundError as error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
