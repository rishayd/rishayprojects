with source as (

    select * from {{ source('raw', 'medication_logs') }}

)

select
    patient_id,
    cast(log_date as date) as log_date,
    medication_taken,
    ab_test_group

from source
