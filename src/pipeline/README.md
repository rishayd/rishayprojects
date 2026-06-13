# Pipeline Orchestration (Dagster)

`dagster_assets.py` defines a 4-asset Dagster pipeline that runs the whole
project end-to-end:

```
synthea_patient_data --> app_event_data --> raw_tables --> dbt_marts
```

| Asset | What it does |
| --- | --- |
| `synthea_patient_data` | Checks that `data/synthea/csv/{patients,conditions}.csv` exist. Fails with a helpful message if Synthea hasn't been run yet. |
| `app_event_data` | Runs `simulate_app_events.py` to (re)generate the simulated app-engagement CSVs (onboarding, sessions, notifications, appointments, medication logs). Configurable `sim_days`, `seed`, `limit_patients`. |
| `raw_tables` | Runs `load_raw_to_duckdb.py` to load all CSVs into the `raw` schema of `data/warehouse.duckdb`. |
| `dbt_marts` | Runs `dbt build` (staging -> intermediate -> marts + all data tests) against that warehouse. |

A `carepulse_daily_pipeline` schedule materializes all four assets every day
at 06:00, simulating a daily refresh of engagement data and warehouse
rebuild.

## One-time setup

Synthea generation is *not* part of the asset graph (it downloads a ~100MB
jar and can take a few minutes), so run it once manually first:

```bash
./src/data_generation/run_synthea.sh        # default: 2000 patients, MA
```

## Running the pipeline

```bash
pip install -r requirements.txt

export DAGSTER_HOME=$(pwd)/.dagster_home     # optional, enables run history/UI
dagster dev -f src/pipeline/dagster_assets.py
```

Open the Dagster UI (default `http://localhost:3000`), go to **Assets**,
and click **Materialize all**. This will:

1. Verify the Synthea data is present.
2. Regenerate the simulated app-event CSVs.
3. Reload everything into `data/warehouse.duckdb` under the `raw` schema.
4. Run `dbt build` to refresh staging models, intermediate models, marts,
   and all 86 data tests.

To run headlessly instead of via the UI:

```bash
dagster job execute -f src/pipeline/dagster_assets.py -j carepulse_pipeline
```
