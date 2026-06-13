{% test accepted_range(model, column_name, min_value=none, max_value=none) %}
{#
    Generic test: fails if any value in `column_name` falls outside
    [min_value, max_value] (inclusive). Either bound may be omitted.

    Written locally (instead of depending on dbt_utils) so this project
    has zero external package dependencies and `dbt deps` is unnecessary.
#}

select *
from {{ model }}
where
    {% if min_value is not none %}
    {{ column_name }} < {{ min_value }}
    {% if max_value is not none %} or {% endif %}
    {% endif %}
    {% if max_value is not none %}
    {{ column_name }} > {{ max_value }}
    {% endif %}

{% endtest %}
