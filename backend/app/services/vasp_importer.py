from __future__ import annotations

import csv
from pathlib import Path

from app.services.intelligence import add_risk_entity


CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "vasp_addresses.csv"
)

REQUIRED_COLUMNS = {
    "address",
    "chain",
    "entity_type",
    "entity_name",
    "intelligence_source",
    "risk_category",
    "confidence",
    "evidence",
}


def import_vasp_addresses() -> int:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"VASP dataset not found: {CSV_PATH}"
        )

    imported_count = 0

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError(
                "VASP CSV is missing its header"
            )

        missing_columns = (
            REQUIRED_COLUMNS
            - set(reader.fieldnames)
        )

        if missing_columns:
            raise ValueError(
                "VASP CSV is missing columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            address = (row["address"] or "").strip()
            chain = (row["chain"] or "").strip()
            entity_type = (
                row["entity_type"] or ""
            ).strip()
            entity_name = (
                row["entity_name"] or ""
            ).strip()
            intelligence_source = (
                row["intelligence_source"] or ""
            ).strip()
            risk_category = (
                row["risk_category"] or ""
            ).strip()
            confidence_value = (
                row["confidence"] or ""
            ).strip()
            evidence = (
                row["evidence"] or ""
            ).strip()

            if not address:
                raise ValueError(
                    f"Row {row_number}: address is required"
                )

            if not chain:
                raise ValueError(
                    f"Row {row_number}: chain is required"
                )

            if not entity_name:
                raise ValueError(
                    f"Row {row_number}: entity_name is required"
                )

            if not intelligence_source:
                raise ValueError(
                    f"Row {row_number}: "
                    "intelligence_source is required"
                )

            confidence = None

            if confidence_value:
                try:
                    confidence = float(
                        confidence_value
                    )
                except ValueError as error:
                    raise ValueError(
                        f"Row {row_number}: "
                        "confidence must be a number"
                    ) from error

            add_risk_entity(
                address=address,
                chain=chain,
                entity_type=entity_type,
                name=entity_name,
                source=intelligence_source,
                risk_category=(
                    risk_category
                    or None
                ),
                confidence=confidence,
                evidence=evidence or None,
            )

            imported_count += 1

    return imported_count


if __name__ == "__main__":
    count = import_vasp_addresses()
    print(
        f"VASP import completed: {count} row(s) imported."
    )
