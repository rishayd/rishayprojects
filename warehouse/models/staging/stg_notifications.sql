with source as (

    select * from {{ source('raw', 'notifications') }}

)

select
    patient_id,
    notification_type,
    cast(sent_at as timestamp)    as sent_at,
    opened,
    cast(opened_at as timestamp)  as opened_at,
    ab_test_group

from source
