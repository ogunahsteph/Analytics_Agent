"""Application configuration."""

import os
# Tbale settings
PROJECT_ID = os.getenv("ODI_PROJECT_ID", "southwell-infra")

TABLE_ID = os.getenv(
    "ODI_TABLE_ID",
    "southwell-infra.Odibets_Raw.odibets_transaction_new",
)

WITHDRAWAL_DLR = os.getenv(
    "ODI_WITHDRAWAL_DLR",
    "southwell-infra.Odibets_Raw.odibets_withdrawal_dlr",
)

PROFILE_TABLE_ID = os.getenv(
    "ODI_PROFILE_TABLE_ID",
    "southwell-infra.Odibets_Raw.odibets_profile",
)
DEPOSIT_TABLE_ID = os.getenv(
    "ODI_DEPOSIT_TABLE_ID",
    "southwell-infra.Odibets_Raw.odibets_mpesa_transaction",
)
BET_TABLE_ID = os.getenv(
    "ODI_BET_TABLE_ID",
    "southwell-infra.matchesodi.bet",
)

BET_SLIP_TABLE_ID = os.getenv(
    "ODI_BET_SLIP_TABLE_ID",
    "southwell-infra.matchesodi.bet_slip",
)
MATCH_TABLE_ID = os.getenv(
    "ODI_MATCH_TABLE_ID",
    "southwell-infra.matches.odi_bets_matche",
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

