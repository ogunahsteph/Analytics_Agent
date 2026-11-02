"""Application configuration."""

import os

PROJECT_ID = os.getenv("ODI_PROJECT_ID", "southwell-infra")

TABLE_ID = os.getenv(
    "ODI_TABLE_ID",
    "southwell-infra.Odibets_Raw.odibets_transaction_new",
)

TIMEZONE = os.getenv("ODI_TIMEZONE", "Africa/Nairobi")
MODEL_PROVIDER = os.getenv("ODI_MODEL_PROVIDER", "gemini_vertex")
LOCATION = os.getenv("ODI_MODEL_LOCATION", "global")
MODEL_ID = os.getenv("ODI_MODEL_ID", "gemini-3.8-flash")

MAX_BYTES_BILLED = int(
    os.getenv("ODI_MAX_BYTES_BILLED", "30000000000")
)
MAX_RESULT_ROWS = int(
    os.getenv("ODI_MAX_RESULT_ROWS", "10000")
)

SHEETS_SERVICE_ACCOUNT = os.getenv(
    "ODI_SHEETS_SERVICE_ACCOUNT",
    "southwell-data-team-sc@southwell-infra.iam.gserviceaccount.com",
)

SPREADSHEET_ID = os.getenv(
    "ODI_SPREADSHEET_ID",
    "19o8EBmTQSwhuPJd0L3rl3-ZttIwkAQ9cVtQBxAVQn2Q",
)

