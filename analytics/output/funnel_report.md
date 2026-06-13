# Onboarding Funnel Analysis

Cohort of 50 patients across 6 onboarding steps (signup -> profile complete -> consent signed -> first login -> first appointment booked -> first appointment attended).

## Cumulative conversion (overall)

| Step | Patients reached | Cumulative conversion |
|---|---|---|
| signup | 50 | 100% |
| profile_complete | 44 | 88% |
| consent_signed | 36 | 72% |
| first_login | 33 | 66% |
| first_appointment_booked | 26 | 52% |
| first_appointment_attended | 15 | 30% |

Only **30%** of patients who sign up go on to attend a first appointment (15 of 50).

![Cumulative conversion](output/funnel_conversion.png)

## Step-over-step (conditional) conversion

| From -> To | Conditional conversion |
|---|---|
| signup -> profile_complete | 88% |
| profile_complete -> consent_signed | 82% |
| consent_signed -> first_login | 92% |
| first_login -> first_appointment_booked | 79% |
| first_appointment_booked -> first_appointment_attended | 58% |

**Biggest leak:** `first_appointment_attended` retains only 58% of patients who reached the prior step -- this is the highest-leverage step to investigate/improve.

![Conditional conversion](output/funnel_dropoff.png)

## By A/B cohort

Final-step (first appointment attended) conversion is **12%** for `treatment` vs **18%** for `control` (-6.0 pp). See `ab_test_report.md` for whether this difference is statistically meaningful -- with this sample size it likely is not on its own.

## Time-to-convert between steps

| Transition | Patients completing both | Median days |
|---|---|---|
| signup -> profile_complete | 44 | 1.1 |
| profile_complete -> consent_signed | 36 | 1.0 |
| consent_signed -> first_login | 33 | 1.2 |
| first_login -> first_appointment_booked | 26 | 0.9 |
| first_appointment_booked -> first_appointment_attended | 15 | 0.7 |

## Caveats

This is a 50-patient synthetic cohort, so cohort splits in particular (roughly 25/25) are noisy -- treat percentage-point differences between `treatment` and `control` here as directional, not conclusive. The shape of the funnel (steady ~85-90% retention through `consent_signed`, then a sharper drop into `first_appointment_booked`/`attended`) is the more robust signal and would be the first thing to validate against a larger run.
