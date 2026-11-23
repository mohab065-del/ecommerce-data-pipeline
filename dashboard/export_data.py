from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.loading.clean_and_load import build_connection_string

OUTPUT_DIR = Path(__file__).parent / "snapshots"

QUERIES = {
    "rpt_daily_revenue": """
        SELECT * FROM reports.rpt_daily_revenue ORDER BY full_date
    """,
    "rpt_category_performance": """
        SELECT * FROM reports.rpt_category_performance ORDER BY revenue_usd DESC
    """,
    "rpt_customer_value": """
        SELECT * FROM reports.rpt_customer_value ORDER BY revenue_usd DESC
    """,
    "row_counts": """
        SELECT 'fct_sales' AS table_name, COUNT(*) AS row_count FROM marts.fct_sales
        UNION ALL SELECT 'dim_customer', COUNT(*) FROM marts.dim_customer
        UNION ALL SELECT 'dim_product', COUNT(*) FROM marts.dim_product
        UNION ALL SELECT 'dim_seller', COUNT(*) FROM marts.dim_seller
        UNION ALL SELECT 'dim_date', COUNT(*) FROM marts.dim_date
        UNION ALL SELECT 'olist_orders', COUNT(*) FROM dbo.olist_orders
        UNION ALL SELECT 'olist_order_items', COUNT(*) FROM dbo.olist_order_items
        UNION ALL SELECT 'olist_customers', COUNT(*) FROM dbo.olist_customers
        UNION ALL SELECT 'olist_products', COUNT(*) FROM dbo.olist_products
        UNION ALL SELECT 'olist_sellers', COUNT(*) FROM dbo.olist_sellers
        UNION ALL SELECT 'exchange_rates', COUNT(*) FROM dbo.exchange_rates
    """,
    "fx_quality": """
        SELECT COUNT(*) AS items,
               SUM(CASE WHEN total_usd IS NULL THEN 1 ELSE 0 END) AS null_usd,
               MIN(fx_gap_days) AS min_gap_days,
               MAX(fx_gap_days) AS max_gap_days,
               MIN(fx_rate) AS min_rate,
               MAX(fx_rate) AS max_rate,
               MIN(order_date_key) AS first_date_key,
               MAX(order_date_key) AS last_date_key
        FROM marts.fct_sales
    """,
    "monthly_brl_vs_usd": """
        SELECT d.year, d.month,
               COUNT(DISTINCT f.order_id) AS orders,
               SUM(f.price_brl) AS revenue_brl,
               SUM(f.price_usd) AS revenue_usd,
               AVG(f.fx_rate) AS avg_fx_rate
        FROM marts.fct_sales f
        JOIN marts.dim_date d ON d.date_key = f.order_date_key
        WHERE f.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
    """,
    "order_status": """
        SELECT order_status, COUNT(DISTINCT order_id) AS orders, COUNT(*) AS items
        FROM marts.fct_sales
        GROUP BY order_status
        ORDER BY orders DESC
    """,
}


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    engine = create_engine(build_connection_string())
    for name, query in QUERIES.items():
        df = pd.read_sql(text(query), engine)
        df.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
        print(f"{name}.csv: {len(df)} rows")
    engine.dispose()


if __name__ == "__main__":
    main()