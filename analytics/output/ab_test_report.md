# A/B Test Readout: Medication Reminder Nudge

**Design:** patients are randomly assigned to `treatment` (gets an extra `medication_reminder` push notification) or `control`. Alpha = 0.05.

## Primary metric: medication adherence rate

Adherent patient-days / tracked patient-days.

| Cohort | Tracked days | Adherent days | Adherence rate |
|---|---|---|---|
| control | 183 | 122 | 66.7% |
| treatment | 189 | 122 | 64.6% |

Lift: **-2.1 pp** (95% CI: [-11.8, +7.5] pp). z = -0.43, p = 0.668 -- **not statistically significant** at alpha = 0.05.

![Adherence by cohort](output/ab_test_adherence.png)

Treatment adherence is essentially flat vs. control (in this run, slightly *lower*, well within noise). **The nudge did not move the primary metric** -- this is a real, useful null result, not a bug.

## Secondary metric: medication-reminder open rate

| Cohort | Reminders sent | Reminders opened | Open rate |
|---|---|---|---|
| control | 41 | 17 | 41.5% |
| treatment | 86 | 50 | 58.1% |

Lift: **+16.7 pp** (95% CI: [-1.7, +35.0] pp). z = 1.76, p = 0.078 -- **not statistically significant** at alpha = 0.05.

![Medication reminder open rate by cohort](output/ab_test_notifications.png)

Treatment patients also simply receive more medication reminders (86 vs 41 sent) -- the intervention mechanism is working as designed (more reminders, higher open rate). The disconnect is between *opening a reminder* and *taking the medication that day* -- see Recommendations.

## Power & sample-size analysis

At the observed sample size (372 patient-days total, ~186 per arm), this experiment has **7% power** to detect the effect size actually observed (-2.1 pp) -- consistent with the non-significant result above.

To reliably detect a **5 percentage-point** lift in adherence (from a baseline of 67%) at 80% power and alpha = 0.05, the experiment would need approximately **1,337 patient-days per arm**. At ~6.5 tracked days per patient in this dataset, that's roughly **206 patients per arm** -- well beyond the current 25/25 split.

## Recommendations

1. **Don't ship on this result yet** -- the experiment is underpowered for the primary metric at this sample size; the null result could easily flip with more data.
2. **The mechanism works, the outcome doesn't (yet)** -- treatment patients open more medication reminders, but that isn't translating into more adherent days. Consider an intermediate metric (reminder -> in-app medication log within the same day) to test the causal chain more directly.
3. **Re-run at the architecture doc's target scale** (2,000-5,000 patients) -- at that scale, the same effect size would be well within reach of 80% power for adherence.
