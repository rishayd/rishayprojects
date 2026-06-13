"""Clinical Ops: appointment no-show rates and medication adherence trends."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

import db

st.set_page_config(page_title="Clinical Ops | CarePulse", page_icon="\U0001F3E5", layout="wide")
st.title("\U0001F3E5 Clinical Operations")

# ---------------------------------------------------------------------------
# Appointments / no-shows
# ---------------------------------------------------------------------------

status_df = db.appointment_status_breakdown()
no_show_df = db.no_show_summary()

total_appts = status_df["appointments"].sum()
no_shows = status_df.loc[status_df["status"] == "no_show", "appointments"].sum()
overall_no_show_rate = no_shows / total_appts if total_appts else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Appointments", f"{total_appts:,}")
col2.metric("No-Shows", f"{no_shows:,}")
col3.metric("Overall No-Show Rate", f"{overall_no_show_rate:.1%}")

left, right = st.columns(2)

with left:
    st.subheader("Appointment Status Breakdown")
    fig = px.pie(status_df, names="status", values="appointments", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("No-Show Rate by Segment & Chronic Condition")
    fig = px.bar(
        no_show_df,
        x="engagement_segment",
        y="no_show_rate",
        color="has_chronic_condition",
        barmode="group",
        labels={
            "engagement_segment": "Engagement Segment",
            "no_show_rate": "No-Show Rate",
            "has_chronic_condition": "Chronic Condition",
        },
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    no_show_df.assign(no_show_rate=lambda d: (d["no_show_rate"] * 100).round(1)).rename(
        columns={"no_show_rate": "no_show_rate_%"}
    ),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Medication adherence
# ---------------------------------------------------------------------------

st.subheader("Medication Adherence Over Time")
adherence_ts = db.adherence_over_time()

fig = px.line(
    adherence_ts,
    x="log_date",
    y="adherence_rate",
    color="ab_test_group",
    labels={"log_date": "Date", "adherence_rate": "Adherence Rate", "ab_test_group": "A/B Cohort"},
)
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Adherence is tracked only for patients with a chronic condition. "
    "The `treatment` cohort receives an extra medication-reminder "
    "notification -- see the Product Analytics page for the A/B comparison."
)

st.subheader("Per-Patient Adherence Distribution")
adherence_summary = db.adherence_summary()
fig = px.histogram(
    adherence_summary,
    x="adherence_rate",
    color="ab_test_group",
    nbins=20,
    barmode="overlay",
    opacity=0.7,
    labels={"adherence_rate": "Adherence Rate", "ab_test_group": "A/B Cohort"},
)
fig.update_xaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)
