#!/usr/bin/env python3
"""
Load Synthea + simulated app-event CSVs into a DuckDB database under a `raw` schema.

This is the entry point for the dbt project in warehouse/ -- dbt sources point at
the `raw.*` tables created here.

Usage:
    python load_raw_to_duckdb.py \\
        --data-dir data \\
        --db-path data/warehouse.duckdb
"""

import argparse
from pathlib import Path

import duckdb

# Maps raw table name -> path (relative to --data-dir) of the source CSV.
SOURCE_FILES = {
    "patient_profiles": "app_events/patient_profiles.csv",
    "onboarding_events": "app_events/onboarding_events.csv",
    "app_sessions": "app_events/app_sessions.csv",
    "notifications": "app_events/notifications.csv",
    "appointments": "app_events/appointments.csv",
    "medication_logs": "app_events/medication_logs.csv",
    "conditions": "synthea/csv/conditions.csv",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                        help="Base directory containing app_events/ and synthea/ subfolders")
    parser.add_argument("--db-path", type=Path, default=Path("data/warehouse.duckdb"),
                        help="Path to the DuckDB database file to create/update")
    args = parser.parse_args()

    args.db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(args.db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    print(f"Loading raw tables into {args.db_path} ...")
    for table_name, rel_path in SOURCE_FILES.items():
        csv_path = args.data_dir / rel_path
        if not csv_path.exists():
            print(f"  [skip] {csv_path} not found")
            continue

        con.execute(
            f"CREATE OR REPLACE TABLE raw.{table_name} AS "
            f"SELECT * FROM read_csv_auto(?, header=True)",
            [str(csv_path)],
        )
        count = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
        print(f"  [ok]   raw.{table_name:<20} {count:>8,} rows  <- {csv_path}")

    con.close()
    print("Done.")


if __name__ == "__main__":
    main()
