import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SNAPSHOTS = HERE / "snapshots"
TEST_RESULT_PATHS = [
    SNAPSHOTS / "dbt_test_results.json",
    ROOT / "dbt_project" / "target" / "run_results.json",
]
PENDING = "[PENDING ACTUAL DATA - DO NOT USE IN DEFENSE]"

NAVY = "#1F2A44"
STEEL = "#3E6E8E"
TEAL = "#4A8C8C"
GRAY = "#9AA5B1"
LIGHT = "#E4E8EC"

st.set_page_config(page_title="Olist pipeline dashboard", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stMetric"] {background: #F3F5F7; border: 1px solid #E4E8EC; border-radius: 6px; padding: 14px 16px;}
    h1, h2, h3 {color: #1F2A44;}
    </style>
    """,
    unsafe_allow_html=True,
)


def usd(value):
    return f"${value:,.0f}"


def num(value):
    return f"{int(value):,}"


def show(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def table(df):
    try:
        st.dataframe(df, hide_index=True, width="stretch")
    except TypeError:
        st.dataframe(df, hide_index=True, use_container_width=True)


def style(fig, height=380):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=NAVY),
        legend=dict(orientation="h", y=1.12),
    )
    fig.update_xaxes(gridcolor=LIGHT, linecolor=GRAY)
    fig.update_yaxes(gridcolor=LIGHT, linecolor=GRAY)
    return fig


def with_period(df):
    out = df.copy()
    out["period"] = pd.to_datetime(dict(year=out["year"], month=out["month"], day=1))
    return out


@st.cache_data(show_spinner=False)
def read_snapshot(name):
    path = SNAPSHOTS / f"{name}.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data(show_spinner=False, ttl=300)
def read_live(name):
    sys.path.insert(0, str(ROOT))
    from sqlalchemy import create_engine, text

    from dashboard.export_data import QUERIES
    from src.loading.clean_and_load import build_connection_string

    engine = create_engine(build_connection_string())
    try:
        return pd.read_sql(text(QUERIES[name]), engine)
    finally:
        engine.dispose()


def get(name):
    if st.session_state.get("live"):
        try:
            return read_live(name)
        except Exception as exc:
            st.sidebar.error(f"Live query failed for {name} ({type(exc).__name__}). Showing the snapshot instead.")
    return read_snapshot(name)


def require(*names):
    frames = {name: get(name) for name in names}
    missing = [name for name, frame in frames.items() if frame is None]
    if missing:
        st.warning(f"{PENDING} Missing: {', '.join(missing)}. Run `python -m dashboard.export_data`.")
        st.stop()
    return [frames[name] for name in names]


def read_test_results():
    for path in TEST_RESULT_PATHS:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), path
    return None, None


def page_overview():
    st.title("Pipeline overview")
    st.write(
        "Olist e-commerce orders and daily BRL to USD exchange rates are loaded into SQL Server "
        "and modelled as a star schema with dbt."
    )
    steps = [
        ("Extraction", "Olist CSV files and daily BRL to USD rates from the Frankfurter API.", "src/extraction"),
        ("Cleaning and loading", "Types are fixed and the tables are loaded into SQL Server (dbo).", "src/loading/clean_and_load.py"),
        ("Modelling with dbt", "Staging views, star schema tables and reporting views, with tests.", "dbt_project/"),
        ("Orchestration", "One command runs every step. The Airflow DAG defines the same order.", "run_pipeline.py, dags/olist_pipeline_dag.py"),
    ]
    for col, (title, body, where) in zip(st.columns(len(steps)), steps):
        with col:
            st.subheader(title)
            st.write(body)
            st.caption(where)

    (counts,) = require("row_counts")
    raw_mask = counts["table_name"].str.startswith("olist_") | (counts["table_name"] == "exchange_rates")
    left, right = st.columns(2)
    with left:
        st.subheader("Raw tables in SQL Server")
        table(counts[raw_mask].rename(columns={"table_name": "Table", "row_count": "Rows"}))
    with right:
        st.subheader("Star schema tables")
        table(counts[~raw_mask].rename(columns={"table_name": "Table", "row_count": "Rows"}))
    st.write(
        "fct_sales has one row per order item. It links to dim_customer, dim_product, dim_seller and dim_date."
    )


def page_currency():
    st.title("Currency conversion")
    st.write(
        "Every order item is converted from BRL to USD with the latest daily exchange rate dated on or before "
        "its purchase date (an as-of join in fct_sales). The columns fx_rate_date and fx_gap_days record "
        "which rate was used and how old it was."
    )
    fx, monthly = require("fx_quality", "monthly_brl_vs_usd")
    q = fx.iloc[0]
    first = pd.to_datetime(str(int(q["first_date_key"])), format="%Y%m%d")
    last = pd.to_datetime(str(int(q["last_date_key"])), format="%Y%m%d")

    a, b, c, d = st.columns(4)
    a.metric("Items converted to USD", num(q["items"] - q["null_usd"]))
    b.metric("Items without a USD value", num(q["null_usd"]))
    c.metric("Oldest rate used (days)", num(q["max_gap_days"]))
    d.metric("Rate range (USD per BRL)", f"{q['min_rate']:.3f} to {q['max_rate']:.3f}")
    st.caption(f"Purchase dates covered by fct_sales: {first:%Y-%m-%d} to {last:%Y-%m-%d}.")

    m = with_period(monthly)
    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        fig.add_scatter(x=m["period"], y=m["revenue_brl"], name="BRL", mode="lines+markers", line=dict(color=GRAY, width=2.5))
        fig.add_scatter(x=m["period"], y=m["revenue_usd"], name="USD", mode="lines+markers", line=dict(color=STEEL, width=2.5))
        fig.update_layout(title="Monthly revenue (item price) in BRL and USD")
        show(style(fig))
    with right:
        fig = go.Figure(
            go.Scatter(x=m["period"], y=m["avg_fx_rate"], mode="lines+markers", line=dict(color=TEAL, width=2.5))
        )
        fig.update_layout(title="Average exchange rate by month (USD per BRL)")
        show(style(fig))

    threshold = 100
    solid = m[m["orders"] >= threshold]
    if not solid.empty:
        lo = solid.loc[solid["avg_fx_rate"].idxmin()]
        hi = solid.loc[solid["avg_fx_rate"].idxmax()]
        st.write(
            f"Among months with at least {threshold} orders, the average rate ranged from "
            f"{lo['avg_fx_rate']:.3f} ({lo['period']:%Y-%m}) to {hi['avg_fx_rate']:.3f} ({hi['period']:%Y-%m})."
        )
    shown = m[["period", "orders", "revenue_brl", "revenue_usd", "avg_fx_rate"]].copy()
    shown["period"] = shown["period"].dt.strftime("%Y-%m")
    with st.expander("Monthly table"):
        table(shown.rename(columns={"period": "Month", "orders": "Orders", "revenue_brl": "Revenue BRL", "revenue_usd": "Revenue USD", "avg_fx_rate": "Average rate"}))


def page_kpis():
    st.title("Core KPIs")
    daily, customers = require("rpt_daily_revenue", "rpt_customer_value")
    daily = daily.copy()
    daily["full_date"] = pd.to_datetime(daily["full_date"])
    years = [int(y) for y in sorted(daily["year"].unique())]
    period = st.selectbox("Period", ["All"] + years)
    d = daily if period == "All" else daily[daily["year"] == period]

    revenue = d["revenue_usd"].sum()
    freight = d["freight_usd"].sum()
    orders = d["orders"].sum()
    items = d["items"].sum()
    aov = (revenue + freight) / orders if orders else 0

    row1 = st.columns(3)
    row1[0].metric("Revenue (item price, USD)", usd(revenue))
    row1[1].metric("Freight (USD)", usd(freight))
    row1[2].metric("Average order value incl. freight (USD)", f"${aov:,.2f}")
    row2 = st.columns(3)
    row2[0].metric("Orders", num(orders))
    row2[1].metric("Items sold", num(items))
    row2[2].metric("Customers with a valid order (all periods)", num(customers["customers"].sum()))
    st.caption(
        "Revenue is the sum of item prices converted to USD. It excludes freight and excludes canceled and "
        "unavailable orders. The customer count covers the whole dataset."
    )

    monthly = d.groupby(["year", "month"], as_index=False).agg(revenue_usd=("revenue_usd", "sum"), orders=("orders", "sum"))
    monthly = with_period(monthly)
    fig = go.Figure(go.Bar(x=monthly["period"], y=monthly["revenue_usd"], marker_color=STEEL))
    fig.update_layout(title="Revenue by month (USD)")
    show(style(fig))

    series = d.set_index("full_date")["revenue_usd"].resample("D").sum()
    fig = go.Figure()
    fig.add_scatter(x=series.index, y=series, name="Daily", line=dict(color=GRAY, width=1))
    fig.add_scatter(x=series.index, y=series.rolling(7).mean(), name="7-day average", line=dict(color=NAVY, width=2.5))
    fig.update_layout(title="Daily revenue (USD)")
    show(style(fig))


def page_breakdowns():
    st.title("Breakdowns")
    monthly, category, customers, status = require(
        "monthly_brl_vs_usd", "rpt_category_performance", "rpt_customer_value", "order_status"
    )
    tab_month, tab_category, tab_state, tab_status = st.tabs(["By month", "By category", "By state", "Order status"])

    with tab_month:
        m = with_period(monthly)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=m["period"], y=m["revenue_usd"], name="Revenue (USD)", marker_color=STEEL)
        fig.add_scatter(x=m["period"], y=m["orders"], name="Orders", line=dict(color=TEAL, width=2.5), secondary_y=True)
        fig.update_yaxes(title_text="Revenue (USD)", secondary_y=False)
        fig.update_yaxes(title_text="Orders", secondary_y=True, showgrid=False)
        fig.update_layout(title="Revenue and orders by month")
        show(style(fig, 420))

    with tab_category:
        n = st.slider("Categories shown", 5, 20, 10)
        top = category.sort_values("revenue_usd", ascending=False).head(n)
        fig = go.Figure(go.Bar(x=top["revenue_usd"], y=top["category_en"], orientation="h", marker_color=STEEL))
        fig.update_layout(title=f"Top {n} categories by revenue (USD)", yaxis=dict(autorange="reversed"))
        show(style(fig, 440))
        st.caption(
            "The orders column is not additive across categories because one order can contain items from "
            "several categories."
        )
        unknown = category[category["category_en"] == "unknown"]
        if not unknown.empty:
            row = unknown.iloc[0]
            st.write(
                f"Items without a product category: {num(row['items_sold'])} items, {usd(row['revenue_usd'])} of revenue."
            )
        with st.expander("All categories"):
            table(category.sort_values("revenue_usd", ascending=False))

    with tab_state:
        top = customers.sort_values("revenue_usd", ascending=False).head(15)
        fig = go.Figure(go.Bar(x=top["state"], y=top["revenue_usd"], marker_color=STEEL))
        fig.update_layout(title="Top 15 states by revenue incl. freight (USD)")
        show(style(fig))
        st.caption("State revenue includes freight, unlike the item-price revenue used on the other pages.")
        table(customers.sort_values("revenue_usd", ascending=False))

    with tab_status:
        fig = go.Figure(go.Bar(x=status["order_status"], y=status["orders"], marker_color=TEAL))
        fig.update_layout(title="Orders by status")
        show(style(fig))
        table(status)


def page_quality():
    st.title("Data quality")
    counts, fx, status = require("row_counts", "fx_quality", "order_status")
    c = counts.set_index("table_name")["row_count"]
    q = fx.iloc[0]
    orders_in_fact = status["orders"].sum()

    checks = [
        (
            "fct_sales rows equal olist_order_items rows",
            "OK" if c["fct_sales"] == c["olist_order_items"] else "Review",
            f"{num(c['fct_sales'])} and {num(c['olist_order_items'])}",
        ),
        ("Items without a USD value", "OK" if q["null_usd"] == 0 else "Review", num(q["null_usd"])),
        ("Oldest exchange rate used (days)", "OK" if q["max_gap_days"] <= 7 else "Review", num(q["max_gap_days"])),
        (
            "Orders in olist_orders that are not in fct_sales",
            "Info",
            f"{num(c['olist_orders'] - orders_in_fact)} (orders with no order items)",
        ),
        (
            "Customers in olist_customers and in dim_customer",
            "Info",
            f"{num(c['olist_customers'])} and {num(c['dim_customer'])} (dim_customer has one row per customer_unique_id)",
        ),
    ]
    st.subheader("Reconciliation checks")
    table(pd.DataFrame(checks, columns=["Check", "Result", "Detail"]))

    st.subheader("dbt tests")
    data, path = read_test_results()
    if data is None:
        st.warning(
            f"{PENDING} No dbt test results found. Run `dbt test` inside dbt_project, then copy "
            "dbt_project/target/run_results.json to dashboard/snapshots/dbt_test_results.json."
        )
        return
    results = pd.DataFrame(
        [
            {
                "Test": r["unique_id"].split(".")[2],
                "Status": r["status"],
                "Seconds": round(r.get("execution_time", 0), 2),
            }
            for r in data["results"]
            if r["unique_id"].startswith("test.")
        ]
    )
    if results.empty:
        st.warning(f"{PENDING} {path.name} has no test results. Run `dbt test` and copy the file again.")
        return
    by_status = results["Status"].value_counts()
    cols = st.columns(4)
    cols[0].metric("Tests run", num(len(results)))
    cols[1].metric("Passed", num(by_status.get("pass", 0)))
    cols[2].metric("Warnings", num(by_status.get("warn", 0)))
    cols[3].metric("Failed", num(by_status.get("fail", 0) + by_status.get("error", 0)))
    st.caption(f"Source: {path.name}, generated {data.get('metadata', {}).get('generated_at', 'unknown')}.")
    with st.expander("All tests"):
        table(results)


def page_takeaways():
    st.title("Takeaways and limitations")
    daily, monthly, customers, category = require(
        "rpt_daily_revenue", "monthly_brl_vs_usd", "rpt_customer_value", "rpt_category_performance"
    )
    dates = pd.to_datetime(daily["full_date"])
    total_revenue = daily["revenue_usd"].sum()
    total_orders = daily["orders"].sum()
    top_category = category.loc[category["revenue_usd"].idxmax()]
    top_state = customers.loc[customers["revenue_usd"].idxmax()]
    m = with_period(monthly)
    peak = m.loc[m["revenue_usd"].idxmax()]

    st.subheader("What the data shows")
    st.markdown(
        f"- From {dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}, valid orders total {num(total_orders)} "
        f"and item revenue is {usd(total_revenue)}.\n"
        f"- The top category is {top_category['category_en']} with {usd(top_category['revenue_usd'])}, "
        f"{top_category['revenue_usd'] / category['revenue_usd'].sum():.1%} of item revenue.\n"
        f"- The top state is {top_state['state']} with {usd(top_state['revenue_usd'])} including freight, "
        f"{top_state['revenue_usd'] / customers['revenue_usd'].sum():.1%} of the total.\n"
        f"- The best month is {peak['period']:%Y-%m}: {usd(peak['revenue_usd'])} from {num(peak['orders'])} orders."
    )

    st.subheader("Limitations")
    notes = [
        "Payments, reviews and delivery dates are not modelled, so the dashboard has no payment, review or delivery KPIs.",
        "Revenue means item price in USD. The state report adds freight, so its totals are higher.",
        "Customers are counted by customer_unique_id, and a customer's state is taken from their latest order.",
        "Each item uses the daily exchange rate for its purchase date, not the payment or delivery date.",
        "The Airflow DAG is written and loads without import errors, but it was not run end to end.",
    ]
    small = m[m["orders"] < 10]
    if not small.empty:
        labels = ", ".join(small["period"].dt.strftime("%Y-%m"))
        notes.append(f"Months with fewer than 10 orders look incomplete: {labels}.")
    full = pd.period_range(m["period"].min(), m["period"].max(), freq="M")
    present = set(m["period"].dt.to_period("M"))
    absent = [str(p) for p in full if p not in present]
    if absent:
        notes.append(f"No valid orders appear in these months: {', '.join(absent)}.")
    unknown = category[category["category_en"] == "unknown"]
    if not unknown.empty:
        notes.append(f"{num(unknown.iloc[0]['items_sold'])} items have no product category and are grouped as unknown.")
    st.markdown("\n".join(f"- {note}" for note in notes))


PAGES = {
    "Pipeline overview": page_overview,
    "Currency conversion": page_currency,
    "Core KPIs": page_kpis,
    "Breakdowns": page_breakdowns,
    "Data quality": page_quality,
    "Takeaways and limitations": page_takeaways,
}


def main():
    st.sidebar.title("Walkthrough")
    choice = st.sidebar.radio("Section", list(PAGES), label_visibility="collapsed")
    st.sidebar.toggle("Read live from SQL Server", key="live")
    ref = SNAPSHOTS / "fx_quality.csv"
    if ref.exists():
        st.sidebar.caption(f"Snapshot files saved {datetime.fromtimestamp(ref.stat().st_mtime):%Y-%m-%d %H:%M}")
    PAGES[choice]()


if __name__ == "__main__":
    main()
