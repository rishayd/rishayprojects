{#
    No-show rate by engagement segment and chronic-condition status --
    surfaces which patient populations are most likely to miss appointments.
#}

with appointments as (

    select * from {{ ref('fct_appointments') }}

),

patients as (

    select patient_id, engagement_segment, has_chronic_condition
    from {{ ref('dim_patients') }}

)

select
    p.engagement_segment,
    p.has_chronic_condition,
    count(*)                                              as total_appointments,
    sum(case when a.is_no_show then 1 else 0 end)         as no_shows,
    avg(case when a.is_no_show then 1.0 else 0.0 end)     as no_show_rate

from appointments a
left join patients p
    on a.patient_id = p.patient_id
group by 1, 2
