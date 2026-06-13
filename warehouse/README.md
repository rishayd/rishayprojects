# Warehouse (dbt project)

dbt models that transform the `raw.*` tables (loaded by
`src/ingestion/load_raw_to_duckdb.py`) into clean staging models, with data
quality tests on every model.

## Setup

```bash
pip install -r ../requirements.txt

# 1. Load raw CSVs into DuckDB
python ../src/ingestion/load_raw_to_duckdb.py --data-dir ../data --db-path ../data/warehouse.duckdb

# 2. Run dbt
export DBT_PROFILES_DIR=$(pwd)
dbt build
```

`dbt build` runs all models and all data tests. No external dbt packages are
required (a small custom `accepted_range` generic test lives in
`macros/generic_tests/`).

## Project Layout

```
warehouse/
├── dbt_project.yml
├── profiles.yml
├── macros/
│   └── generic_tests/
│       └── accepted_range.sql   # custom min/max range test
└── models/
    ├── staging/                 # 1:1 cleaned views over raw sources
    │   ├── _sources.yml
    │   ├── _staging.yml         # schema + data tests
    │   ├── stg_patients.sql
    │   ├── stg_conditions.sql
    │   ├── stg_onboarding_events.sql
    │   ├── stg_app_sessions.sql
    │   ├── stg_notifications.sql
    │   ├── stg_appointments.sql
    │   └── stg_medication_logs.sql
    ├── intermediate/            # reusable aggregations
    │   ├── _intermediate.yml
    │   ├── int_patient_conditions.sql
    │   └── int_daily_app_activity.sql
    └── marts/                   # business-facing star schema
        ├── patient_engagement/
        │   ├── _patient_engagement.yml
        │   ├── dim_patients.sql
        │   ├── fct_app_sessions.sql
        │   ├── fct_daily_engagement.sql
        │   └── fct_onboarding_funnel.sql
        ├── clinical/
        │   ├── _clinical.yml
        │   ├── fct_appointments.sql
        │   └── fct_medication_adherence.sql
        └── product_metrics/
            ├── _product_metrics.yml
            ├── fct_notifications.sql
            ├── mart_adherence_summary.sql
            ├── mart_appointment_no_show.sql
            └── mart_funnel_conversion.sql
```

## Current Coverage

- 7 staging models (1:1 views over raw sources)
- 2 intermediate models (per-patient condition rollups, daily app activity)
- 10 mart models across `patient_engagement`, `clinical`, and
  `product_metrics`, including a `dim_patients` dimension and fact/summary
  tables for engagement, onboarding funnel, appointments, medication
  adherence, notifications, and A/B test cohorts
- 86 data tests: `not_null`, `unique`, `accepted_values`, `relationships`
  (referential integrity), and a custom `accepted_range` test for
  probability/count columns

Run `dbt build` — all 86 tests should pass (`PASS=86 ERROR=0`).

## Key Marts

- `dim_patients` — one row per patient: demographics, engagement segment,
  chronic condition summary, no-show propensity, adherence baseline, A/B
  cohort.
- `fct_daily_engagement` — daily session counts/durations per patient.
- `fct_onboarding_funnel` — per-patient funnel step timestamps and
  `funnel_steps_completed` (0-6).
- `fct_appointments` — appointments with `is_no_show`/`is_attended`/
  `is_cancelled` flags.
- `fct_medication_adherence` — daily medication-taken logs.
- `mart_adherence_summary` — per-patient adherence rate by A/B cohort.
- `mart_appointment_no_show` — no-show rate by engagement segment and
  chronic-condition status.
- `mart_funnel_conversion` — onboarding funnel conversion rates by step and
  A/B cohort.
