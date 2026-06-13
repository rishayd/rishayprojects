# CarePulse ML Risk Models

Three classifiers built on the dbt marts in `data/warehouse.duckdb`, each
following the same pattern (see `common.py`):

1. Pull a feature table with a SQL query against `main_marts.*`.
2. `sklearn` `Pipeline`: `ColumnTransformer` (passthrough numeric +
   one-hot categorical) -> `XGBClassifier` (shallow trees, regularized --
   the dataset is small).
3. Evaluate with stratified k-fold cross-validation (out-of-fold
   predictions), since a single train/test split on this dataset would be
   too noisy to mean much.
4. Fit on all data and explain with SHAP (`TreeExplainer`).
5. Write `metrics.json`, `shap_summary.png`, `shap_importance.png`, and
   `model.joblib` to each model's `artifacts/` directory.

Run any model with:

```bash
python ml/<model>/train.py
# or against a different warehouse:
CAREPULSE_DB_PATH=/path/to/warehouse.duckdb python ml/<model>/train.py
```

## Models

### `no_show_model/` -- Appointment no-show risk

Predicts `is_no_show` for a scheduled appointment from appointment type,
day-of-week/month, and the patient's demographics + engagement profile.
The simulator's latent `no_show_propensity` is deliberately **excluded** --
it's the ground-truth signal used to generate the label, so including it
would just let the model read off the answer instead of learning from
observable behavior.

| | |
|---|---|
| Samples | 37 appointments |
| Positive rate | 16.2% (6 no-shows) |
| ROC AUC (out-of-fold) | 0.575 |
| Average precision (out-of-fold) | 0.248 |

With only 6 positive examples, this is right at the edge of what's
learnable -- the honest takeaway is "not enough no-show events yet to
beat the base rate by much," which is itself a useful finding (and would
resolve with the 2,000+ patient population the architecture doc
originally called for).

### `churn_model/` -- Disengagement risk

Predicts whether a patient ends up in the `disengaging` / `low_engagement`
segment, using only **early** signals: onboarding funnel completion,
days-to-first-login, notification open rate, and app activity in the first
14 days after signup. Lifetime session counts are excluded since they're
effectively definitional of the engagement segment.

| | |
|---|---|
| Samples | 50 patients |
| Positive rate | 42% (21 disengaged) |
| ROC AUC (out-of-fold) | 0.813 |
| Average precision (out-of-fold) | 0.773 |

This is the strongest of the three models and the most actionable: an
"early warning" score a product team could use to trigger a re-engagement
nudge before a patient drops off.

### `adherence_risk_model/` -- Medication non-adherence risk

Predicts whether a chronic-condition patient's medication adherence rate
falls below 80%, from demographics, onboarding completion, engagement
segment, and medication-reminder notification engagement.

| | |
|---|---|
| Samples | 25 patients (chronic-condition, adherence-tracked) |
| Positive rate | 60% (15 below 80% adherence) |
| ROC AUC (out-of-fold) | 0.900 |
| Average precision (out-of-fold) | 0.933 |

**Scope note:** this directory was originally scaffolded as
`readmission_model` per the architecture doc's "30-day readmission" model.
The generated dataset has no encounters/admissions table, so there's no
ground truth to predict readmission against. Medication non-adherence is
the closest available clinical-risk analogue -- predicted from the same
kind of early/behavioral signal, and feeding the same "who should the care
team check in on this week?" use case. This mirrors the adjustment made to
the dbt marts in Phase 3 when the architecture doc's plan didn't match the
generated data.

## Caveats

All three models are trained on a 50-patient synthetic sample (the
architecture doc's target population was 2,000-5,000). Cross-validated AUCs
above should be read as a sanity check on the *methodology* -- feature
pipeline, leakage avoidance, SHAP explainability -- rather than as
production-grade performance numbers. Re-running `python ml/<model>/train.py`
against a larger generated population (`src/data_generation/`) is a drop-in
operation: the SQL feature queries and pipelines are population-size
agnostic.
