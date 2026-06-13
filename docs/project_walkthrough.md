# Project Walkthrough

A phase-by-phase explanation of CarePulse Analytics: what was built, why,
and what alternatives were considered. Useful as a talk track for explaining
the project to others. For the deeper tradeoff discussion behind each
decision, see [design_decisions.md](design_decisions.md).

## Phase 0 — Setup

We scaffolded the repo, wrote an architecture doc with a phased plan, and
got a feasibility review before writing any pipeline code.

**Rationale:** a 7-phase build touching data generation, warehousing, ML,
and dashboards is easy to over-scope. Fixing the tech stack and sequencing
up front avoided rework and kept conventions (DB connection patterns, env
vars, directory layout) consistent across phases.

**Alternatives considered:** start coding immediately and let structure
emerge. Faster initially, but tends to produce inconsistent conventions
across phases as the project grows.

## Phase 1 — Data foundation (Synthea + app-event simulator)

[Synthea](https://github.com/synthetichealth/synthea) generates synthetic
patient demographics and conditions. A custom Python simulator layers on top
to produce the "app" data Synthea doesn't generate: logins, onboarding
funnel events, notifications, appointments, and medication logs, each tied
to a patient's engagement segment and A/B test group.

**Rationale:** avoid any real PHI while still getting realistic, internally
consistent behavioral data -- the kind of data needed for funnels, A/B
tests, and risk models to be meaningful.

**Alternatives considered:** a real de-identified healthcare dataset (privacy
and licensing friction, and you can't reshape it to fit a specific funnel/A-B
design); hand-rolled random data (would lack the realistic correlations --
e.g. disengaged patients having lower adherence -- that make the later ML
and analytics work meaningful).

## Phase 2 — Ingestion & dbt staging

Raw CSVs load into DuckDB under a `raw` schema, then dbt staging models
clean/type/dedupe them with data-quality tests (not-null, unique,
referential integrity, accepted ranges).

**Rationale:** DuckDB is an embedded, zero-ops analytical database -- no
server, just a file -- while still being a real columnar warehouse that
dbt-duckdb supports natively. dbt is the standard for testable,
version-controlled SQL transformations.

**Alternatives considered:** Postgres/Snowflake/BigQuery would demonstrate
the same dbt skills but add infrastructure cost/complexity unnecessary for a
single-file portfolio project; a pure-pandas pipeline would skip dbt's
testing and lineage tooling entirely.

## Phase 3 — dbt marts & Dagster orchestration

On top of staging, intermediate and mart models -- `dim_patients`,
`fct_appointments`, `fct_medication_adherence`, `fct_daily_engagement`,
`fct_onboarding_funnel`, plus summary marts -- form the single source of
truth consumed by the dashboard, ML models, and analytics scripts. Dagster
wraps generation -> ingestion -> dbt build as an asset graph so the whole
pipeline materializes with one command.

**Rationale:** Dagster was chosen over Airflow for its lighter local dev
loop (`dagster dev`) and because its asset model maps naturally onto
"raw -> staging -> marts" lineage.

**Alternatives considered:** Airflow or Prefect would work but add more
operational overhead for local development; skipping orchestration and
running scripts in sequence would be simpler but less demonstrative of DE
practice.

## Phase 4 — Streamlit dashboards

A 4-page Streamlit app (Home, Engagement, Clinical Ops, Product Analytics)
reads directly from the marts via a shared `db.py` connection layer, so it
always reflects the latest `dbt build`.

**Rationale:** Streamlit gets you from "DuckDB query" to "interactive
dashboard" with no separate frontend build -- appropriate when the SQL and
chart logic are the point, not UI engineering.

**Alternatives considered:** a BI tool like Looker/Tableau/Power BI would be
more "enterprise" but isn't code-based or git-trackable; a custom React + API
backend would demonstrate frontend skills but is overkill for an analytics
portfolio piece.

## Phase 5 — ML risk models (no-show, churn, medication adherence)

Three classifiers (sklearn `Pipeline` + XGBoost, evaluated via stratified
k-fold CV, explained with SHAP) predict appointment no-shows, patient
disengagement, and medication non-adherence. Each model deliberately
excludes features that would leak the label -- e.g. the simulator's internal
"no-show propensity" parameter, or lifetime session counts that are
definitionally tied to the churn label.

**Rationale / pivot:** we originally planned a 30-day readmission model, but
Synthea's CSV export doesn't include enough encounter/admission data to
support that label. We pivoted to medication-adherence risk -- a closer fit
to the data we actually have, and it ties directly into the North Star
metric.

**Alternatives considered:** logistic regression would be more interpretable
as a baseline but likely weaker on non-linear interactions; a train/test
split instead of CV would be simpler but far noisier given the small
(24-50 row) samples; LightGBM/CatBoost are comparable choices to XGBoost with
similar tradeoffs.

## Phase 6 — Product analytics (funnel, A/B test, North Star)

The funnel script computes cumulative and step-over-step conversion through
onboarding and identifies the biggest drop-off point. The A/B test script
runs a two-proportion z-test on the medication-reminder nudge, plus a
power/sample-size analysis -- which matters more than the significance test
itself, because it reveals the experiment is underpowered (~7% power) rather
than just reporting "not significant." The North Star metric (Weekly
Adherent Patient Rate) ties the whole product together: onboarding feeds it,
the reminder experiment is a lever on it, and engagement is an input to it
rather than the goal itself.

**Alternatives considered:** a Bayesian framing of the A/B test would avoid
some p-value interpretation pitfalls; an engagement-based North Star (e.g.
WAU) would be easier to move but wouldn't reflect the product's actual value
proposition (medication adherence, not app usage).

## Phase 7 — CI, deployment docs, design decisions, polish

GitHub Actions generates a small synthetic dataset on every push, runs it
through ingestion + the full dbt build (86 tests), and smoke-tests every ML
model and analytics script -- so "it works on my machine" is continuously
checked against a fresh dataset rather than a stale fixture. Deployment docs
cover Streamlit Community Cloud (building the warehouse at startup, since the
warehouse file is gitignored), and a design-decisions doc documents every
tradeoff above in one place.

**Pivot:** live dashboard screenshots weren't possible -- the dev sandbox has
no browser runtime and no permission to install one. The dashboard README
instead points to the static analytics charts and explains how to run the
app locally to see the real thing.

**Alternatives considered:** CI could run against a checked-in warehouse
snapshot instead of regenerating data each time (faster, but risks drift from
the actual generator code); deployment could use Docker instead of Streamlit
Cloud for more control, at the cost of more setup.
