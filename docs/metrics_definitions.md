# Metric Definitions

## Engagement Metrics

- **DAU / WAU / MAU**: Distinct patients with at least one `app_sessions` event in the trailing 1 / 7 / 30 days.
- **Retention (Day N)**: % of patients with an app session on day N after first session, relative to their cohort.

## Clinical Operations Metrics

- **No-show rate**: % of scheduled appointments with status = `no_show`, segmented by demographic/condition.
- **Medication adherence rate**: % of expected medication doses logged as taken, per patient per period.
- **Medication non-adherence risk**: ML-predicted probability that a patient's 14-day adherence rate falls below 80% (see `ml/adherence_risk_model/`). Originally scoped as a 30-day readmission model, but Synthea's CSV export doesn't include an encounters table at the population sizes used here -- adherence is the closest available behavioral-risk proxy and maps directly onto the North Star metric below. See `docs/design_decisions.md` for the full rationale.

## Product Analytics Metrics

- **Onboarding funnel conversion**: % progressing through signup → profile complete → first login → first appointment booked → first appointment attended.
- **North Star Metric (Weekly Adherent Patient Rate)**: % of chronic-condition patients tracked in a given week whose trailing 7-day medication adherence rate is ≥ 80% (see `analytics/north_star_metric.py`).
- **Experiment lift**: Difference in adherence/engagement rate between treatment (reminder nudge) and control groups, with confidence interval and p-value.
