{#
    Onboarding funnel conversion counts and rates per step, overall and by
    A/B test cohort. Each row is one funnel step; `patients_reached` counts
    patients whose `funnel_steps_completed` is >= that step's index, and
    `conversion_rate` is relative to the total patient population.
#}

with funnel as (

    select * from {{ ref('fct_onboarding_funnel') }}

),

totals as (

    select count(*) as total_patients
    from funnel

),

steps as (

    select 1 as step_index, 'signup'                     as step_name
    union all select 2, 'profile_complete'
    union all select 3, 'consent_signed'
    union all select 4, 'first_login'
    union all select 5, 'first_appointment_booked'
    union all select 6, 'first_appointment_attended'

)

select
    s.step_index,
    s.step_name,
    f.ab_test_group,
    count(*) as patients_reached,
    cast(count(*) as double) / max(t.total_patients) as conversion_rate

from steps s
cross join totals t
left join funnel f
    on f.funnel_steps_completed >= s.step_index
group by 1, 2, 3
order by 3, 1
