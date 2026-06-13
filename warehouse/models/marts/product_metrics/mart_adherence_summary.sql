{#
    Per-patient medication adherence summary, with the A/B test cohort
    (medication-reminder nudge: treatment vs. control) carried through so
    Phase 6 can compare adherence rates between groups.
#}

select
    patient_id,
    ab_test_group,
    count(*)                                                       as days_tracked,
    sum(case when medication_taken then 1 else 0 end)              as days_adherent,
    avg(case when medication_taken then 1.0 else 0.0 end)          as adherence_rate

from {{ ref('fct_medication_adherence') }}
group by 1, 2
