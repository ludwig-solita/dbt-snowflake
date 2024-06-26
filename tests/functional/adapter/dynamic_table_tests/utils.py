from typing import Optional

import agate
from dbt.tests.util import get_connection

from dbt.adapters.snowflake.relation import SnowflakeRelation


def query_relation_type(project, relation: SnowflakeRelation) -> Optional[str]:
    sql = f"""
        select
            case
                when table_type = 'BASE TABLE' and is_dynamic = 'YES' then 'dynamic_table'
                when table_type = 'BASE TABLE' then 'table'
                when table_type = 'VIEW' then 'view'
                when table_type = 'EXTERNAL TABLE' then 'external_table'
            end as relation_type
        from information_schema.tables
        where table_name like '{relation.identifier.upper()}'
        and table_schema like '{relation.schema.upper()}'
        and table_catalog like '{relation.database.upper()}'
    """
    results = project.run_sql(sql, fetch="one")
    if results is None or len(results) == 0:
        return None
    elif len(results) > 1:
        raise ValueError(f"More than one instance of {relation.name} found!")
    else:
        return results[0].lower()


def query_target_lag(project, dynamic_table: SnowflakeRelation) -> Optional[str]:
    config = describe_dynamic_table(project, dynamic_table)
    return config.get("target_lag")


def query_warehouse(project, dynamic_table: SnowflakeRelation) -> Optional[str]:
    config = describe_dynamic_table(project, dynamic_table)
    return config.get("warehouse")


def query_refresh_mode(project, dynamic_table: SnowflakeRelation) -> Optional[str]:
    config = describe_dynamic_table(project, dynamic_table)
    return config.get("refresh_mode")


def describe_dynamic_table(project, dynamic_table: SnowflakeRelation) -> agate.Row:
    with get_connection(project.adapter):
        macro_results = project.adapter.execute_macro(
            "snowflake__describe_dynamic_table", kwargs={"relation": dynamic_table}
        )
    config = macro_results["dynamic_table"]
    return config.rows[0]
