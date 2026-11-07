
# """BigQuery query tool exposed to the agent."""

# import json
# from uuid import uuid4

# from google.cloud import bigquery
# from langchain.tools import tool

# from odi_agent.auth import get_google_credentials
# from odi_agent.config import (
#     PROJECT_ID,
#     TABLE_ID,
#     WITHDRAWAL_DLR,
#     PROFILE_TABLE_ID,
#     DEPOSIT_TABLE_ID,
#     BET_TABLE_ID,
#     BET_SLIP_TABLE_ID,
#     MATCH_TABLE_ID,
#     MAX_BYTES_BILLED,
#     MAX_RESULT_ROWS,
# )
# from odi_agent.state.results import query_results


# # Add future approved table settings here and to the imports above.
# # The validation logic below works for individual tables and joins.
# ALLOWED_TABLES = {
#     TABLE_ID,
#     WITHDRAWAL_DLR,
#     PROFILE_TABLE_ID,
#     DEPOSIT_TABLE_ID,
#     BET_TABLE_ID,
#     BET_SLIP_TABLE_ID,
#     MATCH_TABLE_ID,
# }


# @tool
# def query_bigquery(sql: str) -> dict:
#     """Execute a read-only SELECT query on approved business tables.

#     Queries may use one approved table or join approved tables.
#     Follow each table's documented partitioning and deduplication rules.
#     Do not assume every table supports _PARTITIONTIME.
#     Returns a result ID, row count, and at most three preview rows.
#     Full results remain available for Google Sheets export.
#     """
#     try:
#         client = bigquery.Client(
#             project=PROJECT_ID,
#             credentials=get_google_credentials(),
#         )

#         # Validate SQL and estimate scanning without executing it.
#         estimate = client.query(
#             sql,
#             job_config=bigquery.QueryJobConfig(
#                 dry_run=True,
#                 use_query_cache=False,
#             ),
#         )

#         if estimate.statement_type != "SELECT":
#             return {"error": "Only a single SELECT query is allowed."}

#         referenced_tables = {
#             f"{table.project}.{table.dataset_id}.{table.table_id}"
#             for table in (estimate.referenced_tables or [])
#         }

#         if not referenced_tables:
#             return {
#                 "error": "Query must reference an approved business table."
#             }

#         # Accept any combination of approved tables.
#         disallowed_tables = referenced_tables - ALLOWED_TABLES

#         if disallowed_tables:
#             return {
#                 "error": "Query references tables that are not approved.",
#                 "disallowed_tables": sorted(disallowed_tables),
#                 "allowed_tables": sorted(ALLOWED_TABLES),
#             }

#         estimated_bytes = estimate.total_bytes_processed

#         if estimated_bytes is None:
#             return {
#                 "error": "Could not estimate query size; execution blocked."
#             }

#         if estimated_bytes > MAX_BYTES_BILLED:
#             return {
#                 "error": (
#                     f"Query exceeds the "
#                     f"{MAX_BYTES_BILLED / 1_000_000_000:g} GB allowance. "
#                     "Narrow the query."
#                 ),
#                 "estimated_gb": round(
#                     estimated_bytes / 1_000_000_000, 3
#                 ),
#             }

#         # Enforce the configured allowance during execution.
#         job = client.query(
#             sql,
#             job_config=bigquery.QueryJobConfig(
#                 maximum_bytes_billed=MAX_BYTES_BILLED,
#             ),
#         )
#         rows = job.result()

#         if rows.total_rows > MAX_RESULT_ROWS:
#             return {
#                 "error": (
#                     f"Result exceeds {MAX_RESULT_ROWS:,} rows. "
#                     "Aggregate or narrow the query."
#                 ),
#                 "row_count": rows.total_rows,
#                 "job_id": job.job_id,
#             }

#         df = rows.to_dataframe(create_bqstorage_client=False)
#         result_id = uuid4().hex

#         query_results[result_id] = {
#             "data": df,
#             "sql": sql,
#             "job_id": job.job_id,
#         }

#         # Full results stay in Python; only a small preview reaches the model.
#         preview = json.loads(
#             df.head(3).to_json(
#                 orient="records",
#                 date_format="iso",
#             )
#         )

#         return {
#             "result_id": result_id,
#             "row_count": len(df),
#             "columns": list(df.columns),
#             "preview_rows": preview,
#             "preview_is_partial": len(df) > 3,
#             "bytes_processed": job.total_bytes_processed,
#         }

#     except Exception as exc:
#         return {"error": str(exc)}

"""BigQuery tool with direct terminal approval for over-limit queries."""

import json
from uuid import uuid4

from google.cloud import bigquery
from langchain.tools import tool

from odi_agent.auth import get_google_credentials
from odi_agent.config import (
    PROJECT_ID,
    TABLE_ID,
    WITHDRAWAL_DLR,
    PROFILE_TABLE_ID,
    DEPOSIT_TABLE_ID,
    BET_TABLE_ID,
    BET_SLIP_TABLE_ID,
    MATCH_TABLE_ID,
    MAX_BYTES_BILLED,
    MAX_RESULT_ROWS,
)
from odi_agent.state.results import query_results


# Add future approved tables here and import their settings above.
# The validation below supports both individual tables and joins.
ALLOWED_TABLES = {
    TABLE_ID,
    WITHDRAWAL_DLR,
    PROFILE_TABLE_ID,
    DEPOSIT_TABLE_ID,
    BET_TABLE_ID,
    BET_SLIP_TABLE_ID,
    MATCH_TABLE_ID,
}


def request_scan_approval(sql: str, estimated_bytes: int) -> int | None:
    """Ask the terminal user to approve this exact query and billing cap."""

    # NEW: Round up to a whole decimal GB so the approved cap is clear.
    # The estimate may change before execution; BigQuery still enforces
    # this cap and will reject execution if it requires more.
    one_gb = 1_000_000_000
    approved_cap = (
        (estimated_bytes + one_gb - 1) // one_gb
    ) * one_gb

    print("\n--- BigQuery approval required ---")
    print(f"Estimated scan: {estimated_bytes / one_gb:,.3f} GB")
    print(f"Default allowance: {MAX_BYTES_BILLED / one_gb:g} GB")
    print(f"Proposed maximum billed: {approved_cap / one_gb:g} GB")
    print("This is a scan allowance, not a confirmed monetary charge.")
    print("\nSQL awaiting approval:\n")
    print(sql)

    try:
        # NEW: Approval comes directly from you through the terminal.
        # The model cannot approve by supplying a tool argument.
        answer = input(
            "\nType 'approve' to execute this query; "
            "anything else cancels: "
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nQuery cancelled before execution.")
        return None

    if answer != "approve":
        print("Query cancelled before execution.")
        return None

    # NEW: Return a cap for this call only.
    # MAX_BYTES_BILLED remains unchanged for subsequent queries.
    return approved_cap


@tool
def query_bigquery(sql: str) -> dict:
    """Execute a read-only SELECT query on approved business tables.

    Queries may use one approved table or join approved tables.
    Follow each table's documented partitioning and deduplication rules.
    Do not assume every table supports _PARTITIONTIME.

    Queries above the configured scan allowance require direct approval
    from the terminal user before execution. The tool handles that approval.
    If the user rejects execution, stop and report the cancellation;
    do not retry the same request through another query.

    Returns a result ID, row count, and at most three preview rows.
    Full results remain available for Google Sheets export.
    """
    try:
        client = bigquery.Client(
            project=PROJECT_ID,
            credentials=get_google_credentials(),
        )

        # Validate SQL and estimate scanning without executing it.
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

        if not referenced_tables:
            return {
                "error": "Query must reference an approved business table."
            }

        disallowed_tables = referenced_tables - ALLOWED_TABLES

        if disallowed_tables:
            return {
                "error": "Query references tables that are not approved.",
                "disallowed_tables": sorted(disallowed_tables),
                "allowed_tables": sorted(ALLOWED_TABLES),
            }

        estimated_bytes = estimate.total_bytes_processed

        if estimated_bytes is None:
            return {
                "error": "Could not estimate query size; execution blocked."
            }

        # NEW: Each query starts with the ordinary configured allowance.
        execution_cap = MAX_BYTES_BILLED
        user_approved = False

        if estimated_bytes > MAX_BYTES_BILLED:
            # NEW: Pause before execution and show the exact SQL and cap.
            # The SQL passed to execution below is the same SQL displayed.
            execution_cap = request_scan_approval(sql, estimated_bytes)

            if execution_cap is None:
                return {
                    "status": "cancelled",
                    "executed": False,
                    "reason": "The user did not approve the query.",
                    "estimated_gb": round(
                        estimated_bytes / 1_000_000_000, 3
                    ),
                    "instruction": (
                        "Report the cancellation and stop. "
                        "Do not retry or submit an alternative query "
                        "unless the user requests it."
                    ),
                }

            user_approved = True

        # CHANGED: Use the default cap or the cap explicitly approved
        # for this query. Never remove the execution billing limit.
        job = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                maximum_bytes_billed=execution_cap,
            ),
        )
        rows = job.result()

        if rows.total_rows > MAX_RESULT_ROWS:
            return {
                "error": (
                    f"Result exceeds {MAX_RESULT_ROWS:,} rows. "
                    "Aggregate or narrow the query."
                ),
                # NEW: Make clear that the query already ran,
                # even though its result is too large to retain.
                "executed": True,
                "row_count": rows.total_rows,
                "job_id": job.job_id,
                "bytes_processed": job.total_bytes_processed,
            }

        df = rows.to_dataframe(create_bqstorage_client=False)
        result_id = uuid4().hex

        query_results[result_id] = {
            "data": df,
            "sql": sql,
            "job_id": job.job_id,
            # NEW: Retain scan and approval details with the result
            # for later inspection without another BigQuery query.
            "estimated_bytes": estimated_bytes,
            "maximum_bytes_billed": execution_cap,
            "user_approved": user_approved,
            "bytes_processed": job.total_bytes_processed,
            "bytes_billed": job.total_bytes_billed,
        }

        # Full results remain in Python; only three rows reach the model.
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
            # NEW: Processed bytes and billed bytes may differ.
            "bytes_billed": job.total_bytes_billed,
        }

    except Exception as exc:
        return {"error": str(exc)}