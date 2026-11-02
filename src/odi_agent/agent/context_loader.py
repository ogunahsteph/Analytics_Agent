"""Load table descriptions from the project's context directory."""

import os
from pathlib import Path

import yaml


def load_table_context() -> str:
    """Read and validate the available table-context YAML files."""

    # This file lives at src/odi_agent/agent/context_loader.py.
    project_root = Path(__file__).resolve().parents[3]

    # An environment override also supports a different deployment location.
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

        if table_id in seen_table_ids:
            raise ValueError(
                f"Duplicate table context for {table_id}"
            )

        seen_table_ids.add(table_id)
        documents.append(document)

    return yaml.safe_dump(
        {"tables": documents},
        sort_keys=False,
        allow_unicode=True,
    )