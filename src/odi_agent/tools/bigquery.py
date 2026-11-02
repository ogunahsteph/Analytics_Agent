"""BigQuery query tool exposed to the agent."""

import json
from uuid import uuid4

from google.cloud import bigquery
from langchain.tools import tool

from odi_agent.auth import get_google_credentials
from odi_agent.config import (
    PROJECT_ID,
    TABLE_ID,
    MAX_BYTES_BILLED,
    MAX_RESULT_ROWS,
)
from odi_agent.state.results import query_results


@tool
def query_bigquery(sql: str) -> dict:
    """Execute a read-only SELECT query on the allowed transaction table.

    Use bounded ingestion partition filters and the agreed deduplication rule.
    Returns a result ID, row count, and at most three preview rows.
    Full results remain available for Google Sheets export.
    """
    try:
        client = bigquery.Client(
            project=PROJECT_ID,
            credentials=get_google_credentials(),
        )

        # Validate the query and estimate scanning without executing it.
        estimate = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False,
            ),
        )

        if estimate.statement_type != "SELECT":
            return {"error": "Only a single SELECT query is allowed."}

        referenced_tables = {
            f"{table.project}.{table.dataset_id}.{table.table_id}"
            for table in (estimate.referenced_tables or [])
        }

        if referenced_tables != {TABLE_ID}:
            return {"error": f"Query must read only {TABLE_ID}."}

        estimated_bytes = estimate.total_bytes_processed

        if estimated_bytes is None:
            return {
                "error": "Could not estimate query size; execution blocked."
            }

        if estimated_bytes > MAX_BYTES_BILLED:
            return {
                "error": (
                    f"Query exceeds the "
                    f"{MAX_BYTES_BILLED / 1_000_000_000:g} GB allowance. "
                    "Narrow the query."
                ),
                "estimated_gb": round(
                    estimated_bytes / 1_000_000_000, 3
                ),
            }

        # Enforce the configured allowance during execution.
        job = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                maximum_bytes_billed=MAX_BYTES_BILLED,
            ),
        )
        rows = job.result()

        if rows.total_rows > MAX_RESULT_ROWS:
            return {
                "error": (
                    f"Result exceeds {MAX_RESULT_ROWS:,} rows. "
                    "Aggregate or narrow the query."
                ),
                "row_count": rows.total_rows,
                "job_id": job.job_id,
            }

        df = rows.to_dataframe(create_bqstorage_client=False)
        result_id = uuid4().hex

        query_results[result_id] = {
            "data": df,
            "sql": sql,
            "job_id": job.job_id,
        }

        # Small preview only; full results stay outside model context.
        preview = json.loads(
            df.head(3).to_json(
                orient="records",
                date_format="iso",
            )
        )

        return {
            "result_id": result_id,
            "row_count": len(df),
            "columns": list(df.columns),
            "preview_rows": preview,
            "preview_is_partial": len(df) > 3,
            "bytes_processed": job.total_bytes_processed,
        }

    except Exception as exc:
        return {"error": str(exc)}