# CarePulse Product Analytics

Three product-analytics scripts over the dbt marts in `data/warehouse.duckdb`,
each producing a markdown report + chart(s) under `analytics/output/`.

Run any of them with:

```bash
python analytics/<script>.py
# or against a different warehouse:
CAREPULSE_DB_PATH=/path/to/warehouse.duckdb python analytics/<script>.py
```

## `funnel_analysis.py` -- Onboarding funnel

Cumulative and step-over-step (conditional) conversion through the 6-step
onboarding funnel (signup -> ... -> first appointment attended), time-to-
convert between steps, and a comparison across the A/B cohorts.

**Headline finding:** only 30% of patients who sign up attend a first
appointment; the single biggest leak is `first_appointment_booked ->
first_appointment_attended` (58% conditional conversion).

-> [`output/funnel_report.md`](output/funnel_report.md)

## `ab_test_analysis.py` -- Medication reminder nudge experiment

Full readout of the `treatment` (extra medication-reminder push) vs.
`control` experiment: two-proportion z-test + 95% CI on adherence (primary)
and reminder open rate (secondary), effect sizes, and a power/sample-size
analysis for a 5pp minimum detectable effect.

**Headline finding:** the reminder mechanism works (treatment patients open
medication reminders 16.7pp more often), but that hasn't translated into
higher adherence at this sample size (-2.1pp, not significant, ~7% power).
The report includes the sample size needed to actually detect a 5pp lift.

-> [`output/ab_test_report.md`](output/ab_test_report.md)

## `north_star_metric.py` -- North Star Metric

Defines and tracks **Weekly Adherent Patient Rate**: % of chronic-condition
patients whose 7-day medication adherence is >= 80%, with Weekly Active
Patients (WAU) as a supporting metric. Explains why adherence (rather than
engagement) is the right North Star for this product, and how the funnel and
A/B test work above feed into it.

-> [`output/north_star_report.md`](output/north_star_report.md)

## Caveats (apply to all three)

These analyses run against a 50-patient synthetic sample spanning ~4 weeks
(the architecture doc's target population was 2,000-5,000 patients over a
longer window). Sample sizes are called out explicitly in each report;
treat percentage-point comparisons as directional. Every script is written
to be population-size agnostic -- re-running against a larger generated
dataset (`src/data_generation/`) requires no code changes.
