"""Disengagement (churn) risk model.

Predicts whether a patient will end up in the ``disengaging`` or
``low_engagement`` segment, using only *early* signals available shortly
after onboarding -- the onboarding funnel itself, time-to-first-login,
notification engagement, and app activity in the first two weeks after
signup, plus demographics.

Note on leakage: ``engagement_segment`` (the label source) is also used
elsewhere in the warehouse to drive simulated session volume. We
deliberately avoid using lifetime/total session counts as features --
those would essentially encode the label. Restricting to a 14-day
post-signup window keeps this a genuine "early warning" model: the kind
of thing a product team could act on (e.g. trigger a re-engagement
campaign) before a patient is fully disengaged.

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
with funnel as (
    select
        patient_id,
        signup_at,
        first_login_at,
        funnel_steps_completed,
        date_diff('day', signup_at, first_login_at) as days_to_first_login
    from main_marts.fct_onboarding_funnel
),
notif as (
    select
        patient_id,
        avg(case when opened then 1.0 else 0.0 end) as notification_open_rate,
        count(*)                                     as notifications_sent
    from main_marts.fct_notifications
    group by 1
),
early_activity as (
    -- App activity in the 14 days following signup only, to avoid leaking
    -- lifetime engagement (which is what defines the label).
    select
        e.patient_id,
        sum(e.session_count)        as early_session_count,
        avg(e.avg_duration_seconds)  as early_avg_duration_seconds
    from main_marts.fct_daily_engagement e
    join funnel f using (patient_id)
    where cast(e.session_date as timestamp) <= f.signup_at + interval 14 day
    group by 1
)
select
    p.patient_id,
    p.age,
    p.gender,
    p.has_chronic_condition,
    p.condition_count,
    p.ab_test_group,
    f.funnel_steps_completed,
    coalesce(f.days_to_first_login, -1)            as days_to_first_login,
    coalesce(n.notification_open_rate, 0)          as notification_open_rate,
    coalesce(n.notifications_sent, 0)              as notifications_sent,
    coalesce(ea.early_session_count, 0)            as early_session_count,
    coalesce(ea.early_avg_duration_seconds, 0)     as early_avg_duration_seconds,
    cast(p.engagement_segment in ('disengaging', 'low_engagement') as int) as is_disengaged
from main_marts.dim_patients p
left join funnel f using (patient_id)
left join notif n using (patient_id)
left join early_activity ea using (patient_id)
"""

NUMERIC_FEATURES = [
    "age",
    "has_chronic_condition",
    "condition_count",
    "funnel_steps_completed",
    "days_to_first_login",
    "notification_open_rate",
    "notifications_sent",
    "early_session_count",
    "early_avg_duration_seconds",
]
CATEGORICAL_FEATURES = ["gender", "ab_test_group"]


def main() -> None:
    con = common.get_connection()
    df = common.query_df(con, FEATURES_SQL)

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["is_disengaged"].astype(int).to_numpy()

    pipeline = common.build_pipeline(NUMERIC_FEATURES, CATEGORICAL_FEATURES, n_estimators=100, max_depth=3)

    metrics = common.cross_validated_metrics(pipeline, X, y)
    common.print_summary("Disengagement (Churn) Risk Model", metrics)

    pipeline, shap_values, X_transformed, feature_names = common.fit_and_explain(pipeline, X, y)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    common.save_shap_summary_plot(shap_values, X_transformed, feature_names, ARTIFACT_DIR / "shap_summary.png")
    common.save_shap_bar_plot(shap_values, feature_names, ARTIFACT_DIR / "shap_importance.png")
    common.write_artifacts(ARTIFACT_DIR, pipeline, metrics)

    print(f"\nArtifacts written to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
