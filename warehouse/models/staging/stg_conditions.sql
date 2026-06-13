with source as (

    select * from {{ source('raw', 'conditions') }}

)

select
    patient                     as patient_id,
    description                 as condition_description,
    lower(description)          as condition_description_lower

from source
