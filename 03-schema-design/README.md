# 03 — Schema Design

## Normalization, briefly

- **1NF**: every column holds a single atomic value (no comma-separated lists
  stuffed into one column), rows are uniquely identifiable.
- **2NF**: 1NF + every non-key column depends on the *whole* primary key, not
  part of it. Matters mainly for composite keys.
- **3NF**: 2NF + no non-key column depends on another non-key column
  (no transitive dependency).

This database is a working 3NF example: `order_items.unit_price` looks
redundant with `products.unit_price`, but it isn't a normalization violation
— it's an intentional **snapshot** of the price at the moment of purchase, so
that a later price change doesn't rewrite history. This is a common,
deliberate reason to duplicate a value: normalize for data you must keep
consistent, denormalize (or snapshot) for facts that are true at a point in
time.

Real systems often denormalize on purpose for read performance (a
`orders.total_amount` column instead of summing `order_items` every time).
That's a legitimate trade — just make the trade consciously, and keep the
derived value in sync (trigger, application code, or recompute-on-write).

## Keys & constraints

```sql
PRIMARY KEY        -- unique, not null, one per table (can be composite)
FOREIGN KEY         -- enforces referential integrity: can't insert an
                     -- order_items row pointing at a product_id that doesn't exist
UNIQUE              -- e.g. customers.email — no two rows may share a value
CHECK (expr)        -- e.g. quantity > 0 — enforced by the server in MySQL 8.0.16+
NOT NULL / DEFAULT  -- basic column-level constraints
```

Try breaking things to see the constraints in action:
```sql
-- Fails: no category_id 999
INSERT INTO products (category_id, sku, name, unit_price) VALUES (999, 'X', 'X', 1);

-- Fails: duplicate email
INSERT INTO customers (first_name, last_name, email, country, signed_up_at)
VALUES ('A', 'B', 'ana.silva@example.com', 'Portugal', CURDATE());

-- Fails: CHECK constraint
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (1, 1, 0, 10);
```

### ON DELETE / ON UPDATE

By default a `FOREIGN KEY` blocks deleting a referenced row
(`ON DELETE RESTRICT`, the implicit default). You can instead say
`ON DELETE CASCADE` (delete children too) or `ON DELETE SET NULL` (requires
the FK column to be nullable). Choose deliberately — `CASCADE` on the wrong
relationship is how people accidentally delete a customer's entire order
history.

## Indexes — the design angle

An index isn't just "add it to make things fast" — it's a table you design
alongside your queries. Covered in depth in `05-performance`; the schema-design
takeaway here: every `FOREIGN KEY` in MySQL/InnoDB automatically gets an
index (needed to make the constraint check itself fast), which is why
`orders.customer_id` and `order_items.order_id`/`product_id` are already
indexed in `01_schema.sql` without an explicit `INDEX` clause for those.

## Exercise

Design (on paper/markdown, no need to run it) a schema for a blog: `authors`,
`posts`, `tags` (many-to-many with posts), `comments`. Decide: what's the
primary key of the posts-tags relationship? What happens to comments when a
post is deleted — cascade or restrict? What should be `NOT NULL`?
