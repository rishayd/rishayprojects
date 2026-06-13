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
    ├── intermediate/            # Phase 3
    └── marts/                   # Phase 3
```

## Current Coverage

- 7 staging models, one per raw source table
- 33 data tests: `not_null`, `unique`, `accepted_values`, `relationships`
  (referential integrity to `stg_patients`), and a custom `accepted_range`
  test for probability columns

Run `dbt build` — all 33 tests should pass (`PASS=33 ERROR=0`).
