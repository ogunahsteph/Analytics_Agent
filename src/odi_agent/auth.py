"""Google authentication helpers."""

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request

from odi_agent.config import SHEETS_SERVICE_ACCOUNT


def get_google_credentials():
    """Obtain the credentials available to this application."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return credentials


def get_sheets_credentials():
    """Obtain short-lived credentials for the Sheets service account."""
    credentials = impersonated_credentials.Credentials(
        source_credentials=get_google_credentials(),
        target_principal=SHEETS_SERVICE_ACCOUNT,
        target_scopes=[
            "https://www.googleapis.com/auth/spreadsheets"
        ],
        lifetime=3600,
    )

    credentials.refresh(Request())
    return credentials