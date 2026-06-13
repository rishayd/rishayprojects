"""Shared utilities for the CarePulse ML risk models.

Each model (no-show, churn/disengagement, medication non-adherence) follows
the same pattern:

1. Pull a feature table from the dbt marts in ``data/warehouse.duckdb`` via
   SQL.
2. Build a small ``sklearn`` pipeline (preprocessing + ``XGBClassifier``).
3. Evaluate with stratified k-fold cross-validation (the synthetic dataset
   is small, so a single train/test split would be noisy).
4. Fit the final model on all available data and explain it with SHAP.
5. Write ``metrics.json``, a SHAP summary plot, and the fitted pipeline to
   ``ml/<model>/artifacts/``.

This module holds the bits that are identical across all three models so
each ``train.py`` can focus on feature engineering and framing.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import duckdb
import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Read-only connection to the dbt-built warehouse.

    Defaults to ``data/warehouse.duckdb``, overridable with the
    ``CAREPULSE_DB_PATH`` env var (matches the convention used by the dbt
    project and Dagster pipeline).
    """
    path = db_path or os.environ.get("CAREPULSE_DB_PATH") or str(DEFAULT_DB_PATH)
    return duckdb.connect(path, read_only=True)


def query_df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetchdf()


def build_pipeline(
    numeric_features: list[str],
    categorical_features: list[str],
    *,
    n_estimators: int = 100,
    max_depth: int = 3,
    learning_rate: float = 0.1,
) -> Pipeline:
    """A small, regularized XGBoost pipeline.

    Depth/estimator counts are kept modest deliberately: the synthetic
    dataset has dozens-to-low-hundreds of rows, and a deep/large ensemble
    would simply memorize it.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ]
    )
    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", model)])


def cross_validated_metrics(pipeline: Pipeline, X: pd.DataFrame, y: np.ndarray, max_splits: int = 5) -> dict:
    """Stratified k-fold out-of-fold evaluation.

    ``n_splits`` is capped by the smaller class count so this degrades
    gracefully on small/imbalanced samples instead of raising.
    """
    min_class_count = int(np.bincount(y).min())
    n_splits = max(2, min(max_splits, min_class_count))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    proba = cross_val_predict(pipeline, X, y, cv=cv, method="predict_proba")[:, 1]
    preds = (proba >= 0.5).astype(int)

    return {
        "n_samples": int(len(y)),
        "n_positive": int(y.sum()),
        "positive_rate": float(y.mean()),
        "cv_folds": n_splits,
        "roc_auc": float(roc_auc_score(y, proba)) if len(np.unique(y)) > 1 else None,
        "average_precision": float(average_precision_score(y, proba)) if len(np.unique(y)) > 1 else None,
        "confusion_matrix": confusion_matrix(y, preds).tolist(),
        "classification_report": classification_report(y, preds, output_dict=True, zero_division=0),
    }


def transformed_feature_names(pipeline: Pipeline) -> list[str]:
    return list(pipeline.named_steps["preprocess"].get_feature_names_out())


def fit_and_explain(pipeline: Pipeline, X: pd.DataFrame, y: np.ndarray) -> tuple[Pipeline, np.ndarray, np.ndarray, list[str]]:
    """Fit on all data and return SHAP values for the transformed features."""
    pipeline.fit(X, y)
    feature_names = transformed_feature_names(pipeline)
    X_transformed = pipeline.named_steps["preprocess"].transform(X)

    model = pipeline.named_steps["model"]
    # Work around a shap/xgboost interop issue: newer xgboost versions
    # serialize `base_score` as a bracketed array string (e.g.
    # "[1.62E-1]"), which shap's float() parsing chokes on. Rewrite the
    # booster config with a plain float before handing it to shap.
    booster = model.get_booster()
    config = json.loads(booster.save_config())
    raw_base_score = config["learner"]["learner_model_param"]["base_score"]
    match = re.search(r"[-+0-9.eE]+", raw_base_score)
    if match:
        config["learner"]["learner_model_param"]["base_score"] = match.group(0)
        booster.load_config(json.dumps(config))

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_transformed)
    if isinstance(shap_values, list):
        # binary classifier returning [class0, class1]
        shap_values = shap_values[1]
    return pipeline, shap_values, X_transformed, feature_names


def save_shap_summary_plot(shap_values: np.ndarray, X_transformed: np.ndarray, feature_names: list[str], output_path: Path, max_display: int = 15) -> None:
    plt.figure(figsize=(8, 6))
    shap.summary_plot(
        shap_values,
        X_transformed,
        feature_names=feature_names,
        show=False,
        max_display=max_display,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches="tight")
    plt.close()


def save_shap_bar_plot(shap_values: np.ndarray, feature_names: list[str], output_path: Path, max_display: int = 15) -> None:
    plt.figure(figsize=(8, 6))
    shap.summary_plot(
        shap_values,
        feature_names=feature_names,
        plot_type="bar",
        show=False,
        max_display=max_display,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches="tight")
    plt.close()


def write_artifacts(output_dir: Path, pipeline: Pipeline, metrics: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_dir / "model.joblib")
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=float)


def print_summary(model_name: str, metrics: dict) -> None:
    print(f"\n=== {model_name} ===")
    print(f"n_samples={metrics['n_samples']}  n_positive={metrics['n_positive']}  "
          f"positive_rate={metrics['positive_rate']:.2%}  cv_folds={metrics['cv_folds']}")
    if metrics["roc_auc"] is not None:
        print(f"ROC AUC (out-of-fold): {metrics['roc_auc']:.3f}")
        print(f"Average precision (out-of-fold): {metrics['average_precision']:.3f}")
    print(f"Confusion matrix (out-of-fold): {metrics['confusion_matrix']}")
