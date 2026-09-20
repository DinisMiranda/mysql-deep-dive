-- 02-querying exercises.

-- 1. List each order with the customer's full name and the order's status.

-- 2. Find every customer who has never placed an order (LEFT JOIN + IS NULL).

-- 3. Total revenue (quantity * unit_price) per product, highest first.

-- 4. Total revenue per month (use DATE_FORMAT(ordered_at, '%Y-%m')), excluding
--    cancelled orders.

-- 5. Customers who have placed more than 3 orders (GROUP BY + HAVING).

-- 6. The single most expensive product in each category (correlated subquery
--    or a window function if you want to jump ahead to module 04).

-- 7. Using a CTE, find the top 5 customers by total amount spent
--    (exclude cancelled orders).

-- 8. Products that have never been ordered (LEFT JOIN order_items, IS NULL).

-- 9. For each category, the number of distinct customers who bought from it.

-- 10. The average order value (per order, not per line item), excluding cancelled orders.
