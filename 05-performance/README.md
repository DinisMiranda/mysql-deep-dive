# 05 — Performance

## EXPLAIN

```sql
EXPLAIN SELECT * FROM orders WHERE customer_id = 1;
```

Key columns to read:
- **type**: access method, roughly best→worst: `const`/`eq_ref` (single row
  by unique key) → `ref` (index lookup, possibly many rows) → `range` →
  `index` (full index scan) → `ALL` (full table scan — the one to hunt down
  on a large table).
- **key**: which index MySQL actually chose (or `NULL` if none).
- **rows**: MySQL's *estimate* of rows it'll examine — not exact, but useful
  for spotting something scanning way more than it should.
- **Extra**: `Using filesort` (had to sort outside of index order — costly on
  big result sets), `Using temporary` (built a temp table, common with
  `GROUP BY`/`DISTINCT` on non-indexed columns), `Using index` (covering
  index — see below, this one's *good*).

`EXPLAIN ANALYZE` (8.0.18+) actually runs the query and shows real timings
per step, not just estimates:
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 1;
```

## Try it: table scan vs index

```sql
EXPLAIN SELECT * FROM orders WHERE ordered_at > '2026-03-01';
-- Should use idx_orders_ordered_at (type: range)

EXPLAIN SELECT * FROM orders WHERE YEAR(ordered_at) = 2026;
-- Won't use the index: wrapping the column in a function makes it
-- non-sargable — MySQL can't use the index because it would have to compute
-- YEAR() on every row anyway. Rewrite as a range instead:
EXPLAIN SELECT * FROM orders WHERE ordered_at >= '2026-01-01' AND ordered_at < '2027-01-01';
```

## Indexing strategy

- **Composite index column order matters.** An index on `(a, b)` serves
  queries filtering on `a` alone, or `a AND b`, but not `b` alone (leftmost
  prefix rule).
- **Covering index**: if every column a query needs is in the index itself,
  MySQL never has to touch the actual table row (`Using index` in `Extra`).
  E.g. `INDEX (customer_id, status)` would cover
  `SELECT status FROM orders WHERE customer_id = ?`.
- **Cardinality**: an index on a low-cardinality column (like `orders.status`
  with 4 distinct values) is usually not worth much on its own — the
  optimizer may reasonably choose a table scan anyway, since a `ref` lookup
  matching a large fraction of the table isn't actually cheaper.
- **Don't over-index.** Every index speeds up reads that use it but slows
  down every `INSERT`/`UPDATE`/`DELETE` that touches the indexed columns
  (the index has to be maintained too), and takes disk space.

Try adding and comparing:
```sql
CREATE INDEX idx_products_category_price ON products (category_id, unit_price);
EXPLAIN SELECT name FROM products WHERE category_id = 1 AND unit_price > 30;
DROP INDEX idx_products_category_price ON products;
```

## Slow query log (optional, for later — needs config)

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.1;  -- seconds; log anything slower than 100ms
SHOW VARIABLES LIKE 'slow_query_log_file';
```
In the Docker setup, tail it with
`docker compose exec mysql tail -f /var/lib/mysql/*-slow.log`, or point it
elsewhere via `slow_query_log_file` first.

## Exercises

See `exercises.sql`.
