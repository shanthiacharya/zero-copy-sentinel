#!/usr/bin/env bash
# Re-ingest the real Snowflake table into DataHub, with .env variables actually
# exported into the shell first. `datahub ingest` resolves ${SNOWFLAKE_ACCOUNT}
# etc. in snowflake_ingest.yml from real environment variables, not from a
# python-dotenv load — so running the raw `datahub ingest` command in a plain
# terminal fails with `expandvars.UnboundVariable` unless .env has been sourced
# first. This script does that automatically, every time, regardless of shell
# state.
set -euo pipefail
cd "$(dirname "$0")"

source .venv/bin/activate
set -a
source .env
set +a

datahub ingest -c snowflake_ingest.yml
