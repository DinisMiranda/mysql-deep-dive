# 07 — Administration

Lighter-touch module: the operational commands worth having seen once.

## Backup & restore

```bash
# Dump one database to a .sql file
docker compose exec mysql mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" ecommerce > ecommerce_backup.sql

# Restore into a (fresh or existing) database
docker compose exec -T mysql mysql -u root -p"$MYSQL_ROOT_PASSWORD" ecommerce < ecommerce_backup.sql
```

`mysqldump` produces plain SQL (`CREATE TABLE` + `INSERT`) — portable and
human-readable, but slow to restore on large databases since it replays every
statement. For bigger data, `mysqlpump` (parallel dump) or physical backup
tools (`mysqlbackup`, Percona XtraBackup, or MySQL's own Enterprise Backup)
are what real production restores use.

## Users & privileges

```sql
CREATE USER 'analyst'@'%' IDENTIFIED BY 'a_real_password';
GRANT SELECT ON ecommerce.* TO 'analyst'@'%';          -- read-only on one database
GRANT SELECT, INSERT, UPDATE ON warehouse.* TO 'analyst'@'%';
FLUSH PRIVILEGES;

SHOW GRANTS FOR 'analyst'@'%';
REVOKE INSERT, UPDATE ON warehouse.* FROM 'analyst'@'%';
DROP USER 'analyst'@'%';
```

Principle: grant the narrowest privilege set that does the job. An ETL job's
database user needs `SELECT` on the source and `SELECT, INSERT, UPDATE` on
the target — not `ALL PRIVILEGES`, and never against `root`.

## Useful introspection

```sql
SHOW PROCESSLIST;              -- what's currently running/connected
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Threads_connected';
SELECT * FROM information_schema.TABLES WHERE table_schema = 'ecommerce';
SELECT * FROM information_schema.COLUMNS WHERE table_name = 'orders';
```

## Exercises

See `exercises.sql`.
