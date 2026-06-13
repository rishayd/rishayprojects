with activity as (

    select * from {{ ref('int_daily_app_activity') }}

),

patients as (

    select
        patient_id,
        engagement_segment,
        ab_test_group,
        has_chronic_condition
    from {{ ref('dim_patients') }}

)

select
    a.patient_id,
    a.session_date,
    a.session_count,
    a.total_duration_seconds,
    a.avg_duration_seconds,
    p.engagement_segment,
    p.ab_test_group,
    p.has_chronic_condition

from activity a
left join patients p
    on a.patient_id = p.patient_id
