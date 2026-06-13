"""Medication non-adherence risk model.

Predicts whether a patient with a chronic condition will fall below an
80% medication adherence rate, using demographics, onboarding-funnel
completion, engagement segment, and medication-reminder notification
engagement from ``mart_adherence_summary`` and related marts.

Note on scope: the original architecture doc called for a "30-day
readmission" model (this directory was originally scaffolded as
``readmission_model``). The generated dataset has no encounters/admissions
table, so there's no ground truth to predict readmission against. Medication
non-adherence is the closest available clinical-risk analogue -- it's
predicted from the same kind of early/behavioral signal, feeds the same
care-team-outreach use case ("who should we call this week?"), and the data
actually exists. This mirrors the adjustment made to the dbt marts in Phase 3
when the architecture doc's plan didn't match the generated data.

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
with med_notif as (
    select
        patient_id,
        avg(case when opened then 1.0 else 0.0 end) as med_reminder_open_rate,
        count(*)                                     as med_reminders_sent
    from main_marts.fct_notifications
    where notification_type = 'medication_reminder'
    group by 1
),
funnel as (
    select patient_id, funnel_steps_completed
    from main_marts.fct_onboarding_funnel
)
select
    a.patient_id,
    a.ab_test_group,
    a.days_tracked,
    p.age,
    p.gender,
    p.condition_count,
    p.engagement_segment,
    coalesce(f.funnel_steps_completed, 0)   as funnel_steps_completed,
    coalesce(m.med_reminder_open_rate, 0)   as med_reminder_open_rate,
    coalesce(m.med_reminders_sent, 0)       as med_reminders_sent,
    cast(a.adherence_rate < 0.8 as int)     as is_low_adherence
from main_marts.mart_adherence_summary a
join main_marts.dim_patients p using (patient_id)
left join med_notif m using (patient_id)
left join funnel f using (patient_id)
"""

NUMERIC_FEATURES = [
    "days_tracked",
    "age",
    "condition_count",
    "funnel_steps_completed",
    "med_reminder_open_rate",
    "med_reminders_sent",
]
CATEGORICAL_FEATURES = ["gender", "engagement_segment", "ab_test_group"]


def main() -> None:
    con = common.get_connection()
    df = common.query_df(con, FEATURES_SQL)

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["is_low_adherence"].astype(int).to_numpy()

    pipeline = common.build_pipeline(NUMERIC_FEATURES, CATEGORICAL_FEATURES, n_estimators=80, max_depth=2)

    metrics = common.cross_validated_metrics(pipeline, X, y)
    common.print_summary("Medication Non-Adherence Risk Model", metrics)

    pipeline, shap_values, X_transformed, feature_names = common.fit_and_explain(pipeline, X, y)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    common.save_shap_summary_plot(shap_values, X_transformed, feature_names, ARTIFACT_DIR / "shap_summary.png")
    common.save_shap_bar_plot(shap_values, feature_names, ARTIFACT_DIR / "shap_importance.png")
    common.write_artifacts(ARTIFACT_DIR, pipeline, metrics)

    print(f"\nArtifacts written to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
