-- Zero-Copy Sentinel — Step 9a: add the column that will later be dropped.
-- Run this NOW, right after 01_setup.sql. This must happen BEFORE the first
-- DataHub ingestion so the "discount_pct" column exists in schema v1, and
-- BEFORE we set up downstream lineage pointing at it.

USE WAREHOUSE ZCS_WH;
USE DATABASE FINANCE_DB;
USE SCHEMA PUBLIC;

ALTER TABLE REVENUE_LIVE_ICEBERG ADD COLUMN discount_pct DECIMAL(5,2);

CREATE OR REPLACE TEMPORARY TABLE _discount_updates (transaction_id VARCHAR, pct DECIMAL(5,2)) AS
SELECT * FROM VALUES
  ('TXN-3000', 8.1),
  ('TXN-3001', 3.8),
  ('TXN-3002', 16.3),
  ('TXN-3003', 1.8),
  ('TXN-3004', 13.4),
  ('TXN-3005', 9.1),
  ('TXN-3006', 1.4),
  ('TXN-3007', 12.7),
  ('TXN-3008', 0.9),
  ('TXN-3009', 10.8),
  ('TXN-3010', 1.7),
  ('TXN-3011', 2.3),
  ('TXN-3012', 10.6),
  ('TXN-3013', 20.7),
  ('TXN-3014', 3.1),
  ('TXN-3015', 5.6),
  ('TXN-3016', 15.7),
  ('TXN-3017', 23.7),
  ('TXN-3018', 14.4),
  ('TXN-3019', 9.9),
  ('TXN-3020', 24.4),
  ('TXN-3021', 1.2),
  ('TXN-3022', 21.5),
  ('TXN-3023', 7.2),
  ('TXN-3024', 3.6),
  ('TXN-3025', 2.9),
  ('TXN-3026', 7.7),
  ('TXN-3027', 20.4),
  ('TXN-3028', 4.5),
  ('TXN-3029', 14.5),
  ('TXN-3030', 16.0),
  ('TXN-3031', 9.3),
  ('TXN-3032', 13.7),
  ('TXN-3033', 1.6),
  ('TXN-3034', 1.5),
  ('TXN-3035', 5.1),
  ('TXN-3036', 17.0),
  ('TXN-3037', 10.7),
  ('TXN-3038', 7.9),
  ('TXN-3039', 14.6),
  ('TXN-3040', 11.3),
  ('TXN-3041', 7.5),
  ('TXN-3042', 19.9),
  ('TXN-3043', 17.5),
  ('TXN-3044', 6.1),
  ('TXN-3045', 14.4),
  ('TXN-3046', 13.1),
  ('TXN-3047', 21.9),
  ('TXN-3048', 18.2),
  ('TXN-3049', 7.2)
AS t(transaction_id, pct);

UPDATE REVENUE_LIVE_ICEBERG r
SET discount_pct = u.pct
FROM _discount_updates u
WHERE r.transaction_id = u.transaction_id;

-- Sanity check
SELECT transaction_id, amount, discount_pct FROM REVENUE_LIVE_ICEBERG LIMIT 5;
