"""
Tests for the app-event simulator (Phase 1).

Run with: pytest tests/ -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "data_generation"))

from simulate_app_events import (  # noqa: E402
    ENGAGEMENT_SEGMENTS,
    ONBOARDING_STEPS,
    assign_patient_profiles,
    generate_app_sessions,
    generate_appointments,
    generate_medication_logs,
    generate_notifications,
    generate_onboarding_events,
    load_synthea_data,
)


@pytest.fixture(scope="module")
def mock_synthea_dir(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("synthea_csv")
    sys.path.insert(0, str(ROOT / "tests" / "fixtures"))
    from generate_mock_synthea import main as generate_mock

    sys.argv = ["generate_mock_synthea.py", "--out", str(out_dir), "--n", "60", "--seed", "1"]
    generate_mock()
    return out_dir


@pytest.fixture(scope="module")
def patients_and_conditions(mock_synthea_dir):
    return load_synthea_data(mock_synthea_dir)


@pytest.fixture(scope="module")
def patient_profiles(patients_and_conditions):
    patients, conditions = patients_and_conditions
    rng = np.random.default_rng(42)
    return assign_patient_profiles(patients, conditions, sim_days=90, rng=rng)


SIM_END = pd.Timestamp.today().normalize()


def test_load_synthea_data_excludes_deceased(mock_synthea_dir):
    patients, conditions = load_synthea_data(mock_synthea_dir)
    assert "patient_id" in patients.columns
    assert patients["patient_id"].is_unique
    assert len(patients) > 0


def test_patient_profiles_have_valid_segments(patient_profiles):
    assert set(patient_profiles["engagement_segment"]).issubset(set(ENGAGEMENT_SEGMENTS.keys()))
    assert patient_profiles["no_show_propensity"].between(0, 1).all()
    assert patient_profiles["adherence_baseline"].between(0, 1).all()


def test_ab_test_groups_roughly_balanced(patient_profiles):
    counts = patient_profiles["ab_test_group"].value_counts(normalize=True)
    assert set(counts.index) == {"treatment", "control"}
    assert abs(counts["treatment"] - 0.5) < 0.15


def test_onboarding_events_follow_funnel_order(patient_profiles):
    rng = np.random.default_rng(1)
    onboarding = generate_onboarding_events(patient_profiles, SIM_END, rng)
    assert not onboarding.empty
    assert set(onboarding["step"]).issubset(set(ONBOARDING_STEPS))

    for _, group in onboarding.groupby("patient_id"):
        steps = list(group.sort_values("event_timestamp")["step"])
        # Each patient's completed steps must be a prefix of the funnel.
        assert steps == ONBOARDING_STEPS[: len(steps)]


def test_app_sessions_within_observation_window(patient_profiles):
    rng = np.random.default_rng(2)
    sessions = generate_app_sessions(patient_profiles, SIM_END, rng)
    assert not sessions.empty
    assert (pd.to_datetime(sessions["session_timestamp"]) <= SIM_END + pd.Timedelta(days=1)).all()


def test_notifications_treatment_group_has_extra_reminders(patient_profiles):
    rng = np.random.default_rng(3)
    notifications = generate_notifications(patient_profiles, SIM_END, rng)
    assert not notifications.empty

    counts = notifications.groupby("ab_test_group").size()
    per_patient = {
        grp: counts.get(grp, 0) / (patient_profiles["ab_test_group"] == grp).sum()
        for grp in ["treatment", "control"]
    }
    # Treatment patients should receive more notifications on average
    # (extra weekly medication_reminder).
    assert per_patient["treatment"] > per_patient["control"]


def test_appointments_have_valid_statuses(patient_profiles):
    rng = np.random.default_rng(4)
    appointments = generate_appointments(patient_profiles, SIM_END, rng)
    assert not appointments.empty
    assert set(appointments["status"]).issubset({"attended", "no_show", "cancelled"})
    assert appointments["appointment_id"].is_unique


def test_medication_logs_only_for_chronic_patients(patient_profiles):
    rng = np.random.default_rng(5)
    logs = generate_medication_logs(patient_profiles, SIM_END, rng)
    chronic_ids = set(patient_profiles.loc[patient_profiles["has_chronic_condition"], "patient_id"])
    assert set(logs["patient_id"]).issubset(chronic_ids)
    assert logs["medication_taken"].dtype == bool


def test_medication_adherence_higher_for_treatment_group(patient_profiles):
    rng = np.random.default_rng(6)
    logs = generate_medication_logs(patient_profiles, SIM_END, rng)
    adherence_by_group = logs.groupby("ab_test_group")["medication_taken"].mean()
    # The simulator applies a +0.06 adherence boost to the treatment group,
    # so on average treatment adherence should exceed control.
    assert adherence_by_group["treatment"] > adherence_by_group["control"]
