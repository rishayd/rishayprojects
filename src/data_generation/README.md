# Data Generation (Phase 1)

## 1. Generate a synthetic patient population (Synthea)

```bash
./run_synthea.sh [population_size] [state]
# e.g. ./run_synthea.sh 2000 Massachusetts
```

Downloads Synthea (Java jar, first run only) and writes patient/encounter/condition
CSVs to `data/synthea/csv/`.

## 2. Generate app engagement events

```bash
python simulate_app_events.py \
    --synthea-dir data/synthea/csv \
    --output-dir data/app_events \
    --sim-days 180 \
    --seed 42
```

Produces, in `data/app_events/`:

- `patient_profiles.csv` — engagement segment, chronic condition flag, A/B test group
- `onboarding_events.csv` — signup -> first appointment attended funnel steps
- `app_sessions.csv` — login/session events
- `notifications.csv` — reminders sent + opened
- `appointments.csv` — scheduled appointments (attended / no_show / cancelled)
- `medication_logs.csv` — daily medication adherence (chronic patients only)

Each patient is assigned an **engagement segment** (highly_engaged, moderately_engaged,
disengaging, low_engagement) that drives login frequency, adherence, notification
open rates, and no-show propensity — and an **A/B test group** (treatment receives
extra medication reminders with a modest adherence lift) used in the Phase 6
experiment analysis.

## Testing without Synthea

`tests/fixtures/generate_mock_synthea.py` creates a small mock `patients.csv` /
`conditions.csv` so the simulator (and CI) can run without the Java/Synthea
dependency:

```bash
python tests/fixtures/generate_mock_synthea.py --out data/synthea/csv --n 50
python simulate_app_events.py --synthea-dir data/synthea/csv --sim-days 90
```
