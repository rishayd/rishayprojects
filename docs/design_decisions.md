# Design Decisions & Tradeoffs

This doc collects the judgment calls made while building CarePulse Analytics
-- places where the implementation diverged from `docs/architecture.md`'s
original plan, or where a tradeoff was made deliberately and is worth being
explicit about. The goal throughout was **honest adaptation over silent
deviation**: every pivot below is documented in the relevant module's README
as well.

## 1. Dataset scale: 50 patients vs. the planned 2,000-5,000

The architecture doc called for 2,000-5,000 Synthea patients. The actual
pipeline runs against a **50-patient** sample generated via
`tests/fixtures/generate_mock_synthea.py` (a lightweight mock that avoids the
Java/Synthea dependency for development and CI).

**Why:** iterating on dbt models, dashboard queries, ML feature pipelines,
and analytics scripts is much faster against a small dataset, and the mock
generator removes a ~100MB Java dependency from the dev loop entirely. Every
piece of downstream code -- dbt models, `ml/*/train.py`, `analytics/*.py` --
is written to be **population-size agnostic**: SQL queries use aggregates and
joins with no hardcoded thresholds tied to row counts, and the ML pipelines
use stratified k-fold CV with a fold count that adapts to the minority class
size (`max(2, min(5, n_minority))`).

**Consequences, called out honestly rather than hidden:**
- ML model sample sizes are tiny (24-50 rows, sometimes single digits of
  positive examples for the no-show model). Cross-validated AUCs are a
  methodology sanity check, not production performance numbers (`ml/README.md`).
- The A/B test is severely underpowered (~7% power to detect the observed
  effect; `analytics/output/ab_test_report.md` computes the ~1,300
  patient-days per arm actually needed).
- The North Star metric's weekly trend is dominated by cohort-ramp (patients
  signing up at different points over a 4-week window), not a genuine
  longitudinal signal (`analytics/output/north_star_report.md`).

**Why this is fine for a portfolio project:** the point being demonstrated is
the *pipeline* -- feature engineering, leakage avoidance, statistical
methodology, dashboard design -- not a specific number. Running
`run_synthea.sh 2000` plus the same downstream commands at full scale would
turn these "methodology sanity checks" into real findings with no code
changes. That portability is itself part of the design.

## 2. The readmission -> medication-adherence pivot

The architecture doc's Phase 5 called for a "30-day readmission risk model."
Synthea's CSV export at the population sizes used here doesn't include an
encounters/admissions table with enough inpatient stays to define a
readmission label -- there's no ground truth to train against.

**Resolution:** `ml/readmission_model/` was renamed to
`ml/adherence_risk_model/`, predicting whether a chronic-condition patient's
medication adherence rate falls below 80% (ROC AUC 0.900 on 25 patients).
This is the closest available analogue: a behavioral-risk signal, predictable
from the same kind of early/demographic features, feeding the same "who
should the care team check in on this week?" workflow a readmission model
would serve. It also ties directly into the North Star metric (Weekly
Adherent Patient Rate), which a readmission model wouldn't have.

This mirrors an earlier, smaller adjustment in Phase 3: the dbt marts were
designed around the data Synthea + the app-event simulator actually produce,
not a fixed schema assumed up front. `docs/metrics_definitions.md` and
`docs/architecture.md` have been updated to reflect this pivot rather than
leaving stale "readmission" references.

## 3. ML leakage-avoidance decisions

Each model deliberately excludes features that would leak the label:

- **No-show model**: excludes the simulator's latent `no_show_propensity`,
  which is the ground-truth parameter used to *generate* the `is_no_show`
  label. Including it would let the model "read off the answer" rather than
  learn from observable scheduling/demographic signals.
- **Churn model**: excludes lifetime session counts and other signals that
  are effectively definitional of the `engagement_segment` label itself.
  Only the first **14 days** of post-signup behavior is used, so the model
  reflects an actually-actionable "early warning" -- a score computable while
  there's still time to intervene.
- **Adherence risk model**: uses only demographics, onboarding completion,
  engagement segment, and medication-reminder notification engagement --
  signals available early, not adherence history itself (which would be
  circular).

The common thread: a feature is excluded if it's either (a) the generative
ground truth behind the label, or (b) only knowable *after* the outcome has
already happened. This is a stricter bar than "drop the literal target
column," and it's the main reason the no-show model's AUC (0.575) looks weak
relative to the others -- it really is a hard, mostly-unlearnable problem at
this sample size and feature set, and that's a more honest result than an
inflated AUC from a leaked feature.

## 4. A/B test: reporting a null/underpowered result as a result

`analytics/ab_test_analysis.py` finds that the medication-reminder nudge
increases reminder open rates by +16.7pp (the *mechanism* works) but doesn't
move medication adherence (-2.1pp, p=0.668, not significant) -- and the
script computes that the experiment has only ~7% power to detect the effect
it observed.

**Decision:** report this as a genuine finding with a sample-size
recommendation, rather than searching for a "significant" result or quietly
omitting the power analysis. A real experimentation platform should surface
*both* "is this significant" and "could this experiment have detected an
effect if there were one" -- the second question is what `required_sample_size()`
and `achieved_power()` answer. This is the kind of thing that separates
"data analyst ran a t-test" from "product analyst can tell you whether the
t-test result means anything."

## 5. Tech stack choices

| Choice | Why |
|---|---|
| **DuckDB** | Embedded, zero-ops OLAP database -- no server to run, fast on analytical queries, and `dbt-duckdb` + `duckdb`'s Python API make it a drop-in for both the dbt warehouse and direct dashboard/ML queries. For a single-file portfolio project, this avoids the overhead (and cost) of Postgres/Snowflake/BigQuery while still demonstrating real SQL-based modeling. |
| **dbt (dbt-core + dbt-duckdb)** | Industry-standard transformation layer: staging -> intermediate -> marts, with 86 data tests (uniqueness, not-null, referential integrity, accepted ranges) as a CI gate. Demonstrates the modeling discipline expected in a DE role regardless of warehouse choice. |
| **Dagster** | Asset-based orchestration over the generation -> ingestion -> dbt pipeline. Chosen over Airflow for its lighter local dev experience (`dagster dev`) and asset-centric model, which maps cleanly onto "raw tables -> staging -> marts" as a lineage graph. |
| **Streamlit** | Fastest path from "DuckDB query" to "interactive multi-page dashboard" without a separate frontend build step -- appropriate for an analytics portfolio piece where the SQL and the chart logic are the point, not frontend engineering. |
| **XGBoost + scikit-learn Pipeline + SHAP** | `ColumnTransformer` -> `XGBClassifier` is a standard, defensible baseline for small tabular classification problems; shallow trees + regularization (`max_depth=3`, subsampling) suit the small sample sizes here. SHAP `TreeExplainer` gives per-feature, per-prediction explanations -- important in a health-tech context where "why did the model flag this patient" matters as much as the prediction itself. (Pinned to `xgboost==2.0.3` -- see `ml/common.py` -- because shap 0.49's `TreeExplainer` can't parse xgboost 3.x's `base_score` serialization.) |
| **statsmodels (proportions_ztest, NormalIndPower)** | Standard, well-tested implementations of two-proportion z-tests and power analysis -- avoids hand-rolling statistical formulas for the A/B test readout. |
| **GitHub Actions** | Free, zero-config CI tightly integrated with the repo; runs the full generate -> ingest -> dbt build -> ML smoke tests -> analytics smoke tests pipeline on every push, so the "it works on my machine" risk is continuously checked against a fresh dataset. |

## 6. What's explicitly out of scope

This is a portfolio project demonstrating a pipeline architecture and
analytical methodology, not a production health-tech system. Notably out of
scope: authentication/authorization, HIPAA-compliant data handling (the data
is fully synthetic, so this doesn't apply here but would in a real system),
multi-tenancy, real-time/streaming ingestion, and model monitoring/retraining
infrastructure. `docs/deployment.md` Option C (Docker) sketches where
auth would sit if this were productionized.
