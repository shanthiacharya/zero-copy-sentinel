"""
Reset the Zero-Copy Sentinel demo dataset back to its pristine, un-flagged state.
Run this before every recording take — including right before the FINAL take,
since a dry run will dirty the state again.

Undoes exactly what the agent's write-back does: removes the stale-copy-risk tag
and restores the original description. Uses the same verified GraphQL mutations
as the agent itself, so "reset" and "detect" are symmetric.
"""

import os
import subprocess

import requests
from dotenv import load_dotenv

load_dotenv()

GMS_URL = os.environ["DATAHUB_GMS_URL"]
TOKEN = os.environ["DATAHUB_GMS_TOKEN"]

COPY_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,finance_db.public.revenue_dashboard_extract,PROD)"

ORIGINAL_DESCRIPTION = (
    "Nightly-ETL'd snapshot of revenue_live_iceberg, materialized for dashboard "
    "performance. NOT zero-copy — drifts from the source between syncs."
)


def _graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        f"{GMS_URL}/api/graphql",
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


REMOVE_TAG = """
mutation removeTag($tagUrn: String!, $resourceUrn: String!) {
  removeTag(input: { tagUrn: $tagUrn, resourceUrn: $resourceUrn })
}
"""

UPDATE_DESCRIPTION = """
mutation updateDescription($description: String!, $resourceUrn: String!) {
  updateDescription(input: { description: $description, resourceUrn: $resourceUrn })
}
"""

# DataHub's GraphQL schema has no deleteIncident mutation (only raiseIncident /
# updateIncidentStatus / updateIncident) — confirmed via introspection. So a true
# clean slate needs the CLI's generic hard-delete instead, which works on any URN.
LIST_INCIDENTS = """
query listIncidents($urn: String!) {
  dataset(urn: $urn) {
    incidents(state: null, start: 0, count: 100) {
      incidents { urn }
    }
  }
}
"""


def _delete_incidents(resource_urn: str) -> None:
    data = _graphql(LIST_INCIDENTS, {"urn": resource_urn})
    incidents = data["dataset"]["incidents"]["incidents"]
    if not incidents:
        print("No incidents to delete.")
        return
    for inc in incidents:
        urn = inc["urn"]
        subprocess.run(
            ["datahub", "delete", "--urn", urn, "--hard", "-f"],
            check=True,
            capture_output=True,
        )
        print(f"Hard-deleted incident: {urn}")


def main() -> None:
    result = _graphql(
        REMOVE_TAG, {"tagUrn": "urn:li:tag:stale-copy-risk", "resourceUrn": COPY_URN}
    )
    print("Removed stale-copy-risk tag:", result["removeTag"])

    result = _graphql(
        UPDATE_DESCRIPTION,
        {"description": ORIGINAL_DESCRIPTION, "resourceUrn": COPY_URN},
    )
    print("Restored original description:", result["updateDescription"])

    _delete_incidents(COPY_URN)

    print("\nDemo state reset. Verify in the DataHub UI or re-run the agent to confirm.")


if __name__ == "__main__":
    main()
