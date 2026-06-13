"""Onboarding funnel analysis.

Reads `main_marts.mart_funnel_conversion` and `main_marts.fct_onboarding_funnel`
to answer three questions a product analyst would ask about an onboarding
funnel:

1. Where do patients drop off overall, and does it differ by A/B cohort?
2. What's the *conditional* (step-over-step) conversion rate -- i.e. of the
   patients who reached step N, what fraction made it to step N+1? This is
   often more actionable than the cumulative rate because it isolates the
   specific transition that's leaking users.
3. How long does each transition typically take?

Outputs (to ``analytics/output/``):
    - funnel_conversion.png   (cumulative conversion by step & cohort)
    - funnel_dropoff.png      (step-over-step conditional conversion)
    - funnel_report.md        (narrative summary with numbers)

Usage:
    python analytics/funnel_analysis.py
    CAREPULSE_DB_PATH=/path/to/warehouse.duckdb python analytics/funnel_analysis.py
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

STEP_ORDER = [
    "signup",
    "profile_complete",
    "consent_signed",
    "first_login",
    "first_appointment_booked",
    "first_appointment_attended",
]

STEP_TIMESTAMP_COLS = [
    "signup_at",
    "profile_complete_at",
    "consent_signed_at",
    "first_login_at",
    "first_appointment_booked_at",
    "first_appointment_attended_at",
]


def load_data(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    conversion = common.query_df(
        con,
        "select step_index, step_name, ab_test_group, patients_reached, conversion_rate "
        "from main_marts.mart_funnel_conversion order by ab_test_group, step_index",
    )
    funnel = common.query_df(con, "select * from main_marts.fct_onboarding_funnel")
    return conversion, funnel


def overall_conversion(conversion: pd.DataFrame, total_patients: int) -> pd.DataFrame:
    """Cumulative conversion across both cohorts combined."""
    overall = (
        conversion.groupby(["step_index", "step_name"], as_index=False)["patients_reached"]
        .sum()
    )
    overall["conversion_rate"] = overall["patients_reached"] / total_patients
    return overall.sort_values("step_index")


def conditional_conversion(overall: pd.DataFrame) -> pd.DataFrame:
    """Step-over-step conversion: reached(N) / reached(N-1)."""
    df = overall.sort_values("step_index").copy()
    df["prev_reached"] = df["patients_reached"].shift(1)
    df["conditional_rate"] = df["patients_reached"] / df["prev_reached"]
    df.loc[df["step_index"] == 1, "conditional_rate"] = 1.0
    return df


def transition_times(funnel: pd.DataFrame) -> pd.DataFrame:
    """Median days between consecutive funnel steps (among patients who completed both)."""
    rows = []
    for i in range(len(STEP_TIMESTAMP_COLS) - 1):
        from_col, to_col = STEP_TIMESTAMP_COLS[i], STEP_TIMESTAMP_COLS[i + 1]
        both = funnel.dropna(subset=[from_col, to_col])
        if both.empty:
            median_days = None
        else:
            delta = (both[to_col] - both[from_col]).dt.total_seconds() / 86400
            median_days = delta.median()
        rows.append(
            {
                "from_step": STEP_ORDER[i],
                "to_step": STEP_ORDER[i + 1],
                "n_completed_both": len(both),
                "median_days": median_days,
            }
        )
    return pd.DataFrame(rows)


def plot_cumulative_conversion(conversion: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for cohort, group in conversion.groupby("ab_test_group"):
        group = group.sort_values("step_index")
        ax.plot(group["step_name"], group["conversion_rate"], marker="o", label=cohort)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Cumulative conversion rate")
    ax.set_title("Onboarding Funnel: Cumulative Conversion by Cohort")
    ax.tick_params(axis="x", rotation=30)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    ax.legend(title="A/B cohort")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=130)
    plt.close(fig)


def plot_conditional_conversion(cond: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(cond["step_name"], cond["conditional_rate"], color="#2563eb")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Step-over-step conversion rate")
    ax.set_title("Onboarding Funnel: Conditional Conversion (reached N / reached N-1)")
    ax.tick_params(axis="x", rotation=30)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    for i, rate in enumerate(cond["conditional_rate"]):
        ax.text(i, rate + 0.02, f"{rate:.0%}", ha="center", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=130)
    plt.close(fig)


def write_report(
    overall: pd.DataFrame,
    cond: pd.DataFrame,
    conversion: pd.DataFrame,
    times: pd.DataFrame,
    total_patients: int,
    output_path: Path,
) -> None:
    worst_step = cond[cond["step_index"] > 1].sort_values("conditional_rate").iloc[0]
    final_overall = overall.iloc[-1]
    treatment_final = conversion[(conversion["ab_test_group"] == "treatment") & (conversion["step_index"] == 6)]
    control_final = conversion[(conversion["ab_test_group"] == "control") & (conversion["step_index"] == 6)]

    lines = []
    lines.append("# Onboarding Funnel Analysis\n")
    lines.append(
        f"Cohort of {total_patients} patients across 6 onboarding steps "
        "(signup -> profile complete -> consent signed -> first login -> "
        "first appointment booked -> first appointment attended).\n"
    )

    lines.append("## Cumulative conversion (overall)\n")
    lines.append("| Step | Patients reached | Cumulative conversion |")
    lines.append("|---|---|---|")
    for _, row in overall.iterrows():
        lines.append(f"| {row['step_name']} | {int(row['patients_reached'])} | {row['conversion_rate']:.0%} |")
    lines.append("")
    lines.append(
        f"Only **{final_overall['conversion_rate']:.0%}** of patients who sign up go on to attend a "
        f"first appointment ({int(final_overall['patients_reached'])} of {total_patients}).\n"
    )

    lines.append("![Cumulative conversion](output/funnel_conversion.png)\n")

    lines.append("## Step-over-step (conditional) conversion\n")
    lines.append("| From -> To | Conditional conversion |")
    lines.append("|---|---|")
    for i in range(1, len(cond)):
        prev_row, row = cond.iloc[i - 1], cond.iloc[i]
        lines.append(f"| {prev_row['step_name']} -> {row['step_name']} | {row['conditional_rate']:.0%} |")
    lines.append("")
    lines.append(
        f"**Biggest leak:** `{worst_step['step_name']}` retains only "
        f"{worst_step['conditional_rate']:.0%} of patients who reached the prior step "
        "-- this is the highest-leverage step to investigate/improve.\n"
    )

    lines.append("![Conditional conversion](output/funnel_dropoff.png)\n")

    lines.append("## By A/B cohort\n")
    if not treatment_final.empty and not control_final.empty:
        t_rate = treatment_final["conversion_rate"].iloc[0]
        c_rate = control_final["conversion_rate"].iloc[0]
        lines.append(
            f"Final-step (first appointment attended) conversion is "
            f"**{t_rate:.0%}** for `treatment` vs **{c_rate:.0%}** for `control` "
            f"({(t_rate - c_rate) * 100:+.1f} pp). See `ab_test_report.md` for "
            "whether this difference is statistically meaningful -- with this "
            "sample size it likely is not on its own.\n"
        )

    lines.append("## Time-to-convert between steps\n")
    lines.append("| Transition | Patients completing both | Median days |")
    lines.append("|---|---|---|")
    for _, row in times.iterrows():
        median = f"{row['median_days']:.1f}" if row["median_days"] is not None else "n/a"
        lines.append(f"| {row['from_step']} -> {row['to_step']} | {int(row['n_completed_both'])} | {median} |")
    lines.append("")

    lines.append(
        "## Caveats\n\n"
        "This is a 50-patient synthetic cohort, so cohort splits in particular "
        "(roughly 25/25) are noisy -- treat percentage-point differences between "
        "`treatment` and `control` here as directional, not conclusive. The "
        "shape of the funnel (steady ~85-90% retention through `consent_signed`, "
        "then a sharper drop into `first_appointment_booked`/`attended`) is the "
        "more robust signal and would be the first thing to validate against a "
        "larger run.\n"
    )

    output_path.write_text("\n".join(lines))


def main() -> None:
    con = common.get_connection()
    conversion, funnel = load_data(con)
    total_patients = len(funnel)

    overall = overall_conversion(conversion, total_patients)
    cond = conditional_conversion(overall)
    times = transition_times(funnel)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_cumulative_conversion(conversion, OUTPUT_DIR / "funnel_conversion.png")
    plot_conditional_conversion(cond, OUTPUT_DIR / "funnel_dropoff.png")
    write_report(overall, cond, conversion, times, total_patients, OUTPUT_DIR / "funnel_report.md")

    print("=== Onboarding Funnel ===")
    print(overall.to_string(index=False))
    print("\nConditional conversion:")
    print(cond[["step_name", "conditional_rate"]].to_string(index=False))
    print(f"\nReport written to {OUTPUT_DIR / 'funnel_report.md'}")


if __name__ == "__main__":
    main()
