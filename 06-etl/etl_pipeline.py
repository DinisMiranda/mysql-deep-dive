"""
A small but real ETL pipeline: ecommerce (OLTP) -> warehouse (star schema).

Extract : pull order_items with order_item_id greater than the last watermark
          from `ecommerce`.
Transform: shape them into dimension rows (date/customer/product) and fact rows,
           computing `revenue = quantity * unit_price` along the way.
Load    : upsert dimensions, upsert facts keyed on the natural key `order_item_id`
          (so re-running the script is idempotent — no duplicate facts), then
          advance the watermark.

Run once against a fresh warehouse:
    pip install -r requirements.txt
    python etl_pipeline.py

Run again after seeding more orders into `ecommerce` and it will only pick up
the new/changed rows (incremental load), not reprocess everything.

Cancelled orders are deliberately excluded from the fact table — a business
rule applied in the Transform step, not the Extract step, so it's visible and
easy to change.

The watermark is the max `order_item_id` seen, not a timestamp. order_item_id
is a monotonically increasing, unique AUTO_INCREMENT column, which avoids the
classic timestamp-watermark bug: with a DATETIME watermark and `WHERE
ordered_at > watermark`, two orders landing in the same second can tie at the
boundary and one gets silently skipped. It also means the watermark always
advances past cancelled orders too (extract sees them, transform drops them),
so a run doesn't keep re-pulling the same trailing cancelled rows forever.
"""

import os

import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3308"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", os.getenv("DB_PASSWORD", "mysql_study"))

JOB_NAME = "ecommerce_to_warehouse_sales"


def get_connection(database: str):
    """Raw DB-API connection, used for writes (executemany upserts)."""
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=database
    )


def get_engine(database: str):
    """SQLAlchemy engine, used for pd.read_sql (which wants one, not a raw connection)."""
    url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{database}"
    return create_engine(url)


def get_last_watermark(wh_conn) -> int:
    cur = wh_conn.cursor()
    cur.execute("SELECT last_watermark FROM etl_control WHERE job_name = %s", (JOB_NAME,))
    row = cur.fetchone()
    cur.close()
    if row:
        return row[0]
    return 0


def extract(src_engine, watermark: int) -> pd.DataFrame:
    """Pull sale line items (order_items joined up to customer/product/category)
    with order_item_id greater than the watermark. Includes cancelled orders —
    transform() drops them, but extract() must still see them so the watermark
    advances past them."""
    query = """
        SELECT
            oi.order_item_id,
            oi.order_id,
            oi.quantity,
            oi.unit_price,
            o.ordered_at,
            o.status,
            c.customer_id, c.first_name, c.last_name, c.email, c.country,
            p.product_id, p.sku, p.name AS product_name, p.unit_price AS current_price,
            cat.name AS category_name
        FROM order_items oi
        JOIN orders o     ON o.order_id = oi.order_id
        JOIN customers c  ON c.customer_id = o.customer_id
        JOIN products p   ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE oi.order_item_id > %s
        ORDER BY oi.order_item_id
    """
    df = pd.read_sql(query, src_engine, params=(watermark,))
    return df


def transform(df: pd.DataFrame):
    """Shape raw (already-extracted, still-including-cancelled) rows into
    dimension tables + a fact table. Returns
    (dim_date, dim_customer, dim_product, fact_sales) — any of which may be
    None if nothing survives the cancelled-order filter."""
    # Business rule lives here, not in the SQL: cancelled orders never sold anything.
    df = df[df["status"] != "cancelled"].copy()
    if df.empty:
        return None, None, None, None

    df["order_date"] = pd.to_datetime(df["ordered_at"]).dt.date
    df["date_key"] = df["order_date"].apply(lambda d: int(d.strftime("%Y%m%d")))
    df["revenue"] = df["quantity"] * df["unit_price"]

    dim_date = (
        df[["date_key", "order_date"]]
        .drop_duplicates()
        .rename(columns={"order_date": "full_date"})
    )
    dim_date["year"] = dim_date["full_date"].apply(lambda d: d.year)
    dim_date["quarter"] = dim_date["full_date"].apply(lambda d: (d.month - 1) // 3 + 1)
    dim_date["month"] = dim_date["full_date"].apply(lambda d: d.month)
    dim_date["month_name"] = dim_date["full_date"].apply(lambda d: d.strftime("%B"))
    dim_date["day"] = dim_date["full_date"].apply(lambda d: d.day)
    dim_date["day_of_week"] = dim_date["full_date"].apply(lambda d: d.strftime("%A"))
    dim_date["is_weekend"] = dim_date["full_date"].apply(lambda d: d.weekday() >= 5)

    dim_customer = df[
        ["customer_id", "first_name", "last_name", "email", "country"]
    ].drop_duplicates(subset="customer_id").rename(columns={"customer_id": "customer_key"})

    dim_product = df[
        ["product_id", "sku", "product_name", "category_name", "current_price"]
    ].drop_duplicates(subset="product_id").rename(
        columns={"product_id": "product_key", "product_name": "name"}
    )

    fact_sales = df[
        [
            "order_item_id", "order_id", "date_key", "customer_id", "product_id",
            "quantity", "unit_price", "revenue",
        ]
    ].rename(columns={"customer_id": "customer_key", "product_id": "product_key"})

    return dim_date, dim_customer, dim_product, fact_sales


def load_dim_date(wh_conn, dim_date: pd.DataFrame):
    cur = wh_conn.cursor()
    sql = """
        INSERT INTO dim_date (date_key, full_date, year, quarter, month, month_name, day, day_of_week, is_weekend)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE full_date = VALUES(full_date)
    """
    cur.executemany(sql, list(dim_date.itertuples(index=False, name=None)))
    wh_conn.commit()
    cur.close()


def load_dim_customer(wh_conn, dim_customer: pd.DataFrame):
    cur = wh_conn.cursor()
    sql = """
        INSERT INTO dim_customer (customer_key, first_name, last_name, email, country)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            first_name = VALUES(first_name), last_name = VALUES(last_name),
            email = VALUES(email), country = VALUES(country)
    """
    cur.executemany(sql, list(dim_customer.itertuples(index=False, name=None)))
    wh_conn.commit()
    cur.close()


def load_dim_product(wh_conn, dim_product: pd.DataFrame):
    cur = wh_conn.cursor()
    sql = """
        INSERT INTO dim_product (product_key, sku, name, category_name, current_price)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sku = VALUES(sku), name = VALUES(name),
            category_name = VALUES(category_name), current_price = VALUES(current_price)
    """
    cur.executemany(sql, list(dim_product.itertuples(index=False, name=None)))
    wh_conn.commit()
    cur.close()


def load_fact_sales(wh_conn, fact_sales: pd.DataFrame):
    cur = wh_conn.cursor()
    sql = """
        INSERT INTO fact_sales
            (order_item_id, order_id, date_key, customer_key, product_key, quantity, unit_price, revenue)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            quantity = VALUES(quantity), unit_price = VALUES(unit_price), revenue = VALUES(revenue)
    """
    cur.executemany(sql, list(fact_sales.itertuples(index=False, name=None)))
    wh_conn.commit()
    cur.close()


def update_watermark(wh_conn, new_watermark: int):
    cur = wh_conn.cursor()
    cur.execute(
        """
        INSERT INTO etl_control (job_name, last_watermark) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE last_watermark = VALUES(last_watermark)
        """,
        (JOB_NAME, new_watermark),
    )
    wh_conn.commit()
    cur.close()


def main():
    src_engine = get_engine("ecommerce")
    wh_conn = get_connection("warehouse")

    try:
        watermark = get_last_watermark(wh_conn)
        print(f"[extract] watermark = {watermark}")

        raw = extract(src_engine, watermark)
        print(f"[extract] pulled {len(raw)} order_item rows")

        if raw.empty:
            print("[load] nothing new to load")
            return

        # Watermark comes from the raw extract (cancelled rows included), so it
        # always advances past everything just seen — not just what made it
        # into the fact table.
        new_watermark = int(raw["order_item_id"].max())

        dim_date, dim_customer, dim_product, fact_sales = transform(raw)

        if fact_sales is None or fact_sales.empty:
            update_watermark(wh_conn, new_watermark)
            print(f"[load] nothing new to load (all cancelled). New watermark = {new_watermark}")
            return

        load_dim_date(wh_conn, dim_date)
        load_dim_customer(wh_conn, dim_customer)
        load_dim_product(wh_conn, dim_product)
        load_fact_sales(wh_conn, fact_sales)
        update_watermark(wh_conn, new_watermark)

        print(
            f"[load] {len(fact_sales)} fact rows, "
            f"{len(dim_customer)} customers, {len(dim_product)} products, "
            f"{len(dim_date)} dates. New watermark = {new_watermark}"
        )
    finally:
        src_engine.dispose()
        wh_conn.close()


if __name__ == "__main__":
    main()
