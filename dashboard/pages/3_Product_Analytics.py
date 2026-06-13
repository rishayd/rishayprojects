"""Product Analytics: onboarding funnel + medication-reminder A/B test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st
from scipy import stats

import db

st.set_page_config(page_title="Product Analytics | CarePulse", page_icon="\U0001F9EA", layout="wide")
st.title("\U0001F9EA Product Analytics & A/B Testing")

st.markdown(
    "**Experiment:** patients are randomly assigned to a `treatment` group "
    "(receives an extra `medication_reminder` push notification) or a "
    "`control` group. We look at whether the nudge moves medication "
    "adherence and onboarding-funnel conversion."
)

# ---------------------------------------------------------------------------
# Onboarding funnel conversion by cohort
# ---------------------------------------------------------------------------

st.subheader("Onboarding Funnel Conversion by Cohort")
funnel_df = db.funnel_conversion()

fig = px.bar(
    funnel_df,
    x="step_name",
    y="conversion_rate",
    color="ab_test_group",
    barmode="group",
    labels={"step_name": "Funnel Step", "conversion_rate": "Conversion Rate", "ab_test_group": "Cohort"},
)
fig.update_yaxes(tickformat=".0%")
fig.update_xaxes(categoryorder="array", categoryarray=funnel_df.sort_values("step_index")["step_name"].unique())
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Medication reminder A/B test: adherence rate
# ---------------------------------------------------------------------------

st.subheader("A/B Test: Medication Reminder Nudge -> Adherence Rate")

ab_df = db.adherence_by_ab_group()
col1, col2 = st.columns(2)
for col, (_, row) in zip([col1, col2], ab_df.iterrows()):
    col.metric(
        f"{row['ab_test_group'].title()} adherence rate",
        f"{row['avg_adherence_rate']:.1%}",
        help=f"{row['patients']} patients, {row['total_days_tracked']:,} patient-days tracked",
    )

fig = px.bar(
    ab_df,
    x="ab_test_group",
    y="avg_adherence_rate",
    color="ab_test_group",
    labels={"ab_test_group": "Cohort", "avg_adherence_rate": "Avg Adherence Rate"},
)
fig.update_yaxes(tickformat=".0%")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Two-proportion z-test on adherent-days vs. tracked-days
treatment_row = ab_df[ab_df["ab_test_group"] == "treatment"].iloc[0]
control_row = ab_df[ab_df["ab_test_group"] == "control"].iloc[0]

count = [treatment_row["total_days_adherent"], control_row["total_days_adherent"]]
nobs = [treatment_row["total_days_tracked"], control_row["total_days_tracked"]]

p1, p2 = count[0] / nobs[0], count[1] / nobs[1]
p_pool = sum(count) / sum(nobs)
se = (p_pool * (1 - p_pool) * (1 / nobs[0] + 1 / nobs[1])) ** 0.5
z = (p1 - p2) / se if se > 0 else 0.0
p_value = 2 * (1 - stats.norm.cdf(abs(z)))

st.markdown(
    f"**Lift:** treatment adherence is "
    f"**{(p1 - p2) * 100:+.1f} pp** vs. control "
    f"({p1:.1%} vs. {p2:.1%}). "
    f"Two-proportion z-test: z = {z:.2f}, p-value = {p_value:.4f}"
    + (" (statistically significant at α=0.05)." if p_value < 0.05 else " (not statistically significant at α=0.05).")
)
st.caption(
    "Note: this is a quick directional check on simulated data with a small "
    "sample size -- see `analytics/` (Phase 6) for the full experiment "
    "write-up, including power/sample-size discussion."
)

st.divider()

# ---------------------------------------------------------------------------
# Notification open rates
# ---------------------------------------------------------------------------

st.subheader("Notification Open Rates")
notif_df = db.notification_open_rates()

fig = px.bar(
    notif_df,
    x="notification_type",
    y="open_rate",
    color="ab_test_group",
    barmode="group",
    labels={"notification_type": "Notification Type", "open_rate": "Open Rate", "ab_test_group": "Cohort"},
)
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    notif_df.assign(open_rate=lambda d: (d["open_rate"] * 100).round(1)).rename(columns={"open_rate": "open_rate_%"}),
    use_container_width=True,
    hide_index=True,
)
