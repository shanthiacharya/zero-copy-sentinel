"""
Custom DataHub tools not covered by the Agent Context Kit.

The kit (datahub_agent_context) ships tag/owner/description/glossary mutations
but has no incident-creation tool, and nothing for external notifications.
These follow the kit's own pattern (see datahub_agent_context.mcp_tools.tags):
a plain function that pulls the active DataHubGraph from context and calls
execute_graphql, wrapped into a LangChain tool the same way build_langchain_tools
wraps the built-in ones.

The `raiseIncident` mutation shape below was confirmed via live GraphQL
introspection against this project's DataHub instance, not assumed from docs.
"""

import logging
import os
from typing import List, Literal, Optional

import requests
from datahub_agent_context.context import get_graph
from datahub_agent_context.mcp_tools.base import execute_graphql
from datahub_agent_context.utils import create_context_wrapper

try:
    from langchain_core.tools import tool
    from langchain_core.tools.base import BaseTool
except ImportError as e:
    raise ImportError(
        "langchain-core is required for these tools. "
        "Install with: pip install 'datahub-agent-context[langchain]'"
    ) from e

logger = logging.getLogger(__name__)

IncidentType = Literal[
    "FRESHNESS", "VOLUME", "FIELD", "SQL", "DATA_SCHEMA", "OPERATIONAL", "CUSTOM"
]
IncidentPriority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def raise_incident(
    resource_urn: str,
    title: str,
    description: str,
    incident_type: IncidentType = "DATA_SCHEMA",
    priority: Optional[IncidentPriority] = None,
) -> dict:
    """Raise a DataHub Incident on an entity to flag a problem that needs attention.

    Use this for issues more serious than a tag or description edit — e.g. a
    downstream dataset whose lineage now points at a column that no longer
    exists upstream (schema drift), or another correctness problem that should
    show up in DataHub's Incidents tab and page the asset's owner.

    Args:
        resource_urn: URN of the entity the incident is about (e.g. a dataset URN).
        title: Short incident title.
        description: Full explanation — what broke, and the evidence for it.
        incident_type: One of FRESHNESS, VOLUME, FIELD, SQL, DATA_SCHEMA,
            OPERATIONAL, CUSTOM. Defaults to DATA_SCHEMA.
        priority: Optional one of LOW, MEDIUM, HIGH, CRITICAL.

    Returns:
        Dictionary with:
        - success: Boolean indicating if the incident was created
        - incident_urn: URN of the newly created incident, if successful
        - message: Human-readable result
    """
    graph = get_graph()

    mutation = """
        mutation raiseIncident($input: RaiseIncidentInput!) {
            raiseIncident(input: $input)
        }
    """
    input_payload: dict = {
        "type": incident_type,
        "title": title,
        "description": description,
        "resourceUrn": resource_urn,
    }
    if priority:
        input_payload["priority"] = priority

    try:
        result = execute_graphql(
            graph,
            query=mutation,
            variables={"input": input_payload},
            operation_name="raiseIncident",
        )
        incident_urn = result.get("raiseIncident")
        if incident_urn:
            return {
                "success": True,
                "incident_urn": incident_urn,
                "message": f"Raised incident {incident_urn} on {resource_urn}",
            }
        raise RuntimeError("raiseIncident returned no incident URN")
    except Exception as e:
        raise RuntimeError(f"Failed to raise incident on {resource_urn}: {e}") from e


def notify_slack(message: str, related_urns: Optional[List[str]] = None) -> dict:
    """Post a notification to the team's Slack channel via incoming webhook.

    Use this to alert a human when the sentinel finds something worth acting
    on — e.g. value drift between a zero-copy source and a stale copy, or a
    schema-drift incident. Reads the webhook URL from the SLACK_WEBHOOK_URL
    environment variable; if it isn't set, this fails loudly rather than
    silently doing nothing.

    Args:
        message: The alert text to post.
        related_urns: Optional list of DataHub URNs to include for context.

    Returns:
        Dictionary with:
        - success: Boolean indicating if the message was posted
        - message: Human-readable result
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError(
            "SLACK_WEBHOOK_URL is not set in the environment — cannot send "
            "the Slack notification. Add it to .env."
        )

    text = message
    if related_urns:
        text += "\n\n" + "\n".join(f"• `{urn}`" for urn in related_urns)

    resp = requests.post(webhook_url, json={"text": text}, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Slack webhook returned {resp.status_code}: {resp.text}"
        )

    return {"success": True, "message": "Posted notification to Slack"}


def build_custom_tools(client) -> List[BaseTool]:
    """Build LangChain tools for the custom DataHub + Slack additions.

    Mirrors datahub_agent_context.langchain_tools.build_langchain_tools's
    wrapping pattern so these tools plug into the same create_react_agent call.
    """
    return [
        tool(create_context_wrapper(raise_incident, client)),
        tool(notify_slack),
    ]
