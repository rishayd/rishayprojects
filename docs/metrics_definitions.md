# Metric Definitions

> To be refined as marts are built (Phase 3+).

## Engagement Metrics

- **DAU / WAU / MAU**: Distinct patients with at least one `app_sessions` event in the trailing 1 / 7 / 30 days.
- **Retention (Day N)**: % of patients with an app session on day N after first session, relative to their cohort.

## Clinical Operations Metrics

- **No-show rate**: % of scheduled appointments with status = `no_show`, segmented by demographic/condition.
- **Medication adherence rate**: % of expected medication doses logged as taken, per patient per period.
- **30-day readmission rate**: % of inpatient encounters followed by another inpatient encounter within 30 days.

## Product Analytics Metrics

- **Onboarding funnel conversion**: % progressing through signup → profile complete → first login → first appointment booked → first appointment attended.
- **North Star Metric**: % of active patients adherent (medication adherence ≥ 80%) at 90 days post-onboarding.
- **Experiment lift**: Difference in adherence/engagement rate between treatment (reminder nudge) and control groups, with confidence interval and p-value.
