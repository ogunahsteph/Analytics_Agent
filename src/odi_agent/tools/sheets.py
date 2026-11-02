"""Google Sheets export tool exposed to the agent."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from googleapiclient.discovery import build
from langchain.tools import tool

from odi_agent.auth import get_sheets_credentials
from odi_agent.config import SPREADSHEET_ID, TIMEZONE
from odi_agent.state.results import query_results


def _cell_value(value):
    """Convert a DataFrame value into a Sheets-compatible value."""
    if pd.isna(value):
        return ""
    if isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


@tool
def export_to_sheets(result_id: str) -> dict:
    """Export a saved BigQuery result to a new tab and return its URL.

    Use the exact result_id returned by query_bigquery.
    """
    if result_id not in query_results:
        return {
            "error": "Unknown result_id. Run the BigQuery query first."
        }

    saved = query_results[result_id]
    df = saved["data"]

    if "sheet_url" in saved:
        return {
            "url": saved["sheet_url"],
            "row_count": len(df),
        }

    if len(df.columns) == 0:
        return {"error": "Result has no columns to export."}

    if "sheet_tab_name" not in saved:
        timestamp = datetime.now(
            ZoneInfo(TIMEZONE)
        ).strftime("%Y%m%d_%H%M%S")

        saved["sheet_tab_name"] = (
            f"Analysis_{timestamp}_{result_id[:6]}"
        )

    title = saved["sheet_tab_name"]

    try:
        client = build(
            "sheets",
            "v4",
            credentials=get_sheets_credentials(),
            cache_discovery=False,
        )

        values = [[str(column) for column in df.columns]]
        values.extend(
            [_cell_value(value) for value in row]
            for row in df.itertuples(index=False, name=None)
        )

        # Reuse a tab created during an earlier interrupted attempt.
        workbook = client.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID,
            fields="sheets.properties",
        ).execute()

        properties = next(
            (
                sheet["properties"]
                for sheet in workbook.get("sheets", [])
                if sheet["properties"]["title"] == title
            ),
            None,
        )

        if properties is None:
            response = client.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    "requests": [{
                        "addSheet": {
                            "properties": {
                                "title": title,
                                "gridProperties": {
                                    "rowCount": max(len(values), 100),
                                    "columnCount": len(df.columns),
                                    "frozenRowCount": 1,
                                },
                            }
                        }
                    }]
                },
            ).execute()

            properties = (
                response["replies"][0]["addSheet"]["properties"]
            )

        sheet_id = properties["sheetId"]

        for start in range(0, len(values), 500):
            client.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{title}'!A{start + 1}",
                valueInputOption="RAW",
                body={"values": values[start:start + 500]},
            ).execute()

        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SPREADSHEET_ID}/edit#gid={sheet_id}"
        )

        saved["sheet_url"] = url

        return {
            "url": url,
            "row_count": len(df),
            "tab_name": title,
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "tab_name": title,
            "note": (
                "Export may be incomplete. "
                "Retry with the same result_id."
            ),
        }