-- 07-administration exercises.

-- 1. Create a read-only 'analyst' user scoped to `warehouse` only (not
--    `ecommerce`). Connect as that user (a second terminal/session) and
--    confirm a SELECT against `ecommerce` is rejected, while SELECT against
--    `warehouse` works. Clean up with DROP USER when done.
