with patients as (

    select * from {{ ref('stg_patients') }}

),

conditions as (

    select * from {{ ref('int_patient_conditions') }}

)

select
    p.patient_id,
    p.birth_date,
    p.age,
    p.gender,
    p.race,
    p.ethnicity,
    p.state,
    p.has_chronic_condition,
    p.engagement_segment,
    p.onboarding_offset_days,
    p.no_show_propensity,
    p.adherence_baseline,
    p.ab_test_group,
    coalesce(c.condition_count, 0) as condition_count,
    c.condition_list

from patients p
left join conditions c
    on p.patient_id = c.patient_id
