"""
Seed data for the zero-copy sentinel demo.

Creates two financial datasets that represent the same underlying number:
  - a LIVE dataset  -> zero-copy (e.g. a Snowflake/Iceberg table queried directly,
                        no duplication). This is the source of truth.
  - a COPY dataset  -> a materialized/ETL'd snapshot that a dashboard was built on.
                        It drifts from the live number between syncs.

...plus a dashboard wired to the COPY, and lineage LIVE -> COPY, so DataHub's
lineage graph shows exactly how the dashboard's number went stale. agent.py's
sentinel then reads this graph, compares the two numbers, and flags the gap.

Two modes, so this works whether or not your Snowflake trial comes through in time:

  --mode seeded     (default) fabricates BOTH datasets locally. No external
                     dependencies beyond a running DataHub instance.

  --mode snowflake  use once you have a real Snowflake Iceberg table ingested into
                     DataHub (via `datahub ingest -c <snowflake_recipe>.yml`). Set
                     LIVE_DATASET_URN below to that table's real URN (copy it from
                     the DataHub UI). This script then leaves the live dataset's
                     schema alone and only stamps it with the comparison numbers,
                     then creates the copy + dashboard + lineage as before.

Run once before `python agent.py`. Safe to re-run — everything is an upsert.
"""

import argparse

from datahub.sdk import DataHubClient, Dataset, Dashboard, Tag
from datahub.metadata.urns import ContainerUrn, DatasetUrn, TagUrn

# --- Config: edit these for your demo ---------------------------------------

# Only used in --mode snowflake. Copy the real URN from the DataHub UI after
# ingesting your Snowflake Iceberg table.
LIVE_DATASET_URN = (
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,"
    "finance_db.public.revenue_live_iceberg,PROD)"
)

LIVE_VALUE = "$4.82M"  # the true, current number (zero-copy source)
COPY_VALUE = "$4.65M"  # what the stale materialized copy still shows
LIVE_LAST_UPDATED = "2026-07-23T09:00:00Z"  # "now" — the live source's last write
COPY_LAST_SYNCED = "2026-07-21T02:00:00Z"  # ~55h behind LIVE_LAST_UPDATED

COPY_DATASET_NAME = "finance_db.public.revenue_dashboard_extract"
DASHBOARD_NAME = "q3_financial_summary"

# The real PUBLIC schema container that the actual Snowflake ingestion of
# revenue_live_iceberg created. Attaching the copy dataset to this SAME container
# entity (instead of letting DataHub infer a path from its dotted name string) is
# what makes both datasets land under one FINANCE_DB folder in the browse tree —
# matching name text alone isn't enough, since a string-inferred path and a
# real-container path are different node types to DataHub's browse tree.
LIVE_SCHEMA_CONTAINER_URN = "urn:li:container:86f5c7c989d95ef73920e03938a2c4e4"

# Tags used by this demo AND by the sentinel's write-back in goal.py.
# DataHub won't apply a tag that doesn't exist yet, so we create all of them here.
TAGS = ["zero-copy", "materialized-copy", "finance", "stale-copy-risk"]

# -----------------------------------------------------------------------------


def seed_tags(client) -> None:
    for name in TAGS:
        client.entities.upsert(Tag(name=name))


def seed_live_dataset(client) -> str:
    """Fabricate the live zero-copy Iceberg table. Returns its URN."""
    dataset = Dataset(
        platform="snowflake",
        name="finance_db.public.revenue_live_iceberg",
        description=(
            "Live Apache Iceberg table queried directly by Snowflake/Workday — "
            "zero-copy, no duplication. This is the source of truth for revenue."
        ),
        schema=[
            ("quarter", "varchar(10)", "Fiscal quarter, e.g. Q3-2026"),
            ("revenue", "decimal(18,2)", "Total recognized revenue for the quarter"),
            ("last_updated", "timestamp", "Last write to the underlying Iceberg table"),
        ],
        custom_properties={
            "table_format": "iceberg",
            "zero_copy": "true",
            "current_quarter_revenue": LIVE_VALUE,
            "last_updated": LIVE_LAST_UPDATED,
        },
        tags=[TagUrn("zero-copy")],
    )
    client.entities.upsert(dataset)
    return str(dataset.urn)


def enrich_real_live_dataset(client, urn: str) -> None:
    """Stamp a real, already-ingested Snowflake dataset with this demo's
    comparison numbers and the zero-copy tag, without touching its real
    (ingested) schema."""
    dataset = client.entities.get(DatasetUrn.from_string(urn))
    dataset.set_custom_properties(
        {
            "table_format": "iceberg",
            "zero_copy": "true",
            "current_quarter_revenue": LIVE_VALUE,
            "last_updated": LIVE_LAST_UPDATED,
        }
    )
    dataset.add_tag(TagUrn("zero-copy"))
    client.entities.update(dataset)


def seed_copy_dataset(client) -> str:
    container = client.entities.get(ContainerUrn.from_string(LIVE_SCHEMA_CONTAINER_URN))
    dataset = Dataset(
        platform="snowflake",
        name=COPY_DATASET_NAME,
        parent_container=container,
        description=(
            "Nightly-ETL'd snapshot of revenue_live_iceberg, materialized for "
            "dashboard performance. NOT zero-copy — drifts from the source "
            "between syncs."
        ),
        schema=[
            ("quarter", "varchar(10)", "Fiscal quarter, e.g. Q3-2026"),
            ("revenue", "decimal(18,2)", "Revenue as of the last sync"),
        ],
        custom_properties={
            "table_format": "materialized_copy",
            "zero_copy": "false",
            "current_quarter_revenue": COPY_VALUE,
            "last_synced": COPY_LAST_SYNCED,
        },
        tags=[TagUrn("materialized-copy")],
    )
    client.entities.upsert(dataset)
    return str(dataset.urn)


def seed_dashboard(client, copy_urn: str) -> str:
    dashboard = Dashboard(
        name=DASHBOARD_NAME,
        platform="looker",
        description="Executive Q3 financial summary dashboard.",
        input_datasets=[copy_urn],
        tags=[TagUrn("finance")],
    )
    client.entities.upsert(dashboard)
    return str(dashboard.urn)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["seeded", "snowflake"], default="seeded")
    args = parser.parse_args()

    client = DataHubClient.from_env()

    seed_tags(client)

    if args.mode == "seeded":
        live_urn = seed_live_dataset(client)
    else:
        enrich_real_live_dataset(client, LIVE_DATASET_URN)
        live_urn = LIVE_DATASET_URN

    copy_urn = seed_copy_dataset(client)
    client.lineage.add_lineage(
        upstream=live_urn,
        downstream=copy_urn,
        # Column-level lineage: the copy's "revenue" field was computed using
        # the live table's discount_pct column. When discount_pct is dropped
        # (schema-drift scenario), this edge points at a column that no
        # longer exists in the upstream schema.
        column_lineage={"revenue": ["discount_pct"]},
    )
    dashboard_urn = seed_dashboard(client, copy_urn)

    print(f"Mode:      {args.mode}")
    print(f"Live (zero-copy):    {live_urn}")
    print(f"Copy (materialized): {copy_urn}")
    print(f"Dashboard:           {dashboard_urn}")
    print("\nSeed complete. Refresh the DataHub UI to see the lineage graph, then run "
          "`python agent.py`.")


if __name__ == "__main__":
    main()
