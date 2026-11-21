from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_DIR}/dbt_project"
DBT = f"cd {DBT_DIR} && dbt"
DBT_FLAGS = f"--profiles-dir {DBT_DIR} --target prod"

with DAG(
    dag_id="olist_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["olist", "dbt"],
) as dag:
    extract_clean_load = BashOperator(
        task_id="extract_clean_load",
        bash_command=f"cd {PROJECT_DIR} && python -m src.loading.clean_and_load",
    )
    dbt_deps = BashOperator(task_id="dbt_deps", bash_command=f"{DBT} deps {DBT_FLAGS}")
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT} run --select staging marts {DBT_FLAGS}",
    )
    dbt_test = BashOperator(task_id="dbt_test", bash_command=f"{DBT} test {DBT_FLAGS}")
    dbt_run_reports = BashOperator(
        task_id="dbt_run_reports",
        bash_command=f"{DBT} run --select reports {DBT_FLAGS}",
    )

    extract_clean_load >> dbt_deps >> dbt_run >> dbt_test >> dbt_run_reports