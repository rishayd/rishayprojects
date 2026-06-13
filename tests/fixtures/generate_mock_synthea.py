#!/usr/bin/env python3
"""
Generate a small mock Synthea-format dataset (patients.csv + conditions.csv)
for testing the app-event simulator without needing to run the real Synthea
jar (which requires Java and a ~100MB download).

Usage:
    python tests/fixtures/generate_mock_synthea.py --out data/synthea/csv --n 50
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CHRONIC_CONDITIONS = [
    "Diabetes",
    "Essential hypertension (disorder)",
    "Chronic obstructive pulmonary disease (disorder)",
    "Prediabetes",
]
OTHER_CONDITIONS = [
    "Viral sinusitis (disorder)",
    "Acute bronchitis (disorder)",
    "Seasonal allergic rhinitis",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/synthea/csv"))
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    n = args.n
    patient_ids = [f"patient-{i:04d}" for i in range(n)]

    patients = pd.DataFrame({
        "Id": patient_ids,
        "BIRTHDATE": pd.to_datetime("2026-06-13") - pd.to_timedelta(rng.integers(20 * 365, 80 * 365, size=n), unit="D"),
        "DEATHDATE": [None] * n,
        "GENDER": rng.choice(["M", "F"], size=n),
        "RACE": rng.choice(["white", "black", "asian", "hispanic", "other"], size=n),
        "ETHNICITY": rng.choice(["nonhispanic", "hispanic"], size=n),
        "STATE": "Massachusetts",
    })
    patients.to_csv(args.out / "patients.csv", index=False)

    # ~60% of patients get a chronic condition.
    rows = []
    for pid in patient_ids:
        if rng.random() < 0.6:
            rows.append({"PATIENT": pid, "DESCRIPTION": rng.choice(CHRONIC_CONDITIONS)})
        if rng.random() < 0.3:
            rows.append({"PATIENT": pid, "DESCRIPTION": rng.choice(OTHER_CONDITIONS)})

    conditions = pd.DataFrame(rows)
    conditions.to_csv(args.out / "conditions.csv", index=False)

    print(f"Wrote {len(patients)} patients and {len(conditions)} conditions to {args.out}/")


if __name__ == "__main__":
    main()
