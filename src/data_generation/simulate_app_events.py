#!/usr/bin/env python3
"""
Simulate digital health app engagement data on top of a Synthea patient population.

Reads Synthea's patients.csv and conditions.csv and produces five event tables
that model how patients use a remote patient monitoring / telehealth app:

    - onboarding_events.csv     funnel steps (signup -> first appointment attended)
    - app_sessions.csv          login/session events
    - notifications.csv         reminders sent + opened
    - appointments.csv          scheduled appointments incl. no-show/cancelled
    - medication_logs.csv       daily medication adherence logs (chronic patients)

Patients are assigned to an "engagement segment" which drives login frequency,
adherence, notification open rates, and no-show propensity -- so downstream
metrics, models, and experiments have realistic signal and variance.

Usage:
    python simulate_app_events.py \\
        --synthea-dir data/synthea/csv \\
        --output-dir data/app_events \\
        --sim-days 180 \\
        --seed 42
"""

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHRONIC_KEYWORDS = [
    "diabetes",
    "hypertension",
    "chronic obstructive pulmonary disease",
    "prediabetes",
]

# Each segment defines the behavioral parameters used to generate events.
#   login_prob   : daily probability of an app session (day 0)
#   decay        : per-day reduction in login/adherence probability (models disengagement)
#   floor        : minimum probability after decay
#   notif_open   : probability a notification is opened
#   adherence    : daily probability of logging a medication dose as taken (day 0)
#   no_show      : probability a scheduled appointment becomes a no-show
ENGAGEMENT_SEGMENTS = {
    "highly_engaged":     dict(weight=0.25, login_prob=0.70, decay=0.0000, floor=0.55, notif_open=0.65, adherence=0.88, no_show=0.04),
    "moderately_engaged": dict(weight=0.40, login_prob=0.45, decay=0.0006, floor=0.25, notif_open=0.42, adherence=0.68, no_show=0.12),
    "disengaging":        dict(weight=0.25, login_prob=0.50, decay=0.0045, floor=0.04, notif_open=0.28, adherence=0.55, no_show=0.22),
    "low_engagement":     dict(weight=0.10, login_prob=0.15, decay=0.0010, floor=0.03, notif_open=0.12, adherence=0.30, no_show=0.38),
}

ONBOARDING_STEPS = [
    "signup",
    "profile_complete",
    "consent_signed",
    "first_login",
    "first_appointment_booked",
    "first_appointment_attended",
]

# Probability a patient in each segment completes each successive funnel step
# (conditional on having completed the previous step).
ONBOARDING_CONTINUE_PROB = {
    "highly_engaged":     [1.00, 0.97, 0.95, 0.95, 0.92, 0.90],
    "moderately_engaged": [1.00, 0.90, 0.85, 0.85, 0.75, 0.65],
    "disengaging":        [1.00, 0.85, 0.75, 0.70, 0.55, 0.40],
    "low_engagement":     [1.00, 0.70, 0.55, 0.50, 0.35, 0.25],
}

NOTIFICATION_TYPES = ["medication_reminder", "appointment_reminder", "weekly_check_in"]


# ---------------------------------------------------------------------------
# Data loading & patient profiles
# ---------------------------------------------------------------------------

def load_synthea_data(synthea_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    patients = pd.read_csv(synthea_dir / "patients.csv")
    conditions = pd.read_csv(synthea_dir / "conditions.csv")

    patients = patients.rename(columns={"Id": "patient_id"})
    conditions = conditions.rename(columns={"PATIENT": "patient_id"})

    # App users are living patients only.
    patients = patients[patients["DEATHDATE"].isna()].copy()
    patients = patients[["patient_id", "BIRTHDATE", "GENDER", "RACE", "ETHNICITY", "STATE"]]

    return patients.reset_index(drop=True), conditions


def assign_patient_profiles(patients: pd.DataFrame, conditions: pd.DataFrame, sim_days: int, rng: np.random.Generator) -> pd.DataFrame:
    df = patients.copy()
    n = len(df)

    # Chronic condition flag from Synthea conditions.
    pattern = "|".join(CHRONIC_KEYWORDS)
    chronic_ids = set(conditions.loc[conditions["DESCRIPTION"].str.lower().str.contains(pattern, na=False), "patient_id"])
    df["has_chronic_condition"] = df["patient_id"].isin(chronic_ids)

    # Assign engagement segment. Patients with a chronic condition are somewhat
    # more likely to be engaged (they have a stronger reason to use the app).
    segments = list(ENGAGEMENT_SEGMENTS.keys())
    base_weights = np.array([ENGAGEMENT_SEGMENTS[s]["weight"] for s in segments])

    chronic_weights = base_weights.copy()
    chronic_weights[0] *= 1.4   # highly_engaged
    chronic_weights[2] *= 0.7   # disengaging
    chronic_weights = chronic_weights / chronic_weights.sum()

    base_weights = base_weights / base_weights.sum()

    segment_choices = np.empty(n, dtype=object)
    chronic_mask = df["has_chronic_condition"].to_numpy()
    segment_choices[chronic_mask] = rng.choice(segments, size=chronic_mask.sum(), p=chronic_weights)
    segment_choices[~chronic_mask] = rng.choice(segments, size=(~chronic_mask).sum(), p=base_weights)
    df["engagement_segment"] = segment_choices

    # Onboarding offset: spread onboarding dates across the first half of the
    # simulation window so every patient has meaningful observation time.
    df["onboarding_offset_days"] = rng.integers(0, max(sim_days // 2, 1), size=n)

    # Per-patient propensities (add individual variance on top of segment defaults).
    df["no_show_propensity"] = np.clip(
        [ENGAGEMENT_SEGMENTS[s]["no_show"] for s in df["engagement_segment"]] + rng.normal(0, 0.05, size=n),
        0.01, 0.9,
    )
    df["adherence_baseline"] = np.clip(
        [ENGAGEMENT_SEGMENTS[s]["adherence"] for s in df["engagement_segment"]] + rng.normal(0, 0.05, size=n),
        0.02, 0.98,
    )

    # Randomly assign half of patients to a "reminder nudge" treatment group
    # for the Phase 6 A/B test (medication reminder nudges -> adherence).
    df["ab_test_group"] = rng.choice(["treatment", "control"], size=n, p=[0.5, 0.5])

    return df


# ---------------------------------------------------------------------------
# Event generators
# ---------------------------------------------------------------------------

def generate_onboarding_events(patients: pd.DataFrame, sim_end: pd.Timestamp, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, p in patients.iterrows():
        onboard_date = sim_end - pd.Timedelta(days=int(sim_end_offset_to_days(p, sim_end)))
        continue_probs = ONBOARDING_CONTINUE_PROB[p["engagement_segment"]]

        step_date = onboard_date
        for step, prob in zip(ONBOARDING_STEPS, continue_probs):
            if rng.random() > prob:
                break  # patient drops off the funnel here
            step_date = step_date + pd.Timedelta(hours=int(rng.integers(0, 48)))
            rows.append({
                "patient_id": p["patient_id"],
                "step": step,
                "event_timestamp": step_date,
            })

    return pd.DataFrame(rows)


def sim_end_offset_to_days(patient_row, sim_end) -> int:
    """Helper: convert a patient's onboarding offset into an actual date."""
    return patient_row["onboarding_offset_days"]


def generate_app_sessions(patients: pd.DataFrame, sim_end: pd.Timestamp, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, p in patients.iterrows():
        seg = ENGAGEMENT_SEGMENTS[p["engagement_segment"]]
        onboard_date = sim_end - pd.Timedelta(days=int(p["onboarding_offset_days"]))
        n_days = (sim_end - onboard_date).days
        if n_days <= 0:
            continue

        day_idx = np.arange(n_days)
        probs = np.clip(seg["login_prob"] - seg["decay"] * day_idx, seg["floor"], 1.0)
        logins = rng.random(n_days) < probs
        login_days = day_idx[logins]

        for d in login_days:
            session_date = onboard_date + pd.Timedelta(days=int(d))
            session_time = session_date + pd.Timedelta(
                hours=int(rng.integers(6, 23)), minutes=int(rng.integers(0, 60))
            )
            rows.append({
                "patient_id": p["patient_id"],
                "session_timestamp": session_time,
                "duration_seconds": int(rng.integers(30, 900)),
            })

    return pd.DataFrame(rows)


def generate_notifications(patients: pd.DataFrame, sim_end: pd.Timestamp, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, p in patients.iterrows():
        seg = ENGAGEMENT_SEGMENTS[p["engagement_segment"]]
        open_prob = seg["notif_open"]

        # A/B test: treatment group gets an extra medication reminder per week
        # and a modest bump to open probability (more salient reminder copy).
        is_treatment = p["ab_test_group"] == "treatment"
        if is_treatment:
            open_prob = min(open_prob + 0.08, 0.95)

        onboard_date = sim_end - pd.Timedelta(days=int(p["onboarding_offset_days"]))
        n_weeks = max((sim_end - onboard_date).days // 7, 0)

        for w in range(n_weeks):
            week_start = onboard_date + pd.Timedelta(weeks=w)
            notif_types = NOTIFICATION_TYPES + (["medication_reminder"] if is_treatment else [])
            for notif_type in notif_types:
                sent_at = week_start + pd.Timedelta(
                    days=int(rng.integers(0, 7)), hours=int(rng.integers(8, 20))
                )
                opened = rng.random() < open_prob
                rows.append({
                    "patient_id": p["patient_id"],
                    "notification_type": notif_type,
                    "sent_at": sent_at,
                    "opened": opened,
                    "opened_at": sent_at + pd.Timedelta(minutes=int(rng.integers(1, 240))) if opened else pd.NaT,
                    "ab_test_group": p["ab_test_group"],
                })

    return pd.DataFrame(rows)


def generate_appointments(patients: pd.DataFrame, sim_end: pd.Timestamp, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    appointment_id = 0
    for _, p in patients.iterrows():
        onboard_date = sim_end - pd.Timedelta(days=int(p["onboarding_offset_days"]))
        # Chronic patients are seen more frequently.
        interval_days = 30 if p["has_chronic_condition"] else 75

        scheduled_date = onboard_date + pd.Timedelta(days=int(rng.integers(3, 14)))
        while scheduled_date <= sim_end:
            r = rng.random()
            if r < 0.04:
                status = "cancelled"
            elif r < 0.04 + p["no_show_propensity"]:
                status = "no_show"
            else:
                status = "attended"

            rows.append({
                "appointment_id": appointment_id,
                "patient_id": p["patient_id"],
                "scheduled_date": scheduled_date,
                "status": status,
                "appointment_type": "follow_up" if p["has_chronic_condition"] else "check_up",
            })
            appointment_id += 1
            scheduled_date = scheduled_date + pd.Timedelta(days=int(interval_days + rng.integers(-5, 6)))

    return pd.DataFrame(rows)


def generate_medication_logs(patients: pd.DataFrame, sim_end: pd.Timestamp, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    chronic_patients = patients[patients["has_chronic_condition"]]

    for _, p in chronic_patients.iterrows():
        seg = ENGAGEMENT_SEGMENTS[p["engagement_segment"]]
        onboard_date = sim_end - pd.Timedelta(days=int(p["onboarding_offset_days"]))
        n_days = (sim_end - onboard_date).days
        if n_days <= 0:
            continue

        day_idx = np.arange(n_days)
        # Adherence decays alongside engagement for disengaging patients.
        probs = np.clip(p["adherence_baseline"] - seg["decay"] * day_idx, 0.02, 0.98)

        # A/B test: treatment group (extra medication reminders) gets a
        # modest adherence lift.
        if p["ab_test_group"] == "treatment":
            probs = np.clip(probs + 0.06, 0.02, 0.98)

        taken = rng.random(n_days) < probs

        for d, was_taken in zip(day_idx, taken):
            log_date = onboard_date + pd.Timedelta(days=int(d))
            rows.append({
                "patient_id": p["patient_id"],
                "log_date": log_date.date(),
                "medication_taken": bool(was_taken),
                "ab_test_group": p["ab_test_group"],
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthea-dir", type=Path, default=Path("data/synthea/csv"),
                        help="Directory containing Synthea's patients.csv and conditions.csv")
    parser.add_argument("--output-dir", type=Path, default=Path("data/app_events"),
                        help="Directory to write generated event CSVs")
    parser.add_argument("--sim-days", type=int, default=180,
                        help="Number of days of app activity to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--limit-patients", type=int, default=None,
                        help="Optional cap on number of patients (useful for quick test runs)")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    print(f"Loading Synthea data from {args.synthea_dir} ...")
    patients, conditions = load_synthea_data(args.synthea_dir)

    if args.limit_patients:
        patients = patients.head(args.limit_patients).reset_index(drop=True)

    print(f"Assigning engagement profiles to {len(patients):,} patients ...")
    patients = assign_patient_profiles(patients, conditions, args.sim_days, rng)

    sim_end = pd.Timestamp.today().normalize()

    print("Generating onboarding funnel events ...")
    onboarding = generate_onboarding_events(patients, sim_end, rng)

    print("Generating app sessions ...")
    sessions = generate_app_sessions(patients, sim_end, rng)

    print("Generating notifications ...")
    notifications = generate_notifications(patients, sim_end, rng)

    print("Generating appointments ...")
    appointments = generate_appointments(patients, sim_end, rng)

    print("Generating medication adherence logs ...")
    medication_logs = generate_medication_logs(patients, sim_end, rng)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    patients.to_csv(args.output_dir / "patient_profiles.csv", index=False)
    onboarding.to_csv(args.output_dir / "onboarding_events.csv", index=False)
    sessions.to_csv(args.output_dir / "app_sessions.csv", index=False)
    notifications.to_csv(args.output_dir / "notifications.csv", index=False)
    appointments.to_csv(args.output_dir / "appointments.csv", index=False)
    medication_logs.to_csv(args.output_dir / "medication_logs.csv", index=False)

    print("\nDone. Summary:")
    print(f"  patients              : {len(patients):,}")
    print(f"  onboarding_events     : {len(onboarding):,}")
    print(f"  app_sessions          : {len(sessions):,}")
    print(f"  notifications         : {len(notifications):,}")
    print(f"  appointments          : {len(appointments):,}")
    print(f"  medication_logs       : {len(medication_logs):,}")
    print(f"\nOutput written to {args.output_dir}/")


if __name__ == "__main__":
    main()
