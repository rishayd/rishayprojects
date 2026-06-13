{#
    Wide, one-row-per-patient view of the onboarding funnel. Each step gets
    its own timestamp column (null if the patient never reached that step),
    plus `funnel_steps_completed` -- the highest step index reached, in the
    canonical funnel order:

        1. signup
        2. profile_complete
        3. consent_signed
        4. first_login
        5. first_appointment_booked
        6. first_appointment_attended
#}

with events as (

    select * from {{ ref('stg_onboarding_events') }}

),

pivoted as (

    select
        patient_id,
        max(case when step = 'signup'                       then event_timestamp end) as signup_at,
        max(case when step = 'profile_complete'             then event_timestamp end) as profile_complete_at,
        max(case when step = 'consent_signed'               then event_timestamp end) as consent_signed_at,
        max(case when step = 'first_login'                  then event_timestamp end) as first_login_at,
        max(case when step = 'first_appointment_booked'     then event_timestamp end) as first_appointment_booked_at,
        max(case when step = 'first_appointment_attended'   then event_timestamp end) as first_appointment_attended_at
    from events
    group by 1

),

patients as (

    select patient_id, engagement_segment, ab_test_group
    from {{ ref('dim_patients') }}

)

select
    p.patient_id,
    p.engagement_segment,
    p.ab_test_group,
    pv.signup_at,
    pv.profile_complete_at,
    pv.consent_signed_at,
    pv.first_login_at,
    pv.first_appointment_booked_at,
    pv.first_appointment_attended_at,
    case
        when pv.first_appointment_attended_at is not null then 6
        when pv.first_appointment_booked_at   is not null then 5
        when pv.first_login_at                is not null then 4
        when pv.consent_signed_at             is not null then 3
        when pv.profile_complete_at           is not null then 2
        when pv.signup_at                     is not null then 1
        else 0
    end as funnel_steps_completed

from patients p
left join pivoted pv
    on p.patient_id = pv.patient_id
