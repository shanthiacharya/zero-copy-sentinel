-- Zero-Copy Sentinel — Step 9d: trigger the schema drift.
-- Run this LAST, only after: (1) 01 + 02 have run, (2) the table has been
-- ingested into DataHub once already (capturing schema v1 WITH discount_pct),
-- and (3) the downstream entity's column-level lineage has been seeded
-- pointing at discount_pct. This simulates "someone changed the schema
-- upstream" — the moment this Snowflake table no longer has the column,
-- the downstream lineage edge becomes dangling, which is exactly what the
-- agent should detect on re-ingestion.

USE WAREHOUSE ZCS_WH;
USE DATABASE FINANCE_DB;
USE SCHEMA PUBLIC;

ALTER TABLE REVENUE_LIVE_ICEBERG DROP COLUMN discount_pct;

-- Confirm it's gone
DESCRIBE TABLE REVENUE_LIVE_ICEBERG;
