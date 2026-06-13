select
    patient_id,
    notification_type,
    sent_at,
    opened,
    opened_at,
    ab_test_group

from {{ ref('stg_notifications') }}
