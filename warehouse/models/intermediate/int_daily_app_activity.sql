with sessions as (

    select * from {{ ref('stg_app_sessions') }}

)

select
    patient_id,
    session_date,
    count(*)                   as session_count,
    sum(duration_seconds)      as total_duration_seconds,
    avg(duration_seconds)      as avg_duration_seconds

from sessions
group by 1, 2
