"""
CarePulse Analytics -- Streamlit dashboard home page.

Run with:

    cd carepulse-analytics
    export CAREPULSE_DB_PATH=$(pwd)/data/warehouse.duckdb   # optional, this is the default
    streamlit run dashboard/Home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plotly.express as px
import streamlit as st

import db

st.set_page_config(
    page_title="CarePulse Analytics",
    page_icon="\U0001FA7A",
    layout="wide",
)

st.title("\U0001FA7A CarePulse Analytics")
st.caption(
    "A simulated digital health (remote patient monitoring / telehealth) "
    "platform -- patient engagement, clinical operations, and product "
    "analytics built on Synthea synthetic patient data."
)

# ---------------------------------------------------------------------------
# Top-line KPIs
# ---------------------------------------------------------------------------

total_patients = db.patient_count()
no_show_df = db.no_show_summary()
adherence_df = db.adherence_summary()
funnel_df = db.funnel_conversion()

overall_no_show_rate = (
    no_show_df["no_shows"].sum() / no_show_df["total_appointments"].sum()
    if no_show_df["total_appointments"].sum() > 0
    else 0
)
overall_adherence_rate = (
    adherence_df["days_adherent"].sum() / adherence_df["days_tracked"].sum()
    if adherence_df["days_tracked"].sum() > 0
    else 0
)
attended_step = funnel_df[funnel_df["step_name"] == "first_appointment_attended"]
overall_activation_rate = (
    (attended_step["patients_reached"].sum() / (total_patients * 2))
    if total_patients
    else 0
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patients", f"{total_patients:,}")
col2.metric("Appointment No-Show Rate", f"{overall_no_show_rate:.1%}")
col3.metric("Medication Adherence Rate", f"{overall_adherence_rate:.1%}")
col4.metric("Onboarding -> First Visit Attended", f"{overall_activation_rate:.1%}")

st.divider()

# ---------------------------------------------------------------------------
# Patient population breakdown
# ---------------------------------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("Patients by Engagement Segment")
    seg_df = db.patients_by_segment()
    seg_totals = seg_df.groupby("engagement_segment", as_index=False)["patients"].sum()
    fig = px.bar(
        seg_totals.sort_values("patients", ascending=False),
        x="engagement_segment",
        y="patients",
        color="engagement_segment",
        labels={"engagement_segment": "Engagement Segment", "patients": "Patients"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("A/B Test Cohort Split")
    ab_df = seg_df.groupby("ab_test_group", as_index=False)["patients"].sum()
    fig = px.pie(
        ab_df,
        names="ab_test_group",
        values="patients",
        hole=0.4,
        title="Medication reminder nudge experiment",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Patient Demographics")
demo_df = db.patient_demographics()
fig = px.bar(
    demo_df,
    x="gender",
    y="patients",
    color="has_chronic_condition",
    barmode="group",
    labels={"gender": "Gender", "patients": "Patients", "has_chronic_condition": "Chronic Condition"},
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown(
    "Use the sidebar to explore **Engagement**, **Clinical Ops**, and "
    "**Product Analytics** in more depth."
)
