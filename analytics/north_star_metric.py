"""North Star Metric: Weekly Adherent Patient Rate.

## Definition

**% of chronic-condition patients tracked that week whose 7-day medication
adherence rate is >= 80%.**

## Why this metric

CarePulse's value proposition is helping patients with chronic conditions
(diabetes, hypertension, COPD, ...) stick to their treatment plan. A patient
can be highly "engaged" with the app (logging in daily) without that
translating into better health behavior, and conversely a patient who
checks in once a week but consistently takes their medication is a success
story. Adherence is the behavior the product is ultimately trying to drive,
it's measurable weekly at the patient level, and it's the metric every other
team's work should ultimately move:

- **Onboarding** (`funnel_analysis.py`) gets patients to the point where
  adherence can even be tracked (first login -> medication logging).
- **Notifications / the medication-reminder experiment**
  (`ab_test_analysis.py`) is a direct lever on this metric.
- **Engagement** (DAU/WAU, tracked here as a supporting metric) is an input
  to adherence, not the outcome itself.

## Outputs (to ``analytics/output/``)
    - north_star_trend.png
    - north_star_report.md

Usage:
    python analytics/north_star_metric.py
    CAREPULSE_DB_PATH=/path/to/warehouse.duckdb python analytics/north_star_metric.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
ADHERENCE_THRESHOLD = 0.8


def load_weekly_adherence(con) -> pd.DataFrame:
    sql = f"""
    with patient_weeks as (
        select
            date_trunc('week', log_date) as week_start,
            patient_id,
            avg(case when medication_taken then 1.0 else 0 end) as weekly_adherence_rate,
            count(*) as days_tracked
        from main_marts.fct_medication_adherence
        group by 1, 2
    )
    select
        week_start,
        count(*)                                                          as patients_tracked,
        sum(case when weekly_adherence_rate >= {ADHERENCE_THRESHOLD} then 1 else 0 end) as patients_adherent,
        avg(weekly_adherence_rate)                                        as avg_adherence_rate
    from patient_weeks
    group by 1
    order by 1
    """
    df = common.query_df(con, sql)
    df["nsm"] = df["patients_adherent"] / df["patients_tracked"]
    return df


def load_weekly_active_patients(con) -> pd.DataFrame:
    return common.query_df(
        con,
        """
        select
            date_trunc('week', session_date) as week_start,
            count(distinct patient_id)        as wau
        from main_marts.fct_daily_engagement
        group by 1
        order by 1
        """,
    )


def plot_trend(nsm: pd.DataFrame, wau: pd.DataFrame, output_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    ax1.plot(nsm["week_start"], nsm["nsm"], marker="o", color="#16a34a")
    ax1.set_ylim(0, 1)
    ax1.set_title(f"North Star: % Patients with >= {ADHERENCE_THRESHOLD:.0%} Weekly Adherence")
    ax1.set_ylabel("Adherent patient rate")
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(axis="y", alpha=0.3)
    for x, y, n in zip(nsm["week_start"], nsm["nsm"], nsm["patients_tracked"]):
        ax1.annotate(f"n={n}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

    ax2.plot(wau["week_start"], wau["wau"], marker="o", color="#2563eb")
    ax2.set_title("Supporting Metric: Weekly Active Patients (WAU)")
    ax2.set_ylabel("Distinct patients with >=1 session")
    ax2.tick_params(axis="x", rotation=30)
    ax2.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=130)
    plt.close(fig)


def write_report(nsm: pd.DataFrame, wau: pd.DataFrame, output_path: Path) -> None:
    # Drop partial first week if it has far fewer patients than the rest (ramp-up artifact)
    full_weeks = nsm[nsm["patients_tracked"] >= nsm["patients_tracked"].max() * 0.5]
    latest = nsm.iloc[-1]
    first_full = full_weeks.iloc[0]

    lines = []
    lines.append("# North Star Metric: Weekly Adherent Patient Rate\n")
    lines.append(
        f"**Definition:** % of chronic-condition patients tracked that week "
        f"whose 7-day medication adherence rate is >= {ADHERENCE_THRESHOLD:.0%}.\n"
    )
    lines.append(
        "**Why this metric:** it's the closest measurable proxy for the "
        "product's core promise (helping chronic-condition patients stay on "
        "their treatment plan), it's actionable weekly at the patient level, "
        "and it sits downstream of onboarding, engagement, and the "
        "notification/reminder experiment -- i.e. every other workstream "
        "should show up here eventually.\n"
    )

    lines.append("## Weekly trend\n")
    lines.append("| Week of | Patients tracked | Patients adherent (>=80%) | NSM | Avg weekly adherence |")
    lines.append("|---|---|---|---|---|")
    for _, row in nsm.iterrows():
        lines.append(
            f"| {row['week_start'].date()} | {int(row['patients_tracked'])} | "
            f"{int(row['patients_adherent'])} | {row['nsm']:.0%} | {row['avg_adherence_rate']:.1%} |"
        )
    lines.append("")
    lines.append("![North Star trend](output/north_star_trend.png)\n")

    lines.append("## Supporting metric: Weekly Active Patients\n")
    lines.append("| Week of | WAU |")
    lines.append("|---|---|")
    for _, row in wau.iterrows():
        lines.append(f"| {row['week_start'].date()} | {int(row['wau'])} |")
    lines.append("")

    lines.append("## Reading the trend\n")
    lines.append(
        f"The NSM rises from {first_full['nsm']:.0%} (week of {first_full['week_start'].date()}) "
        f"to {latest['nsm']:.0%} (week of {latest['week_start'].date()}), and WAU rises "
        f"from {wau.iloc[1]['wau']} to {wau.iloc[-1]['wau']}. **Both of these trends are "
        "dominated by the synthetic cohort's staggered onboarding** -- patients sign up "
        "(and start being tracked) at different points over the ~4-week generation "
        "window, so later weeks simply have more patients in steady state, not "
        "necessarily *better* adherence per patient. The first week "
        f"({nsm.iloc[0]['week_start'].date()}, n={int(nsm.iloc[0]['patients_tracked'])}) is "
        "a partial-cohort artifact and excluded from the headline comparison above.\n"
    )
    lines.append(
        "In a production setting with a stable patient base, this chart would be read "
        "as a genuine retention/outcome signal. Here, the more useful reads are "
        "**cross-sectional**: the A/B test (`ab_test_report.md`) and the no-show / "
        "churn / adherence-risk models (`ml/`) decompose *why* a given patient lands "
        "above or below the 80% line, which is more actionable than the aggregate "
        "trend on this small, short-window sample.\n"
    )

    lines.append("## Caveats\n")
    lines.append(
        "- 25 patients tracked, over 4-5 weeks -- small N and short window for any "
        "time-series read.\n"
        "- Re-running against a larger, longer-running generated population "
        "(`src/data_generation/`) would let this metric be read as an actual "
        "trend rather than a cohort-ramp artifact.\n"
    )

    output_path.write_text("\n".join(lines))


def main() -> None:
    con = common.get_connection()
    nsm = load_weekly_adherence(con)
    wau = load_weekly_active_patients(con)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_trend(nsm, wau, OUTPUT_DIR / "north_star_trend.png")
    write_report(nsm, wau, OUTPUT_DIR / "north_star_report.md")

    print("=== North Star: Weekly Adherent Patient Rate ===")
    print(nsm[["week_start", "patients_tracked", "patients_adherent", "nsm"]].to_string(index=False))
    print("\n=== WAU ===")
    print(wau.to_string(index=False))
    print(f"\nReport written to {OUTPUT_DIR / 'north_star_report.md'}")


if __name__ == "__main__":
    main()
