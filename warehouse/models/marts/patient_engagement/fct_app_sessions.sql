select
    patient_id,
    session_timestamp,
    session_date,
    duration_seconds

from {{ ref('stg_app_sessions') }}
