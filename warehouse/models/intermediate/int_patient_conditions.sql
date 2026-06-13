with conditions as (

    select * from {{ ref('stg_conditions') }}

)

select
    patient_id,
    count(*)                                         as condition_count,
    string_agg(distinct condition_description, ', ') as condition_list

from conditions
group by 1
