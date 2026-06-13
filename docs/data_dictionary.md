# Data Dictionary

> To be filled in as Phase 1 (data generation) progresses.

## Synthea Tables (raw)

| Table | Description |
|---|---|
| `patients` | Demographics, address, birthdate |
| `encounters` | Visits/encounters with care providers |
| `conditions` | Diagnosed conditions per patient |
| `medications` | Prescribed medications |
| `observations` | Vitals and lab results |

## Simulated App Event Tables (raw)

| Table | Description |
|---|---|
| `app_sessions` | Login/session events per patient |
| `notifications` | Push notifications sent and opened |
| `appointments` | Scheduled appointments, status (attended/no-show/cancelled) |
| `medication_logs` | Patient-reported medication adherence events |
| `onboarding_events` | Funnel step events (signup, profile complete, first login, etc.) |

## Marts (to be defined in Phase 3)

| Model | Grain | Description |
|---|---|---|
| `dim_patients` | 1 row per patient | Demographics + condition flags |
| `fct_encounters` | 1 row per encounter | Clinical encounter facts |
| `fct_appointments` | 1 row per appointment | Appointment facts incl. no-show flag |
| `fct_app_events` | 1 row per event | App engagement event stream |
| `fct_medication_adherence` | 1 row per patient-day | Daily adherence status |
