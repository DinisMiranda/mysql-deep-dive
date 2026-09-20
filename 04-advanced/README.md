# 04 — Advanced SQL

## Window functions

Unlike `GROUP BY`, a window function keeps every row while computing an
aggregate "over a window" of related rows.

```sql
-- Running total of revenue per day
SELECT
    DATE(o.ordered_at) AS day,
    SUM(oi.quantity * oi.unit_price) AS daily_revenue,
    SUM(SUM(oi.quantity * oi.unit_price)) OVER (ORDER BY DATE(o.ordered_at)) AS running_total
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status != 'cancelled'
GROUP BY DATE(o.ordered_at)
ORDER BY day;

-- Rank customers by total spend
SELECT
    c.customer_id, c.first_name, c.last_name,
    SUM(oi.quantity * oi.unit_price) AS total_spent,
    RANK() OVER (ORDER BY SUM(oi.quantity * oi.unit_price) DESC) AS spend_rank
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id AND o.status != 'cancelled'
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY spend_rank;

-- Each order's value vs. that same customer's previous order (LAG)
SELECT
    o.customer_id, o.order_id, o.ordered_at,
    LAG(o.ordered_at) OVER (PARTITION BY o.customer_id ORDER BY o.ordered_at) AS previous_order_at
FROM orders o
ORDER BY o.customer_id, o.ordered_at;
```

`ROW_NUMBER()` vs `RANK()` vs `DENSE_RANK()`: with a tie, `ROW_NUMBER` still
hands out distinct sequential numbers (arbitrarily breaking the tie),
`RANK` gives the tied rows the same rank and then skips the next rank number,
`DENSE_RANK` gives the same rank and does *not* skip.

## Views

A view is a saved, named query — not a copy of data. Good for hiding a
complex join behind a simple name, or as a stable interface when the
underlying tables change shape.

```sql
CREATE VIEW order_totals AS
SELECT o.order_id, o.customer_id, o.status,
       SUM(oi.quantity * oi.unit_price) AS total
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.customer_id, o.status;

SELECT * FROM order_totals WHERE total > 100;
```

## Stored procedures & functions

```sql
DELIMITER //
CREATE PROCEDURE customer_order_count(IN cust_id INT, OUT order_count INT)
BEGIN
    SELECT COUNT(*) INTO order_count FROM orders WHERE customer_id = cust_id;
END //
DELIMITER ;

CALL customer_order_count(1, @count);
SELECT @count;
```

`DELIMITER //` is a *client* convention (not MySQL syntax) so the client
doesn't treat the semicolons inside the procedure body as the end of the
statement. Reset it back to `;` after.

## Triggers

```sql
CREATE TABLE order_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNSIGNED,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DELIMITER //
CREATE TRIGGER trg_order_status_change
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO order_audit (order_id, old_status, new_status)
        VALUES (OLD.order_id, OLD.status, NEW.status);
    END IF;
END //
DELIMITER ;

UPDATE orders SET status = 'shipped' WHERE order_id = 13;
SELECT * FROM order_audit;
```

Use triggers sparingly — logic hidden in the database is easy for application
developers to miss. They're the right tool for things that must *always*
hold regardless of which application code touches the table (audit trails,
invariants), not for general business logic.

## Transactions

```sql
START TRANSACTION;
UPDATE orders SET status = 'shipped' WHERE order_id = 1;
INSERT INTO order_audit (order_id, old_status, new_status) VALUES (1, 'paid', 'shipped');
COMMIT;      -- or ROLLBACK to undo everything since START TRANSACTION
```

InnoDB (MySQL's default engine) is ACID and defaults to isolation level
`REPEATABLE READ`. Compared to `READ COMMITTED` (Postgres's default),
`REPEATABLE READ` means a value you read once stays consistent for the rest
of your transaction, even if another transaction commits a change to it in
the meantime — at the cost of more locking. Check yours with
`SELECT @@transaction_isolation;`.

## Exercises

See `exercises.sql`.
