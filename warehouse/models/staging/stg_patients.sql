with source as (

    select * from {{ source('raw', 'patient_profiles') }}

)

select
    patient_id,
    cast(birthdate as date)                            as birth_date,
    gender                                             as gender,
    race                                               as race,
    ethnicity                                          as ethnicity,
    state                                              as state,
    has_chronic_condition,
    engagement_segment,
    onboarding_offset_days,
    no_show_propensity,
    adherence_baseline,
    ab_test_group,
    date_diff('year', cast(birthdate as date), current_date) as age

from source
