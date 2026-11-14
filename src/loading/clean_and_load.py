import pandas as pd
from sqlalchemy import create_engine


def clean_extracted_data(df_dict):

    required_tables = {
        "olist_orders_dataset": "olist_orders",
        "olist_customers_dataset": "olist_customers",
        "olist_products_dataset": "olist_products",
        "olist_order_items_dataset": "olist_order_items",
        "exchange_rates": "exchange_rates"
    }

    cleaned_data = {}

    # Check that all required dataframes exist
    for source_name in required_tables:
        if source_name not in df_dict:
            raise ValueError(f"Missing required dataframe: {source_name}")

    # Make copies so we don't modify the original data
    for source_name, table_name in required_tables.items():

        df = df_dict[source_name].copy()

        # Remove extra spaces from text columns
        for column in df.select_dtypes(include=["object"]).columns:
            df[column] = df[column].apply(
                lambda value: value.strip() if isinstance(value, str) else value
            )

        # Customers cleaning
        if table_name == "olist_customers":
            df["customer_zip_code_prefix"] = (
                df["customer_zip_code_prefix"]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.zfill(5)
            )

        # Orders cleaning
        elif table_name == "olist_orders":
            date_columns = [
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date"
            ]

            for column in date_columns:
                df[column] = pd.to_datetime(df[column], errors="coerce")

        # Products cleaning
        elif table_name == "olist_products":
            numeric_columns = [
                "product_name_lenght",
                "product_description_lenght",
                "product_photos_qty",
                "product_weight_g",
                "product_length_cm",
                "product_height_cm",
                "product_width_cm"
            ]

            for column in numeric_columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        # Order items cleaning
        elif table_name == "olist_order_items":
            df["shipping_limit_date"] = pd.to_datetime(
                df["shipping_limit_date"], errors="coerce"
            )

        # Exchange rates cleaning
        elif table_name == "exchange_rates":
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["rate"] = pd.to_numeric(df["rate"], errors="coerce")

        cleaned_data[table_name] = df

    return cleaned_data


def load_to_sqlserver(df_dict, db_connection_string):

    engine = create_engine(db_connection_string)

    with engine.begin() as connection:

        for table_name, df in df_dict.items():

            df.to_sql(
                name=table_name,
                con=connection,
                if_exists="replace",
                index=False,
                chunksize=1000
            )

            print(f"Loaded {len(df)} rows into {table_name}")

    engine.dispose()