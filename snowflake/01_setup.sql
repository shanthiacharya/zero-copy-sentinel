-- Zero-Copy Sentinel — Step 1: Snowflake setup
-- Run this in Snowsight as your trial account's admin user (ACCOUNTADMIN).
-- Creates a small warehouse/database/table with realistic transaction-level
-- revenue data, plus a dedicated read-only role for DataHub ingestion.

-- ---------------------------------------------------------------------------
-- 1. Warehouse (XS, auto-suspends after 1 min idle to conserve trial credits)
-- ---------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS ZCS_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- ---------------------------------------------------------------------------
-- 2. Database / schema
-- ---------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS FINANCE_DB;
CREATE SCHEMA IF NOT EXISTS FINANCE_DB.PUBLIC;

USE WAREHOUSE ZCS_WH;
USE DATABASE FINANCE_DB;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- 3. The "live" revenue table — transaction-level, not a single summary row.
--    This is what gets ingested into DataHub and stamped as the zero-copy
--    source of truth.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE REVENUE_LIVE_ICEBERG (
  transaction_id   VARCHAR(20)     NOT NULL,
  quarter          VARCHAR(10)     NOT NULL,
  region           VARCHAR(10)     NOT NULL,
  product_line     VARCHAR(20)     NOT NULL,
  amount           DECIMAL(18,2)   NOT NULL,
  recorded_at      TIMESTAMP_NTZ   NOT NULL
);

INSERT INTO REVENUE_LIVE_ICEBERG
  (transaction_id, quarter, region, product_line, amount, recorded_at)
VALUES
  ('TXN-3000', 'Q3-2026', 'APAC', 'Support', 120800.00, TO_TIMESTAMP_NTZ('2026-07-22 13:44:00')),
  ('TXN-3001', 'Q3-2026', 'NA', 'Services', 41300.00, TO_TIMESTAMP_NTZ('2026-07-25 12:10:00')),
  ('TXN-3002', 'Q3-2026', 'LATAM', 'Add-ons', 73700.00, TO_TIMESTAMP_NTZ('2026-07-23 17:14:00')),
  ('TXN-3003', 'Q3-2026', 'APAC', 'Platform', 67000.00, TO_TIMESTAMP_NTZ('2026-07-22 09:51:00')),
  ('TXN-3004', 'Q3-2026', 'APAC', 'Add-ons', 133400.00, TO_TIMESTAMP_NTZ('2026-07-23 10:13:00')),
  ('TXN-3005', 'Q3-2026', 'APAC', 'Services', 125700.00, TO_TIMESTAMP_NTZ('2026-07-24 15:56:00')),
  ('TXN-3006', 'Q3-2026', 'LATAM', 'Services', 153500.00, TO_TIMESTAMP_NTZ('2026-07-23 11:15:00')),
  ('TXN-3007', 'Q3-2026', 'APAC', 'Add-ons', 49300.00, TO_TIMESTAMP_NTZ('2026-07-25 15:23:00')),
  ('TXN-3008', 'Q3-2026', 'EMEA', 'Services', 92700.00, TO_TIMESTAMP_NTZ('2026-07-25 16:05:00')),
  ('TXN-3009', 'Q3-2026', 'NA', 'Platform', 41900.00, TO_TIMESTAMP_NTZ('2026-07-22 11:50:00')),
  ('TXN-3010', 'Q3-2026', 'LATAM', 'Platform', 66400.00, TO_TIMESTAMP_NTZ('2026-07-13 15:38:00')),
  ('TXN-3011', 'Q3-2026', 'LATAM', 'Support', 103500.00, TO_TIMESTAMP_NTZ('2026-07-18 09:43:00')),
  ('TXN-3012', 'Q3-2026', 'NA', 'Support', 41500.00, TO_TIMESTAMP_NTZ('2026-07-11 10:18:00')),
  ('TXN-3013', 'Q3-2026', 'LATAM', 'Services', 63800.00, TO_TIMESTAMP_NTZ('2026-07-15 09:46:00')),
  ('TXN-3014', 'Q3-2026', 'APAC', 'Services', 122200.00, TO_TIMESTAMP_NTZ('2026-07-17 10:55:00')),
  ('TXN-3015', 'Q3-2026', 'APAC', 'Services', 108600.00, TO_TIMESTAMP_NTZ('2026-07-05 14:48:00')),
  ('TXN-3016', 'Q3-2026', 'EMEA', 'Platform', 66600.00, TO_TIMESTAMP_NTZ('2026-07-20 14:31:00')),
  ('TXN-3017', 'Q3-2026', 'NA', 'Platform', 114300.00, TO_TIMESTAMP_NTZ('2026-07-12 13:15:00')),
  ('TXN-3018', 'Q3-2026', 'NA', 'Services', 142800.00, TO_TIMESTAMP_NTZ('2026-07-19 10:05:00')),
  ('TXN-3019', 'Q3-2026', 'LATAM', 'Platform', 38900.00, TO_TIMESTAMP_NTZ('2026-07-18 11:08:00')),
  ('TXN-3020', 'Q3-2026', 'LATAM', 'Services', 142400.00, TO_TIMESTAMP_NTZ('2026-07-09 17:55:00')),
  ('TXN-3021', 'Q3-2026', 'LATAM', 'Services', 128400.00, TO_TIMESTAMP_NTZ('2026-07-18 12:45:00')),
  ('TXN-3022', 'Q3-2026', 'APAC', 'Add-ons', 82100.00, TO_TIMESTAMP_NTZ('2026-07-12 16:57:00')),
  ('TXN-3023', 'Q3-2026', 'LATAM', 'Platform', 58200.00, TO_TIMESTAMP_NTZ('2026-07-08 12:04:00')),
  ('TXN-3024', 'Q3-2026', 'APAC', 'Platform', 162000.00, TO_TIMESTAMP_NTZ('2026-07-19 17:14:00')),
  ('TXN-3025', 'Q3-2026', 'EMEA', 'Platform', 81600.00, TO_TIMESTAMP_NTZ('2026-07-03 09:14:00')),
  ('TXN-3026', 'Q3-2026', 'NA', 'Platform', 50100.00, TO_TIMESTAMP_NTZ('2026-07-11 10:32:00')),
  ('TXN-3027', 'Q3-2026', 'EMEA', 'Support', 50600.00, TO_TIMESTAMP_NTZ('2026-07-16 12:34:00')),
  ('TXN-3028', 'Q3-2026', 'EMEA', 'Add-ons', 147800.00, TO_TIMESTAMP_NTZ('2026-07-08 16:51:00')),
  ('TXN-3029', 'Q3-2026', 'LATAM', 'Services', 116200.00, TO_TIMESTAMP_NTZ('2026-07-04 10:42:00')),
  ('TXN-3030', 'Q3-2026', 'LATAM', 'Support', 142500.00, TO_TIMESTAMP_NTZ('2026-07-14 15:29:00')),
  ('TXN-3031', 'Q3-2026', 'NA', 'Platform', 132500.00, TO_TIMESTAMP_NTZ('2026-07-02 15:46:00')),
  ('TXN-3032', 'Q3-2026', 'APAC', 'Platform', 107500.00, TO_TIMESTAMP_NTZ('2026-07-08 12:12:00')),
  ('TXN-3033', 'Q3-2026', 'LATAM', 'Services', 164000.00, TO_TIMESTAMP_NTZ('2026-07-14 11:17:00')),
  ('TXN-3034', 'Q3-2026', 'LATAM', 'Services', 87100.00, TO_TIMESTAMP_NTZ('2026-07-03 16:51:00')),
  ('TXN-3035', 'Q3-2026', 'NA', 'Platform', 109500.00, TO_TIMESTAMP_NTZ('2026-07-18 09:05:00')),
  ('TXN-3036', 'Q3-2026', 'EMEA', 'Services', 145400.00, TO_TIMESTAMP_NTZ('2026-07-14 16:30:00')),
  ('TXN-3037', 'Q3-2026', 'EMEA', 'Add-ons', 118100.00, TO_TIMESTAMP_NTZ('2026-07-02 11:24:00')),
  ('TXN-3038', 'Q3-2026', 'NA', 'Add-ons', 149600.00, TO_TIMESTAMP_NTZ('2026-07-09 16:18:00')),
  ('TXN-3039', 'Q3-2026', 'LATAM', 'Add-ons', 112800.00, TO_TIMESTAMP_NTZ('2026-07-05 12:18:00')),
  ('TXN-3040', 'Q3-2026', 'EMEA', 'Platform', 129300.00, TO_TIMESTAMP_NTZ('2026-07-19 17:03:00')),
  ('TXN-3041', 'Q3-2026', 'APAC', 'Platform', 44000.00, TO_TIMESTAMP_NTZ('2026-07-02 16:32:00')),
  ('TXN-3042', 'Q3-2026', 'EMEA', 'Platform', 67600.00, TO_TIMESTAMP_NTZ('2026-07-17 10:54:00')),
  ('TXN-3043', 'Q3-2026', 'EMEA', 'Platform', 75500.00, TO_TIMESTAMP_NTZ('2026-07-20 10:43:00')),
  ('TXN-3044', 'Q3-2026', 'EMEA', 'Add-ons', 48400.00, TO_TIMESTAMP_NTZ('2026-07-04 12:37:00')),
  ('TXN-3045', 'Q3-2026', 'NA', 'Platform', 68200.00, TO_TIMESTAMP_NTZ('2026-07-14 17:20:00')),
  ('TXN-3046', 'Q3-2026', 'APAC', 'Services', 51100.00, TO_TIMESTAMP_NTZ('2026-07-11 12:16:00')),
  ('TXN-3047', 'Q3-2026', 'LATAM', 'Services', 74000.00, TO_TIMESTAMP_NTZ('2026-07-10 16:20:00')),
  ('TXN-3048', 'Q3-2026', 'NA', 'Platform', 120300.00, TO_TIMESTAMP_NTZ('2026-07-15 10:04:00')),
  ('TXN-3049', 'Q3-2026', 'EMEA', 'Support', 85300.00, TO_TIMESTAMP_NTZ('2026-07-05 14:56:00'));

-- Sanity check: should read exactly 4,820,000.00
SELECT SUM(amount) AS total_q3_revenue, COUNT(*) AS row_count
FROM REVENUE_LIVE_ICEBERG;

-- The materialized copy's cutoff was 2026-07-21T02:00:00Z (see seed_zero_copy_demo.py).
-- This confirms which rows explain the drift — revenue recorded *after* that cutoff,
-- which the nightly-synced copy never picked up.
SELECT SUM(amount) AS revenue_missed_by_the_copy, COUNT(*) AS transactions_since_last_sync
FROM REVENUE_LIVE_ICEBERG
WHERE recorded_at > '2026-07-21 02:00:00';

-- ---------------------------------------------------------------------------
-- 4. Dedicated read-only role + user for DataHub ingestion
--    (avoid ingesting with your admin account)
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS DATAHUB_INGEST_ROLE;

GRANT USAGE ON WAREHOUSE ZCS_WH TO ROLE DATAHUB_INGEST_ROLE;
GRANT USAGE ON DATABASE FINANCE_DB TO ROLE DATAHUB_INGEST_ROLE;
GRANT USAGE ON SCHEMA FINANCE_DB.PUBLIC TO ROLE DATAHUB_INGEST_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA FINANCE_DB.PUBLIC TO ROLE DATAHUB_INGEST_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA FINANCE_DB.PUBLIC TO ROLE DATAHUB_INGEST_ROLE;

-- Create the ingestion user. Replace the password below before running —
-- use a real password only you know; it goes straight into your local .env,
-- never pasted back into chat.
CREATE USER IF NOT EXISTS DATAHUB_INGEST_USER
  PASSWORD = 'REPLACE_WITH_A_REAL_PASSWORD'
  DEFAULT_ROLE = DATAHUB_INGEST_ROLE
  DEFAULT_WAREHOUSE = ZCS_WH
  MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE DATAHUB_INGEST_ROLE TO USER DATAHUB_INGEST_USER;

-- ---------------------------------------------------------------------------
-- 5. Find your account identifier for the DataHub recipe (Step 4 of the plan)
-- ---------------------------------------------------------------------------
SELECT CURRENT_ACCOUNT(), CURRENT_REGION();
