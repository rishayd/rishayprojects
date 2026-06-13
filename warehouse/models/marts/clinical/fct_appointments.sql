select
    appointment_id,
    patient_id,
    scheduled_date,
    status,
    appointment_type,
    status = 'no_show'  as is_no_show,
    status = 'attended' as is_attended,
    status = 'cancelled' as is_cancelled

from {{ ref('stg_appointments') }}
