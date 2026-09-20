# 01 — Basics

## Connecting

```bash
docker compose exec mysql mysql -u root -p ecommerce
```

Useful client commands (note: no semicolon needed for these):
```sql
SHOW DATABASES;
USE ecommerce;
SHOW TABLES;
DESCRIBE products;       -- column list, types, keys
SHOW CREATE TABLE products\G   -- \G prints vertically, readable for wide output
```

## CRUD

```sql
-- Create
INSERT INTO customers (first_name, last_name, email, country, signed_up_at)
VALUES ('Test', 'User', 'test.user@example.com', 'Portugal', CURDATE());

-- Read
SELECT customer_id, first_name, last_name FROM customers WHERE country = 'Portugal';

-- Update
UPDATE customers SET country = 'Spain' WHERE email = 'test.user@example.com';

-- Delete
DELETE FROM customers WHERE email = 'test.user@example.com';
```

Things that bite beginners:
- MySQL's default mode is **not** strict about silently truncating/coercing
  bad data unless `sql_mode` includes `STRICT_TRANS_TABLES` (default since
  5.7/8.0, but worth knowing `SELECT @@sql_mode;` exists).
- `UPDATE`/`DELETE` without a `WHERE` clause affects every row. There's no
  confirmation prompt.
- `LIMIT` has no `ORDER BY` guarantee — without an explicit `ORDER BY`, which
  rows you get from `LIMIT n` is not guaranteed to be stable across runs.

## Data types (the ones you'll actually use)

| Category | Types | Notes |
|---|---|---|
| Integers | `TINYINT`, `SMALLINT`, `INT`, `BIGINT` | Add `UNSIGNED` when negatives are impossible (doubles the positive range) |
| Exact decimal | `DECIMAL(p,s)` | Use for money. Never use `FLOAT`/`DOUBLE` for currency — they're binary floating point and will drift |
| Strings | `VARCHAR(n)`, `TEXT` | `VARCHAR` has a length cap and can be indexed directly; prefer it unless you genuinely need unbounded text |
| Dates | `DATE`, `DATETIME`, `TIMESTAMP` | `TIMESTAMP` is stored in UTC and converted to the session timezone on read; `DATETIME` stores exactly what you put in, no timezone conversion |
| Enum | `ENUM('a','b','c')` | Compact, but adding a new value means an `ALTER TABLE`. Fine for a small fixed set (like `orders.status` here); avoid for anything that grows |
| Boolean | `BOOLEAN` | Actually a `TINYINT(1)` alias — MySQL has no real boolean type |

See it in this database: `SHOW CREATE TABLE orders\G` — note `status ENUM(...)`
and `unit_price DECIMAL(10,2)`.

## Exercises

Open `exercises.sql`, write your queries there, run them against the live
`ecommerce` database. No answer key on purpose — check yourself by reasoning
about the row counts you expect.
