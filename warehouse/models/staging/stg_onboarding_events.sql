with source as (

    select * from {{ source('raw', 'onboarding_events') }}

)

select
    patient_id,
    step,
    cast(event_timestamp as timestamp) as event_timestamp

from source
