# Deployment

The dashboard (`dashboard/Home.py`) is a self-contained Streamlit app that
reads from a local DuckDB file. The main thing any deployment needs to solve
is: **where does that DuckDB file come from**, since `data/` (including
`*.duckdb`) is gitignored -- the warehouse is a build artifact, not something
checked into source control.

## Option A: Streamlit Community Cloud (recommended for a portfolio demo)

1. Push this repo to GitHub (the user does this manually -- no credentials
   are handled by this project's tooling).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at this repo, branch `main`, main file path
   `dashboard/Home.py`.
3. Streamlit Cloud installs from `requirements.txt` automatically.
4. **Build the warehouse at startup.** Community Cloud gives you an ephemeral
   filesystem, so the warehouse needs to be built when the app boots rather
   than shipped as a binary. Add a small bootstrap step -- either:
   - a `dashboard/bootstrap.py` (imported at the top of `Home.py`) that
     checks whether `data/warehouse.duckdb` exists and, if not, runs the
     mock-data + ingestion + dbt pipeline (the same three steps the CI
     workflow runs: `generate_mock_synthea.py` -> `simulate_app_events.py`
     -> `load_raw_to_duckdb.py` -> `dbt build`), or
   - a `packages.txt` is not needed (dbt-duckdb is pure Python), but the
     bootstrap step does need `dbt` on `PATH` and `DBT_PROFILES_DIR` pointed
     at `warehouse/`.

   This keeps the deployed demo reproducible and avoids committing a
   ~2 MB+ binary warehouse file to git. The tradeoff: cold starts are a few
   seconds slower (one-time dbt build), and the demo always shows the
   50-patient synthetic sample rather than a "real" larger dataset.

5. Set environment variables in the app's "Secrets" / settings if you want
   to point at a different population size or pre-generated dataset:
   - `CAREPULSE_DB_PATH` -- path to the DuckDB file (defaults to
     `data/warehouse.duckdb`)

## Option B: Run locally

This is the path described in `dashboard/README.md` and the fastest way to
see the real app:

```bash
pip install -r requirements.txt

# 1. Generate data (mock Synthea, for a quick run without Java)
python tests/fixtures/generate_mock_synthea.py --out data/synthea/csv --n 50
python src/data_generation/simulate_app_events.py --synthea-dir data/synthea/csv --sim-days 90

# 2. Load + transform
python src/ingestion/load_raw_to_duckdb.py --data-dir data --db-path data/warehouse.duckdb
cd warehouse && DBT_PROFILES_DIR=$(pwd) CAREPULSE_DB_PATH=$(pwd)/../data/warehouse.duckdb dbt build && cd ..

# 3. Run the dashboard
streamlit run dashboard/Home.py
```

For a larger, more realistic population, swap step 1 for the real Synthea
generator (`src/data_generation/run_synthea.sh 2000 Massachusetts`, requires
Java) -- everything downstream (ingestion, dbt, dashboard, ML, analytics) is
population-size agnostic and needs no code changes.

## Option C: Docker (not included, sketch only)

For a fully self-contained deployment (e.g. to Fly.io, Render, or a
container-based host), a `Dockerfile` would:

1. Start from `python:3.11-slim`.
2. `COPY . .` and `pip install -r requirements.txt`.
3. Run the same bootstrap pipeline as Option A (steps 1-2 above) as part of
   the image build, baking a small warehouse into the image -- or run it as
   an entrypoint step before `streamlit run` for a fresh dataset on every
   container start.
4. `CMD ["streamlit", "run", "dashboard/Home.py", "--server.port=8080", "--server.address=0.0.0.0"]`

This isn't included in the repo because it's redundant with Option A for a
portfolio demo, but it's the natural next step if this were a real product
(e.g. behind a reverse proxy with auth in front of patient data -- see
`docs/design_decisions.md` for the "this is a demo, not a HIPAA-compliant
system" caveat).

## Orchestration (Dagster) in deployment

`src/pipeline/dagster_assets.py` defines the ingestion -> staging -> marts
pipeline as Dagster assets. In this project it's used for local
materialization (`dagster dev` and `dagster asset materialize`); it isn't
part of the dashboard's runtime path. In a production setup, Dagster would
run on a schedule (e.g. nightly) against a real data source, materializing
the warehouse that the dashboard then reads -- decoupling "data refresh" from
"dashboard uptime."

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: unit tests, a
small generated dataset through the full ingestion + dbt pipeline (with all
86 dbt tests), and smoke tests for every ML model and analytics script. This
doubles as a living example of the "Option A bootstrap" pipeline above.
