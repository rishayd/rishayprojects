select
    patient_id,
    log_date,
    medication_taken,
    ab_test_group

from {{ ref('stg_medication_logs') }}
