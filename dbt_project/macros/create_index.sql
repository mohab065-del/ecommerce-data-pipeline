{% macro create_index(relation, name, columns) %}
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = '{{ name }}' AND object_id = OBJECT_ID('{{ relation }}')
)
CREATE NONCLUSTERED INDEX {{ name }} ON {{ relation }} ({{ columns | join(', ') }})
{% endmacro %}