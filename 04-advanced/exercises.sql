-- 04-advanced exercises.

-- 1. Rewrite your "top 5 customers by spend" query from 02-querying using
--    RANK() instead of ORDER BY ... LIMIT 5. Under what condition (ties)
--    would the two versions give different results?


-- 2. Create a view `product_revenue` summarizing total revenue per product
--    (quantity * unit_price, summed via order_items). Query it filtered to
--    revenue > 200.


-- 3. Write a trigger that prevents (via SIGNAL) an order_items insert with
--    quantity > 100 -- a crude fraud/typo guard. Test it with an INSERT that
--    should be rejected.
