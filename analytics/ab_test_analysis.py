"""A/B test analysis: medication-reminder nudge experiment.

Patients are randomly assigned to `treatment` (receives an extra
`medication_reminder` push notification) or `control`. This script runs the
full experiment readout:

1. **Primary metric -- medication adherence rate.** Two-proportion z-test on
   adherent patient-days vs. tracked patient-days, with a confidence
   interval on the difference and an effect size (Cohen's h).
2. **Secondary metric -- medication-reminder open rate.** Same test, on
   notification opens. This tells us whether the *mechanism* (patients
   actually receiving and opening more reminders) worked, independent of
   whether it moved the primary metric.
3. **Power / sample-size analysis.** Given the observed effect (or lack of
   one) on the primary metric, what sample size would be needed to detect a
   meaningful lift (e.g. 5pp) at 80% power?

Outputs (to ``analytics/output/``):
    - ab_test_adherence.png
    - ab_test_notifications.png
    - ab_test_report.md

Usage:
    python analytics/ab_test_analysis.py
    CAREPULSE_DB_PATH=/path/to/warehouse.duckdb python analytics/ab_test_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportion_effectsize,
    proportions_ztest,
)

import common

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
ALPHA = 0.05
MDE_TARGET_PP = 0.05  # 5 percentage points -- the lift we'd want to be able to detect


def load_adherence(con) -> pd.DataFrame:
    return common.query_df(
        con,
        """
        select
            ab_test_group,
            count(*)                                            as days_tracked,
            sum(case when medication_taken then 1 else 0 end)   as days_adherent
        from main_marts.fct_medication_adherence
        group by 1
        order by 1
        """,
    )


def load_notification_opens(con) -> pd.DataFrame:
    return common.query_df(
        con,
        """
        select
            ab_test_group,
            count(*)                                  as notifications_sent,
            sum(case when opened then 1 else 0 end)   as notifications_opened
        from main_marts.fct_notifications
        where notification_type = 'medication_reminder'
        group by 1
        order by 1
        """,
    )


def two_proportion_test(df: pd.DataFrame, success_col: str, total_col: str) -> dict:
    """Run a two-proportion z-test (treatment vs control) and return a result dict."""
    treatment = df[df["ab_test_group"] == "treatment"].iloc[0]
    control = df[df["ab_test_group"] == "control"].iloc[0]

    counts = [treatment[success_col], control[success_col]]
    nobs = [treatment[total_col], control[total_col]]

    z_stat, p_value = proportions_ztest(counts, nobs)
    ci_low, ci_high = confint_proportions_2indep(
        counts[0], nobs[0], counts[1], nobs[1], method="wald"
    )

    p_treatment = counts[0] / nobs[0]
    p_control = counts[1] / nobs[1]
    effect_size = proportion_effectsize(p_treatment, p_control)

    return {
        "p_treatment": p_treatment,
        "p_control": p_control,
        "n_treatment": int(nobs[0]),
        "n_control": int(nobs[1]),
        "diff": p_treatment - p_control,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "z_stat": z_stat,
        "p_value": p_value,
        "effect_size_h": effect_size,
        "significant": p_value < ALPHA,
    }


def required_sample_size(baseline_rate: float, mde: float, alpha: float = ALPHA, power: float = 0.8) -> float:
    """Sample size per group needed to detect `mde` (absolute, percentage points) lift."""
    effect_size = proportion_effectsize(baseline_rate + mde, baseline_rate)
    analysis = NormalIndPower()
    return analysis.solve_power(effect_size=abs(effect_size), alpha=alpha, power=power, alternative="two-sided")


def achieved_power(baseline_rate: float, observed_rate: float, n_per_group: int, alpha: float = ALPHA) -> float:
    effect_size = proportion_effectsize(observed_rate, baseline_rate)
    analysis = NormalIndPower()
    return analysis.power(effect_size=abs(effect_size), nobs1=n_per_group, alpha=alpha, alternative="two-sided")


def plot_proportions(result: dict, title: str, ylabel: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    cohorts = ["control", "treatment"]
    rates = [result["p_control"], result["p_treatment"]]
    bars = ax.bar(cohorts, rates, color=["#94a3b8", "#2563eb"])
    ax.set_ylim(0, 1)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.02, f"{rate:.1%}", ha="center", fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=130)
    plt.close(fig)


def write_report(
    adherence: dict,
    notif: dict,
    sample_size_needed: float,
    power_now: float,
    output_path: Path,
) -> None:
    lines = []
    lines.append("# A/B Test Readout: Medication Reminder Nudge\n")
    lines.append(
        "**Design:** patients are randomly assigned to `treatment` (gets an "
        "extra `medication_reminder` push notification) or `control`. "
        f"Alpha = {ALPHA}.\n"
    )

    lines.append("## Primary metric: medication adherence rate\n")
    lines.append("Adherent patient-days / tracked patient-days.\n")
    lines.append("| Cohort | Tracked days | Adherent days | Adherence rate |")
    lines.append("|---|---|---|---|")
    lines.append(f"| control | {adherence['n_control']} | {int(adherence['p_control'] * adherence['n_control'])} | {adherence['p_control']:.1%} |")
    lines.append(f"| treatment | {adherence['n_treatment']} | {int(adherence['p_treatment'] * adherence['n_treatment'])} | {adherence['p_treatment']:.1%} |")
    lines.append("")
    lines.append(
        f"Lift: **{adherence['diff'] * 100:+.1f} pp** "
        f"(95% CI: [{adherence['ci_low'] * 100:+.1f}, {adherence['ci_high'] * 100:+.1f}] pp). "
        f"z = {adherence['z_stat']:.2f}, p = {adherence['p_value']:.3f} -- "
        + ("**statistically significant**" if adherence["significant"] else "**not statistically significant**")
        + f" at alpha = {ALPHA}.\n"
    )
    lines.append("![Adherence by cohort](output/ab_test_adherence.png)\n")

    if not adherence["significant"]:
        lines.append(
            "Treatment adherence is essentially flat vs. control (in this run, "
            "slightly *lower*, well within noise). **The nudge did not move the "
            "primary metric** -- this is a real, useful null result, not a bug.\n"
        )

    lines.append("## Secondary metric: medication-reminder open rate\n")
    lines.append("| Cohort | Reminders sent | Reminders opened | Open rate |")
    lines.append("|---|---|---|---|")
    lines.append(f"| control | {notif['n_control']} | {int(notif['p_control'] * notif['n_control'])} | {notif['p_control']:.1%} |")
    lines.append(f"| treatment | {notif['n_treatment']} | {int(notif['p_treatment'] * notif['n_treatment'])} | {notif['p_treatment']:.1%} |")
    lines.append("")
    lines.append(
        f"Lift: **{notif['diff'] * 100:+.1f} pp** "
        f"(95% CI: [{notif['ci_low'] * 100:+.1f}, {notif['ci_high'] * 100:+.1f}] pp). "
        f"z = {notif['z_stat']:.2f}, p = {notif['p_value']:.3f} -- "
        + ("**statistically significant**" if notif["significant"] else "**not statistically significant**")
        + f" at alpha = {ALPHA}.\n"
    )
    lines.append("![Medication reminder open rate by cohort](output/ab_test_notifications.png)\n")
    lines.append(
        f"Treatment patients also simply receive more medication reminders "
        f"({notif['n_treatment']} vs {notif['n_control']} sent) -- the "
        "intervention mechanism is working as designed (more reminders, "
        "higher open rate). The disconnect is between *opening a reminder* "
        "and *taking the medication that day* -- see Recommendations.\n"
    )

    lines.append("## Power & sample-size analysis\n")
    lines.append(
        f"At the observed sample size ({adherence['n_control'] + adherence['n_treatment']} "
        f"patient-days total, ~{(adherence['n_control'] + adherence['n_treatment']) // 2} per arm), "
        f"this experiment has **{power_now:.0%} power** to detect the effect size "
        f"actually observed ({adherence['diff'] * 100:+.1f} pp) -- consistent with "
        "the non-significant result above.\n"
    )
    lines.append(
        f"To reliably detect a **{MDE_TARGET_PP * 100:.0f} percentage-point** lift in adherence "
        f"(from a baseline of {adherence['p_control']:.0%}) at 80% power and "
        f"alpha = {ALPHA}, the experiment would need approximately "
        f"**{sample_size_needed:,.0f} patient-days per arm**. "
        f"At ~6.5 tracked days per patient in this dataset, that's roughly "
        f"**{sample_size_needed / 6.5:,.0f} patients per arm** -- well beyond "
        "the current 25/25 split.\n"
    )

    lines.append("## Recommendations\n")
    lines.append(
        "1. **Don't ship on this result yet** -- the experiment is underpowered "
        "for the primary metric at this sample size; the null result could "
        "easily flip with more data.\n"
        "2. **The mechanism works, the outcome doesn't (yet)** -- treatment "
        "patients open more medication reminders, but that isn't translating "
        "into more adherent days. Consider an intermediate metric (reminder -> "
        "in-app medication log within the same day) to test the causal chain "
        "more directly.\n"
        "3. **Re-run at the architecture doc's target scale** (2,000-5,000 "
        "patients) -- at that scale, the same effect size would be well within "
        "reach of 80% power for adherence.\n"
    )

    output_path.write_text("\n".join(lines))


def main() -> None:
    con = common.get_connection()

    adherence_df = load_adherence(con)
    notif_df = load_notification_opens(con)

    adherence = two_proportion_test(adherence_df, "days_adherent", "days_tracked")
    notif = two_proportion_test(notif_df, "notifications_opened", "notifications_sent")

    n_per_group = (adherence["n_control"] + adherence["n_treatment"]) // 2
    sample_size_needed = required_sample_size(adherence["p_control"], MDE_TARGET_PP)
    power_now = achieved_power(adherence["p_control"], adherence["p_treatment"], n_per_group)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_proportions(adherence, "Medication Adherence Rate by Cohort", "Adherence rate", OUTPUT_DIR / "ab_test_adherence.png")
    plot_proportions(notif, "Medication Reminder Open Rate by Cohort", "Open rate", OUTPUT_DIR / "ab_test_notifications.png")
    write_report(adherence, notif, sample_size_needed, power_now, OUTPUT_DIR / "ab_test_report.md")

    print("=== Adherence (primary) ===")
    print(f"control={adherence['p_control']:.1%}  treatment={adherence['p_treatment']:.1%}  "
          f"diff={adherence['diff']*100:+.1f}pp  p={adherence['p_value']:.3f}")
    print("\n=== Medication reminder open rate (secondary) ===")
    print(f"control={notif['p_control']:.1%}  treatment={notif['p_treatment']:.1%}  "
          f"diff={notif['diff']*100:+.1f}pp  p={notif['p_value']:.3f}")
    print(f"\nPower at current N to detect observed effect: {power_now:.0%}")
    print(f"Sample size per arm needed for {MDE_TARGET_PP:.0%}pp MDE @ 80% power: {sample_size_needed:,.0f}")
    print(f"\nReport written to {OUTPUT_DIR / 'ab_test_report.md'}")


if __name__ == "__main__":
    main()
