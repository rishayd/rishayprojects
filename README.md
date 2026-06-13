# CarePulse Analytics

An end-to-end analytics platform for a simulated digital health (remote patient monitoring / telehealth) product. Built to demonstrate Data Engineering, Data Science, Data Analytics, and Product Analytics skills on a realistic health tech dataset.

## Concept

A synthetic patient population (generated via [Synthea](https://github.com/synthetichealth/synthea)) is layered with simulated app-engagement events (logins, appointment bookings, reminders, medication logging, no-shows). The project covers the full stack: data generation → orchestrated ELT → dbt-modeled warehouse → ML risk models → dashboards → product experimentation analysis.

## Status

🚧 Work in progress — see [docs/architecture.md](docs/architecture.md) for the full plan and phased roadmap.

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
├── ml/                   # no-show, churn, readmission risk models
├── analytics/            # funnel & A/B test analysis
├── dashboard/            # Streamlit app
└── tests/
```

## Roadmap

- [x] Phase 0 — Setup
- [x] Phase 1 — Data foundation (Synthea + app-event simulator)
- [x] Phase 2 — Ingestion & dbt staging models
- [x] Phase 3 — dbt marts & Dagster orchestration
- [x] Phase 4 — Streamlit dashboards
- [ ] Phase 5 — ML risk models (no-show, churn, readmission)
- [ ] Phase 6 — Product analytics (funnels, A/B testing, North Star metric)
- [ ] Phase 7 — Polish, CI/CD, deploy

## License

MIT
