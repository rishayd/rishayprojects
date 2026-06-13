"""
Shared DuckDB data-access layer for the CarePulse Streamlit dashboard.

All pages should import query functions from here rather than writing raw
SQL inline -- this keeps the dashboard decoupled from warehouse internals
and lets every page share the same cached connection.

The warehouse path defaults to ``../data/warehouse.duckdb`` (relative to
this file), matching the convention used by ``warehouse/profiles.yml``.
Override with the ``CAREPULSE_DB_PATH`` environment variable.
"""

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    db_path = Path(os.environ.get("CAREPULSE_DB_PATH", DEFAULT_DB_PATH))
    if not db_path.exists():
        st.error(
            f"Warehouse database not found at `{db_path}`.\n\n"
            "Run the ingestion + dbt pipeline first "
            "(see `warehouse/README.md` or `src/pipeline/README.md`)."
        )
        st.stop()
    return duckdb.connect(str(db_path), read_only=True)


def _query(sql: str, params: list | None = None) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql, params or []).df()


# ---------------------------------------------------------------------------
# dim_patients / overview
# ---------------------------------------------------------------------------


@st.cache_data
def patient_count() -> int:
    return int(_query("select count(*) as n from main_marts.dim_patients")["n"].iloc[0])


@st.cache_data
def patients_by_segment() -> pd.DataFrame:
    return _query(
        """
        select engagement_segment, ab_test_group, count(*) as patients
        from main_marts.dim_patients
        group by 1, 2
        order by 1, 2
        """
    )


@st.cache_data
def patient_demographics() -> pd.DataFrame:
    return _query(
        """
        select
            gender,
            has_chronic_condition,
            avg(age) as avg_age,
            count(*) as patients
        from main_marts.dim_patients
        group by 1, 2
        order by 1, 2
        """
    )


# ---------------------------------------------------------------------------
# Engagement
# ---------------------------------------------------------------------------


@st.cache_data
def daily_active_patients() -> pd.DataFrame:
    """One row per calendar day with the number of distinct active patients."""
    return _query(
        """
        select
            session_date,
            count(distinct patient_id) as active_patients,
            sum(session_count)         as total_sessions,
            sum(total_duration_seconds) as total_duration_seconds
        from main_marts.fct_daily_engagement
        group by 1
        order by 1
        """
    )


@st.cache_data
def weekly_active_patients() -> pd.DataFrame:
    """One row per ISO week with distinct active patients (WAU)."""
    return _query(
        """
        select
            date_trunc('week', session_date) as week_start,
            count(distinct patient_id)        as active_patients
        from main_marts.fct_daily_engagement
        group by 1
        order by 1
        """
    )


@st.cache_data
def monthly_active_patients() -> pd.DataFrame:
    """One row per calendar month with distinct active patients (MAU)."""
    return _query(
        """
        select
            date_trunc('month', session_date) as month_start,
            count(distinct patient_id)         as active_patients
        from main_marts.fct_daily_engagement
        group by 1
        order by 1
        """
    )


@st.cache_data
def avg_session_duration_by_segment() -> pd.DataFrame:
    return _query(
        """
        select
            engagement_segment,
            avg(avg_duration_seconds) as avg_duration_seconds,
            sum(session_count)        as total_sessions
        from main_marts.fct_daily_engagement
        group by 1
        order by 1
        """
    )


@st.cache_data
def funnel_conversion() -> pd.DataFrame:
    return _query(
        """
        select step_index, step_name, ab_test_group, patients_reached, conversion_rate
        from main_marts.mart_funnel_conversion
        order by ab_test_group, step_index
        """
    )


# ---------------------------------------------------------------------------
# Clinical ops
# ---------------------------------------------------------------------------


@st.cache_data
def no_show_summary() -> pd.DataFrame:
    return _query(
        """
        select engagement_segment, has_chronic_condition,
               total_appointments, no_shows, no_show_rate
        from main_marts.mart_appointment_no_show
        order by no_show_rate desc
        """
    )


@st.cache_data
def appointment_status_breakdown() -> pd.DataFrame:
    return _query(
        """
        select status, count(*) as appointments
        from main_marts.fct_appointments
        group by 1
        order by 1
        """
    )


@st.cache_data
def adherence_over_time() -> pd.DataFrame:
    return _query(
        """
        select
            log_date,
            ab_test_group,
            avg(case when medication_taken then 1.0 else 0.0 end) as adherence_rate,
            count(*) as logs
        from main_marts.fct_medication_adherence
        group by 1, 2
        order by 1, 2
        """
    )


@st.cache_data
def adherence_summary() -> pd.DataFrame:
    return _query("select * from main_marts.mart_adherence_summary")


# ---------------------------------------------------------------------------
# Product analytics / A-B testing
# ---------------------------------------------------------------------------


@st.cache_data
def notification_open_rates() -> pd.DataFrame:
    return _query(
        """
        select
            notification_type,
            ab_test_group,
            count(*) as sent,
            sum(case when opened then 1 else 0 end) as opened,
            avg(case when opened then 1.0 else 0.0 end) as open_rate
        from main_marts.fct_notifications
        group by 1, 2
        order by 1, 2
        """
    )


@st.cache_data
def adherence_by_ab_group() -> pd.DataFrame:
    return _query(
        """
        select
            ab_test_group,
            count(*)                       as patients,
            avg(adherence_rate)            as avg_adherence_rate,
            sum(days_adherent)             as total_days_adherent,
            sum(days_tracked)              as total_days_tracked
        from main_marts.mart_adherence_summary
        group by 1
        order by 1
        """
    )
