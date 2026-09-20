# 02 — Querying

## Joins

```sql
-- INNER JOIN: only rows with a match on both sides
SELECT o.order_id, c.first_name, c.last_name
FROM orders o
INNER JOIN customers c ON c.customer_id = o.customer_id;

-- LEFT JOIN: all rows from the left table, NULLs on the right when there's no match.
-- Use this to find "customers with no orders" — a classic anti-join pattern.
SELECT c.customer_id, c.first_name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- Joining through a bridge table (order_items) to get product-level detail
SELECT o.order_id, p.name, oi.quantity, oi.unit_price
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_id = 1;
```

MySQL also has `RIGHT JOIN` (rarely used — just flip the tables and use
`LEFT JOIN`) and no native `FULL OUTER JOIN` (emulate with `LEFT JOIN UNION
RIGHT JOIN` if you ever need it).

## Aggregation

```sql
-- Revenue per category
SELECT cat.name, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN categories cat ON cat.category_id = p.category_id
GROUP BY cat.name
ORDER BY revenue DESC;

-- HAVING filters on the aggregate, WHERE filters before aggregation
SELECT customer_id, COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 3;
```

`ONLY_FULL_GROUP_BY` is on by default in MySQL 8: every non-aggregated column
in `SELECT` must appear in `GROUP BY`. If you hit "not functionally dependent
on GROUP BY columns", that's why — it's protecting you from an
arbitrary/undefined value being picked.

## Subqueries vs CTEs

```sql
-- Subquery in WHERE
SELECT * FROM customers
WHERE customer_id IN (SELECT customer_id FROM orders WHERE status = 'cancelled');

-- Same logic as a CTE (WITH) — more readable once queries get nested,
-- and reusable within the same statement
WITH cancelled_customers AS (
    SELECT DISTINCT customer_id FROM orders WHERE status = 'cancelled'
)
SELECT c.* FROM customers c JOIN cancelled_customers cc USING (customer_id);

-- Correlated subquery: re-evaluated per outer row. Watch performance on large tables.
SELECT p.name, p.unit_price
FROM products p
WHERE p.unit_price > (
    SELECT AVG(unit_price) FROM products p2 WHERE p2.category_id = p.category_id
);
```

CTEs (`WITH ... AS (...)`) don't change what's possible (everything a CTE
does, a subquery can too) — they change what's *readable*. Reach for one when
a query needs to reference the same derived result more than once, or when
nesting subqueries gets hard to follow.

## Exercises

See `exercises.sql`.
