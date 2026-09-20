-- 05-performance exercises. Prefix each with EXPLAIN (or EXPLAIN ANALYZE)
-- and read the `type`/`key`/`rows`/`Extra` columns before moving on.

-- 1. Run EXPLAIN on your "revenue per month" query from 02-querying. Nothing
--    in this small dataset will be slow, but get comfortable reading the
--    output -- this is the skill that matters most once tables have millions
--    of rows.


-- 2. Compare these two and explain, from the EXPLAIN output, why the first
--    can use idx_orders_ordered_at and the second can't:
--      EXPLAIN SELECT * FROM orders WHERE ordered_at > '2026-03-01';
--      EXPLAIN SELECT * FROM orders WHERE YEAR(ordered_at) = 2026;


-- 3. CREATE INDEX idx_products_category_price ON products (category_id, unit_price);
--    then EXPLAIN SELECT name FROM products WHERE category_id = 1 AND unit_price > 30;
--    -- confirm the new index gets used (check `key` in the output), then
--    DROP INDEX idx_products_category_price ON products;
