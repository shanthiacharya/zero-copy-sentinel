"""
The GOAL — the one thing you change per hackathon challenge.

agent.py (the skeleton) stays the same. To target a different challenge, swap the
GOAL string below (and adjust SYSTEM_PROMPT if the behavior changes). Commented
examples for the other three challenges are at the bottom.
"""

# How the agent should behave, regardless of the specific goal.
SYSTEM_PROMPT = """You are a DataHub catalog steward — an agent that keeps a data
catalog trustworthy.

Always work in this order:
1. READ context from DataHub first (search, schema, lineage, ownership) before doing
   anything. Never act on a dataset you haven't inspected.
2. Take concrete, useful actions for each real problem you find — don't stop after the
   first one if there's more than one kind of drift to check for.
3. WRITE each result back to DataHub so the next person or agent inherits it.
4. REPORT, in plain English, everything you touched, what you found, and what you
   changed.

Be conservative: only act on clearly-justified findings, backed by data you actually
read. Do not guess at URNs — find them via search first."""


# --- Zero-Copy Sentinel: catch dashboards built on stale or schema-broken copies ------
GOAL = """Run BOTH of the following checks. They are independent — do both, not just
whichever you find first.

CHECK 1 — VALUE DRIFT
Search DataHub for dashboards. For each one, trace its lineage upstream to the
dataset(s) it is actually built on. For each of those datasets, check whether IT has a
further upstream dataset tagged `zero-copy` (a live source of truth) versus itself being
a `materialized-copy`.

When a dashboard sits on a `materialized-copy` dataset that has a `zero-copy` upstream:
compare the two datasets' `current_quarter_revenue` and freshness custom properties
(`last_updated` on the zero-copy source, `last_synced` on the copy). If the values
differ, this dashboard is showing stale numbers.

Take action: tag the copied dataset `stale-copy-risk`, and update its description to
state the drift plainly — the copy's stale number, the live source's current number,
and how out of sync it is. Then call notify_slack with a summary of the drift.

CHECK 2 — SCHEMA DRIFT (column-level lineage)
For each `materialized-copy` dataset you find (from check 1), look at its column-level
(fine-grained) upstream lineage — use get_lineage with the column set, for each of its
columns, to see which upstream column(s) each one claims to be derived from. For every
upstream column referenced that way, check whether that column still exists in the
zero-copy source's CURRENT schema (use list_schema_fields on the upstream dataset — do
not assume, actually look).

If a column-level lineage edge points at an upstream column that is no longer in the
source's current schema, that is schema drift: a downstream field is derived from
something that was silently dropped upstream.

Take action: call raise_incident on the downstream (copy) dataset — incident_type
DATA_SCHEMA, with a title and description naming the missing upstream column, the
downstream column that depends on it, and both dataset URNs. Then call notify_slack
with a summary so the owner is alerted outside DataHub too.

REPORT, for each check: which dashboard/dataset(s) you looked at, what you found (or
that you found nothing wrong — say so explicitly), the exact evidence (numbers, column
names, URNs), and exactly what you wrote back to DataHub and Slack."""


# --- Swap GOAL above for one of these to target another challenge ---------------------
#
# Challenge 2 — Metadata-Aware Code Generation:
#   "Read the schema and lineage of mart_billing in DataHub, then generate a dbt model
#    that builds it from its upstream staging table. Use the real column names."
#
# Challenge 3 — Production ML Agents:
#   "Trace the ML lineage from training data to deployed models. If an upstream dataset
#    changed, flag any downstream mlModel as `at-risk` and note which deployment is
#    affected."
#
# Challenge 4 — Open / Wildcard:
#   "<your idea — the skeleton and DataHub tools stay the same>"
