# North Star Metric: Weekly Adherent Patient Rate

**Definition:** % of chronic-condition patients tracked that week whose 7-day medication adherence rate is >= 80%.

**Why this metric:** it's the closest measurable proxy for the product's core promise (helping chronic-condition patients stay on their treatment plan), it's actionable weekly at the patient level, and it sits downstream of onboarding, engagement, and the notification/reminder experiment -- i.e. every other workstream should show up here eventually.

## Weekly trend

| Week of | Patients tracked | Patients adherent (>=80%) | NSM | Avg weekly adherence |
|---|---|---|---|---|
| 2026-05-18 | 8 | 2 | 25% | 73.5% |
| 2026-05-25 | 17 | 7 | 41% | 60.5% |
| 2026-06-01 | 20 | 7 | 35% | 67.1% |
| 2026-06-08 | 25 | 12 | 48% | 65.3% |

![North Star trend](output/north_star_trend.png)

## Supporting metric: Weekly Active Patients

| Week of | WAU |
|---|---|
| 2026-05-11 | 1 |
| 2026-05-18 | 12 |
| 2026-05-25 | 28 |
| 2026-06-01 | 36 |
| 2026-06-08 | 43 |

## Reading the trend

The NSM rises from 41% (week of 2026-05-25) to 48% (week of 2026-06-08), and WAU rises from 12 to 43. **Both of these trends are dominated by the synthetic cohort's staggered onboarding** -- patients sign up (and start being tracked) at different points over the ~4-week generation window, so later weeks simply have more patients in steady state, not necessarily *better* adherence per patient. The first week (2026-05-18, n=8) is a partial-cohort artifact and excluded from the headline comparison above.

In a production setting with a stable patient base, this chart would be read as a genuine retention/outcome signal. Here, the more useful reads are **cross-sectional**: the A/B test (`ab_test_report.md`) and the no-show / churn / adherence-risk models (`ml/`) decompose *why* a given patient lands above or below the 80% line, which is more actionable than the aggregate trend on this small, short-window sample.

## Caveats

- 25 patients tracked, over 4-5 weeks -- small N and short window for any time-series read.
- Re-running against a larger, longer-running generated population (`src/data_generation/`) would let this metric be read as an actual trend rather than a cohort-ramp artifact.
