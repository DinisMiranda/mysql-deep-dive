-- Star-schema warehouse fed by etl_pipeline.py from the `ecommerce` OLTP database.
-- Run once: docker compose exec -T mysql mysql -u root -p"$MYSQL_ROOT_PASSWORD" < 06-etl/warehouse_schema.sql

CREATE DATABASE IF NOT EXISTS warehouse;
USE warehouse;

CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INT PRIMARY KEY,          -- YYYYMMDD, e.g. 20260315
    full_date       DATE NOT NULL,
    year            SMALLINT NOT NULL,
    quarter         TINYINT NOT NULL,
    month           TINYINT NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    day             TINYINT NOT NULL,
    day_of_week     VARCHAR(20) NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

-- Type 1 SCD (overwrite on change) for simplicity. A "how would you do this
-- properly" extension is to make it Type 2: add valid_from/valid_to/is_current
-- and insert a new row instead of updating when a tracked attribute changes.
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key    INT PRIMARY KEY,          -- = ecommerce.customers.customer_id
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    email           VARCHAR(150) NOT NULL,
    country         VARCHAR(60) NOT NULL,
    loaded_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key     INT PRIMARY KEY,          -- = ecommerce.products.product_id
    sku             VARCHAR(32) NOT NULL,
    name            VARCHAR(150) NOT NULL,
    category_name   VARCHAR(100) NOT NULL,
    current_price   DECIMAL(10,2) NOT NULL,
    loaded_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_key        BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_item_id   INT UNSIGNED NOT NULL UNIQUE,   -- natural key from source, makes reloads idempotent
    order_id        INT UNSIGNED NOT NULL,
    date_key        INT NOT NULL,
    customer_key    INT NOT NULL,
    product_key     INT NOT NULL,
    quantity        SMALLINT UNSIGNED NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    revenue         DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    INDEX idx_fact_sales_date (date_key),
    INDEX idx_fact_sales_customer (customer_key),
    INDEX idx_fact_sales_product (product_key)
);

-- Tracks incremental-load progress: the ETL script reads/writes this instead
-- of re-extracting the whole source table on every run. Stores the highest
-- ecommerce.order_items.order_item_id processed so far (not a timestamp —
-- an AUTO_INCREMENT id is unique and strictly increasing, so there's no
-- tie-at-the-boundary risk the way there is with a DATETIME watermark).
CREATE TABLE IF NOT EXISTS etl_control (
    job_name        VARCHAR(100) PRIMARY KEY,
    last_watermark  BIGINT UNSIGNED NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
