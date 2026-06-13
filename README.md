# CarePulse Analytics

An end-to-end analytics platform for a simulated digital health (remote patient monitoring / telehealth) product. Built to demonstrate Data Engineering, Data Science, Data Analytics, and Product Analytics skills on a realistic health tech dataset.

## Concept

A synthetic patient population (generated via [Synthea](https://github.com/synthetichealth/synthea)) is layered with simulated app-engagement events (logins, appointment bookings, reminders, medication logging, no-shows). The project covers the full stack: data generation → orchestrated ELT → dbt-modeled warehouse → ML risk models → dashboards → product experimentation analysis.

## Status

✅ All 7 build phases complete — see [docs/architecture.md](docs/architecture.md) for the full plan and phased roadmap, and [docs/design_decisions.md](docs/design_decisions.md) for the tradeoffs made along the way.

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| Warehouse | DuckDB |
| Transformation | dbt (dbt-duckdb) |
| Orchestration | Dagster |
| Dashboards | Streamlit |
| ML | scikit-learn / XGBoost |
| Experimentation stats | scipy / statsmodels |
| CI/CD | GitHub Actions |

## Repo Structure

```
carepulse-analytics/
├── docs/                 # architecture, data dictionary, metric definitions
├── src/
│   ├── data_generation/  # Synthea + app-event simulator
│   ├── ingestion/        # load raw data into DuckDB
│   └── pipeline/         # Dagster orchestration
├── warehouse/            # dbt project (staging -> intermediate -> marts)
├── ml/                   # no-show, churn, medication-adherence risk models
├── analytics/            # funnel, A/B test, and North Star metric analysis
├── dashboard/            # Streamlit app
└── tests/
```

## Roadmap

- [x] Phase 0 — Setup
- [x] Phase 1 — Data foundation (Synthea + app-event simulator)
- [x] Phase 2 — Ingestion & dbt staging models
- [x] Phase 3 — dbt marts & Dagster orchestration
- [x] Phase 4 — Streamlit dashboards
- [x] Phase 5 — ML risk models (no-show, churn, medication non-adherence)
- [x] Phase 6 — Product analytics (funnels, A/B testing, North Star metric)
- [x] Phase 7 — Polish, CI/CD, deploy

## Docs

- [Architecture & build plan](docs/architecture.md)
- [Data dictionary](docs/data_dictionary.md)
- [Metric definitions](docs/metrics_definitions.md)
- [Design decisions & tradeoffs](docs/design_decisions.md)
- [Deployment](docs/deployment.md)

## CI

Every push/PR to `main` generates a small synthetic dataset, runs it through
ingestion + the full dbt build (86 tests), and smoke-tests every ML model and
analytics script. See `.github/workflows/ci.yml`.

## License

MIT
