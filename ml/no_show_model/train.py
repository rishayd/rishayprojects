"""No-show risk model.

Predicts whether a scheduled appointment will end in a no-show, using
appointment-level features (type, day-of-week, month) plus the patient's
demographics and engagement profile from ``dim_patients``.

Note on leakage: the data simulator assigns each patient a latent
``no_show_propensity`` that directly drives no-show probability. We
deliberately exclude it from the feature set -- including it would let the
model "cheat" by reading off the ground-truth label rather than learning
from observable behavioral/demographic signal, which is the realistic
setting for a production model.

Usage:
    python train.py
    CAREPULSE_DB_PATH=/path/to/warehouse.duckdb python train.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import common

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"

FEATURES_SQL = """
select
    a.appointment_id,
    a.is_no_show,
    a.appointment_type,
    dayofweek(a.scheduled_date)  as scheduled_dow,
    month(a.scheduled_date)      as scheduled_month,
    p.age,
    p.gender,
    p.has_chronic_condition,
    p.condition_count,
    p.engagement_segment,
    p.ab_test_group
from main_marts.fct_appointments a
join main_marts.dim_patients p using (patient_id)
"""

NUMERIC_FEATURES = ["scheduled_dow", "scheduled_month", "age", "condition_count", "has_chronic_condition"]
CATEGORICAL_FEATURES = ["appointment_type", "gender", "engagement_segment", "ab_test_group"]


def main() -> None:
    con = common.get_connection()
    df = common.query_df(con, FEATURES_SQL)

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["is_no_show"].astype(int).to_numpy()

    pipeline = common.build_pipeline(NUMERIC_FEATURES, CATEGORICAL_FEATURES, n_estimators=80, max_depth=2)

    metrics = common.cross_validated_metrics(pipeline, X, y)
    common.print_summary("No-Show Risk Model", metrics)

    pipeline, shap_values, X_transformed, feature_names = common.fit_and_explain(pipeline, X, y)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    common.save_shap_summary_plot(shap_values, X_transformed, feature_names, ARTIFACT_DIR / "shap_summary.png")
    common.save_shap_bar_plot(shap_values, feature_names, ARTIFACT_DIR / "shap_importance.png")
    common.write_artifacts(ARTIFACT_DIR, pipeline, metrics)

    print(f"\nArtifacts written to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
