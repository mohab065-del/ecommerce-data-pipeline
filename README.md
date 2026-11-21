# E-Commerce Data Integration & Analytics Pipeline

End-to-end data pipeline: Olist Brazilian e-commerce CSV files plus daily BRL to USD exchange rates are cleaned, loaded into SQL Server, modelled into a Star Schema with dbt, and orchestrated with Airflow.

## Architecture

    data/raw/*.csv  +  Frankfurter API (BRL to USD)
              |
        src/extraction
              |
        src/loading/clean_and_load.py  ->  dbo.olist_* and dbo.exchange_rates
              |
        dbt_project:  staging (views) -> marts (tables) -> reports (views)
              |
        dags/olist_pipeline_dag.py  (Airflow orchestration)

## Star Schema

Grain: one row per order item (order_id + order_item_id).

    fct_sales  ->  dim_customer   (customer_key = customer_unique_id)
               ->  dim_product    (product_key)
               ->  dim_seller     (seller_key)
               ->  dim_date       (date_key = yyyymmdd)

`fct_sales` holds prices and freight in BRL and USD (`price_usd`, `freight_usd`, `total_usd`), together with `fx_rate`, `fx_rate_date` and `fx_gap_days`.

Currency conversion uses an as-of join: each order takes the latest exchange rate dated on or before its purchase date.

Reporting views (schema `reports`): `rpt_daily_revenue`, `rpt_category_performance`, `rpt_customer_value`.

Indexes on the join and filter columns of `fct_sales` and on the dimension keys are created by a dbt post-hook (`create_index` macro).

## Project structure

    .
    ├── run_pipeline.py            run everything: load, then dbt
    ├── requirements.txt
    ├── data/raw/                  Olist CSV files (not tracked by Git)
    ├── src/
    │   ├── extraction/            olist_extractor.py, currency_extractor.py
    │   └── loading/               clean_and_load.py
    ├── dbt_project/
    │   ├── macros/
    │   └── models/                staging, marts, reports
    └── dags/                      olist_pipeline_dag.py

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Install Microsoft ODBC Driver 18 for SQL Server and create an empty database.
3. Download the Olist dataset and place the CSV files in `data/raw/`.
4. Create a `.env` file in the project root (it is ignored by Git):

        DB_SERVER=your_server
        DB_NAME=your_database

   For SQL authentication also set `DB_USER` and `DB_PASSWORD`.
5. `dbt_project/profiles.yml` uses Windows authentication. For SQL authentication replace `windows_login: true` with `user` and `password` read from `env_var('DB_USER')` and `env_var('DB_PASSWORD')`, and do not commit that change.

## Run

Everything in one command:

    python run_pipeline.py

Skip the loading step when the raw tables are already loaded:

    python run_pipeline.py --skip-load

Step by step:

    python -m src.loading.clean_and_load
    cd dbt_project
    dbt deps
    dbt run --select staging marts
    dbt test
    dbt run --select reports

dbt does not read `.env`. `run_pipeline.py` loads it for you; for manual dbt runs set `DB_SERVER` and `DB_NAME` as environment variables first.

## Data quality

dbt tests cover unique and not-null keys, relationships between the fact and every dimension, and the age of the exchange rate used (`fx_gap_days`). Missing exchange rates or rates older than 7 days raise warnings without stopping the pipeline.

## Edge cases handled

| Case | Handling |
|---|---|
| Order date without an exchange rate (weekends, holidays) | As-of join uses the latest earlier rate; `fx_gap_days` shows its age |
| Order earlier than the first available rate | USD columns stay NULL and a warning test flags them |
| Invalid or duplicate exchange rates | Removed in `stg_fx_rates` |
| Duplicate order items | Deduplicated in `stg_order_items` |
| `customer_id` changes on every order | `dim_customer` is keyed on `customer_unique_id` |
| Products without a category translation | Falls back to the Portuguese name, then `unknown` |
| Zip codes losing leading zeros | CSV files are read as strings |
| Re-running the pipeline | Tables are rebuilt, so every run is idempotent |

## Airflow

`dags/olist_pipeline_dag.py` runs `extract_clean_load`, `dbt_deps`, `dbt_run`, `dbt_test` and `dbt_run_reports` in sequence. Adjust `PROJECT_DIR` to the location of the project inside your Airflow environment. Windows authentication does not work from Linux or Docker, so use SQL authentication there.

## Team

Add team member names here.