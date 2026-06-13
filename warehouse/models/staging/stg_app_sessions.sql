with source as (

    select * from {{ source('raw', 'app_sessions') }}

)

select
    patient_id,
    cast(session_timestamp as timestamp) as session_timestamp,
    cast(session_timestamp as date)      as session_date,
    duration_seconds

from source
