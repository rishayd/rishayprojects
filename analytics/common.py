"""Shared utilities for the CarePulse product-analytics scripts."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Read-only connection to the dbt-built warehouse.

    Defaults to ``data/warehouse.duckdb``, overridable with the
    ``CAREPULSE_DB_PATH`` env var (matches the convention used by the dbt
    project, Dagster pipeline, dashboard, and ml/ scripts).
    """
    path = db_path or os.environ.get("CAREPULSE_DB_PATH") or str(DEFAULT_DB_PATH)
    return duckdb.connect(path, read_only=True)


def query_df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetchdf()
