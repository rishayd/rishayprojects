"""Engagement: DAU/WAU/MAU, session activity by segment, onboarding funnel."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import db

st.set_page_config(page_title="Engagement | CarePulse", page_icon="\U0001F4C8", layout="wide")
st.title("\U0001F4C8 Patient Engagement")

# ---------------------------------------------------------------------------
# DAU / WAU / MAU
# ---------------------------------------------------------------------------

dau_df = db.daily_active_patients()
wau_df = db.weekly_active_patients()
mau_df = db.monthly_active_patients()

col1, col2, col3 = st.columns(3)
col1.metric("Avg Daily Active Patients", f"{dau_df['active_patients'].mean():.1f}")
col2.metric("Avg Weekly Active Patients", f"{wau_df['active_patients'].mean():.1f}")
col3.metric("Avg Monthly Active Patients", f"{mau_df['active_patients'].mean():.1f}")

st.subheader("Daily Active Patients (DAU)")
fig = px.line(dau_df, x="session_date", y="active_patients", labels={"session_date": "Date", "active_patients": "Active Patients"})
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Weekly Active Patients (WAU)")
    fig = px.bar(wau_df, x="week_start", y="active_patients", labels={"week_start": "Week", "active_patients": "Active Patients"})
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Monthly Active Patients (MAU)")
    fig = px.bar(mau_df, x="month_start", y="active_patients", labels={"month_start": "Month", "active_patients": "Active Patients"})
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Session duration by segment
# ---------------------------------------------------------------------------

st.subheader("Avg Session Duration by Engagement Segment")
seg_dur_df = db.avg_session_duration_by_segment()
fig = px.bar(
    seg_dur_df.sort_values("avg_duration_seconds", ascending=False),
    x="engagement_segment",
    y="avg_duration_seconds",
    color="engagement_segment",
    labels={"engagement_segment": "Segment", "avg_duration_seconds": "Avg Session Duration (s)"},
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Onboarding funnel
# ---------------------------------------------------------------------------

st.subheader("Onboarding Funnel")
funnel_df = db.funnel_conversion()

ab_groups = sorted(funnel_df["ab_test_group"].dropna().unique())
selected_groups = st.multiselect("A/B test cohort", options=ab_groups, default=list(ab_groups))

filtered = funnel_df[funnel_df["ab_test_group"].isin(selected_groups)]

fig = go.Figure()
for group in selected_groups:
    sub = filtered[filtered["ab_test_group"] == group].sort_values("step_index")
    fig.add_trace(
        go.Funnel(
            name=group,
            y=sub["step_name"],
            x=sub["patients_reached"],
            textinfo="value+percent initial",
        )
    )
fig.update_layout(title="Onboarding Steps Completed, by Cohort")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    filtered.assign(conversion_rate=lambda d: (d["conversion_rate"] * 100).round(1))
    .rename(columns={"conversion_rate": "conversion_rate_%"}),
    use_container_width=True,
    hide_index=True,
)
