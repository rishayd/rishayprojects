# CarePulse Dashboard (Streamlit)

A 4-page Streamlit app over the dbt marts in `data/warehouse.duckdb`.

## Pages

- **Home** -- top-line KPIs (patient count, no-show rate, adherence rate,
  activation rate), patient population by engagement segment and A/B
  cohort, demographics.
- **Engagement** -- DAU/WAU/MAU trends, average session duration by
  engagement segment, onboarding funnel (overall and by A/B cohort).
- **Clinical Ops** -- appointment status breakdown, no-show rate by
  segment and chronic-condition status, medication adherence trends over
  time and per-patient distribution.
- **Product Analytics** -- onboarding funnel conversion by A/B cohort, the
  medication-reminder A/B test (adherence rate lift with a two-proportion
  z-test), and notification open rates by type and cohort.

## Running it

```bash
pip install -r requirements.txt

# Make sure the warehouse has been built (see warehouse/README.md or
# src/pipeline/README.md for the full pipeline)
export CAREPULSE_DB_PATH=$(pwd)/data/warehouse.duckdb   # optional, this is the default

streamlit run dashboard/Home.py
```

All queries live in `dashboard/db.py` and read directly from the
`main_marts.*` tables (read-only DuckDB connection), so the dashboard
always reflects the latest `dbt build`.
