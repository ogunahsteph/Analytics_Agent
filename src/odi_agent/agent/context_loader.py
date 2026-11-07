# """Load table descriptions from the project's context directory."""

# import os
# from pathlib import Path

# import yaml


# def load_table_context() -> str:
#     """Read and validate the available table-context YAML files."""

#     # This file lives at src/odi_agent/agent/context_loader.py.
#     project_root = Path(__file__).resolve().parents[3]

#     # An environment override also supports a different deployment location.
#     context_dir = Path(
#         os.getenv(
#             "ODI_TABLE_CONTEXT_DIR",
#             str(project_root / "context" / "tables"),
#         )
#     )

#     paths = sorted(context_dir.glob("*.yaml"))

#     if not paths:
#         raise FileNotFoundError(
#             f"No table-context YAML files found in {context_dir}"
#         )

#     documents = []
#     seen_table_ids = set()

#     for path in paths:
#         with path.open(encoding="utf-8") as handle:
#             document = yaml.safe_load(handle)

#         if not isinstance(document, dict):
#             raise ValueError(
#                 f"{path.name} must contain a YAML mapping."
#             )

#         for field in ("name", "table_id", "columns"):
#             if not document.get(field):
#                 raise ValueError(
#                     f"{path.name} is missing required field: {field}"
#                 )

#         table_id = document["table_id"]

#         if table_id in seen_table_ids:
#             raise ValueError(
#                 f"Duplicate table context for {table_id}"
#             )

#         seen_table_ids.add(table_id)
#         documents.append(document)

#     return yaml.safe_dump(
#         {"tables": documents},
#         sort_keys=False,
#         allow_unicode=True,
#     )

"""Load either a compact table catalogue or selected table definitions."""

import os
from pathlib import Path

import yaml


def _read_table_documents() -> list[dict]:
    """Read and validate the available table-context files."""

    project_root = Path(__file__).resolve().parents[3]

    context_dir = Path(
        os.getenv(
            "ODI_TABLE_CONTEXT_DIR",
            str(project_root / "context" / "tables"),
        )
    )

    paths = sorted(context_dir.glob("*.yaml"))

    if not paths:
        raise FileNotFoundError(
            f"No table-context YAML files found in {context_dir}"
        )

    documents = []
    seen_table_ids = set()
    seen_names = set()

    for path in paths:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)

        if not isinstance(document, dict):
            raise ValueError(
                f"{path.name} must contain a YAML mapping."
            )

        for field in ("name", "table_id", "columns"):
            if not document.get(field):
                raise ValueError(
                    f"{path.name} is missing required field: {field}"
                )

        table_id = document["table_id"]
        name = document["name"]

        if not isinstance(table_id, str) or not isinstance(name, str):
            raise ValueError(
                f"{path.name}: name and table_id must be strings."
            )

        if not isinstance(document["columns"], dict):
            raise ValueError(
                f"{path.name}: columns must be a YAML mapping."
            )

        if table_id in seen_table_ids:
            raise ValueError(
                f"Duplicate table context for {table_id}"
            )

        # NEW: Selection uses the YAML 'name', so names must be unique too.
        if name in seen_names:
            raise ValueError(
                f"Duplicate table-context name: {name}"
            )

        seen_table_ids.add(table_id)
        seen_names.add(name)
        documents.append(document)

    return documents


def load_table_catalog() -> str:
    """Return a small directory of available tables."""

    # NEW: The agent can discover tables without receiving every column
    # and rule. Full definitions will be loaded separately when needed.
    catalog = [
        {
            "name": document["name"],
            "table_id": document["table_id"],
            "purpose": document.get("purpose", "").strip(),
        }
        for document in _read_table_documents()
    ]

    return yaml.safe_dump(
        {"available_tables": catalog},
        sort_keys=False,
        allow_unicode=True,
    )


def load_table_context(table_names: list[str] | None = None) -> str:
    """Return full definitions for selected tables, or all if unspecified."""

    documents = _read_table_documents()

    # NEW: Optional selection keeps existing callers working.
    # Calling load_table_context() still returns all table definitions.
    if table_names is not None:
        if (
            not isinstance(table_names, list)
            or not table_names
            or not all(isinstance(name, str) for name in table_names)
        ):
            raise ValueError(
                "table_names must be a non-empty list of table names."
            )

        requested = set(table_names)
        available = {document["name"] for document in documents}
        unknown = requested - available

        # NEW: Reject misspelled names instead of silently omitting context.
        if unknown:
            raise ValueError(
                f"Unknown table names: {', '.join(sorted(unknown))}. "
                f"Available names: {', '.join(sorted(available))}"
            )

        documents = [
            document
            for document in documents
            if document["name"] in requested
        ]

    # Retain all rules for selected tables so token savings do not
    # come from removing important deduplication or join instructions.
    return yaml.safe_dump(
        {"tables": documents},
        sort_keys=False,
        allow_unicode=True,
    )