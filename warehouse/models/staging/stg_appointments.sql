with source as (

    select * from {{ source('raw', 'appointments') }}

)

select
    appointment_id,
    patient_id,
    cast(scheduled_date as date) as scheduled_date,
    status,
    appointment_type

from source
