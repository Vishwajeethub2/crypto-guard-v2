from __future__ import annotations

import csv
from pathlib import Path

from app.services.intelligence import (
    SUPPORTED_CHAINS,
    SUPPORTED_ENTITY_TYPES,
    add_risk_entity,
)


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


def _normalize_address(
    address: str,
    row_number: int,
) -> str:
    address = address.strip()

    if not address:
        raise ValueError(
            f"Row {row_number}: address is required"
        )

    if not address.startswith("0x"):
        raise ValueError(
            f"Row {row_number}: address must start with 0x"
        )

    if len(address) != 42:
        raise ValueError(
            f"Row {row_number}: address must contain 42 characters"
        )

    return address


def _normalize_chain(
    chain: str,
    row_number: int,
) -> str:
    chain = chain.strip().lower()

    if not chain:
        raise ValueError(
            f"Row {row_number}: chain is required"
        )

    if chain not in SUPPORTED_CHAINS:
        raise ValueError(
            f"Row {row_number}: unsupported chain '{chain}'. "
            f"Supported chains: "
            f"{', '.join(sorted(SUPPORTED_CHAINS))}"
        )

    return chain


def _normalize_entity_type(
    entity_type: str,
    row_number: int,
) -> str:
    entity_type = entity_type.strip().lower()

    if not entity_type:
        raise ValueError(
            f"Row {row_number}: entity_type is required"
        )

    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise ValueError(
            f"Row {row_number}: unsupported entity_type "
            f"'{entity_type}'. Supported types: "
            f"{', '.join(sorted(SUPPORTED_ENTITY_TYPES))}"
        )

    return entity_type


def _parse_confidence(
    value: str,
    row_number: int,
) -> float | None:
    value = value.strip()

    if not value:
        return None

    try:
        confidence = float(value)
    except ValueError as error:
        raise ValueError(
            f"Row {row_number}: confidence must be a number"
        ) from error

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"Row {row_number}: confidence must be "
            "between 0 and 1"
        )

    return confidence


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
            address = _normalize_address(
                row["address"] or "",
                row_number,
            )

            chain = _normalize_chain(
                row["chain"] or "",
                row_number,
            )

            entity_type = _normalize_entity_type(
                row["entity_type"] or "",
                row_number,
            )

            entity_name = (
                row["entity_name"] or ""
            ).strip()

            intelligence_source = (
                row["intelligence_source"] or ""
            ).strip()

            risk_category = (
                row["risk_category"] or ""
            ).strip().lower()

            evidence = (
                row["evidence"] or ""
            ).strip()

            if not entity_name:
                raise ValueError(
                    f"Row {row_number}: "
                    "entity_name is required"
                )

            if not intelligence_source:
                raise ValueError(
                    f"Row {row_number}: "
                    "intelligence_source is required"
                )

            confidence = _parse_confidence(
                row["confidence"] or "",
                row_number,
            )

            add_risk_entity(
                address=address,
                chain=chain,
                entity_type=entity_type,
                name=entity_name,
                source=intelligence_source,
                risk_category=(
                    risk_category or None
                ),
                confidence=confidence,
                evidence=evidence or None,
            )

            imported_count += 1

    return imported_count


if __name__ == "__main__":
    count = import_vasp_addresses()

    print(
        f"VASP import completed: "
        f"{count} row(s) imported."
    )