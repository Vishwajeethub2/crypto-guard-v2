from pathlib import Path
from datetime import datetime, timezone
import json
import math

import pandas as pd
import numpy as np


INPUT_PATH = Path(
    "ml/datasets/processed/ethereum_fraud/ethereum_fraud_model_ready.csv"
)

SCHEMA_PATH = Path(
    "ml/feature_schema/crypto_guard_features_v1.json"
)

OUTPUT_PATH = Path(
    "ml/datasets/processed/ethereum_fraud/crypto_guard_features_v1.csv"
)


def safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_concentration(
    values: list[float],
) -> float:

    positive_values = [
        value
        for value in values
        if value > 0
    ]

    total = sum(
        positive_values
    )

    if total <= 0:
        return 0.0

    shares = [
        value / total
        for value in positive_values
    ]

    return sum(
        share * share
        for share in shares
    )


def build_features(
    row: pd.Series,
) -> dict:

    # ------------------------------------------------------------
    # Source fields
    # ------------------------------------------------------------

    sent_tnx = float(
        row.get("Sent tnx", 0)
    )

    received_tnx = float(
        row.get("Received Tnx", 0)
    )

    total_transactions = float(
        row.get(
            "total transactions (including tnx to create contract",
            0,
        )
    )

    unique_received = float(
        row.get(
            "Unique Received From Addresses",
            0,
        )
    )

    unique_sent = float(
        row.get(
            "Unique Sent To Addresses",
            0,
        )
    )

    first_last_minutes = float(
        row.get(
            "Time Diff between first andlast (Mins)",
            0,
        )
    )

    total_received = float(
        row.get(
            "total ether received",
            0,
        )
    )

    total_sent = float(
        row.get(
            "total Ether sent",
            0,
        )
    )

    min_received = float(
        row.get(
            "min value received",
            0,
        )
    )

    max_received = float(
        row.get(
            "max value received ",
            0,
        )
    )

    avg_received = float(
        row.get(
            "avg val received",
            0,
        )
    )

    min_sent = float(
        row.get(
            "min val sent",
            0,
        )
    )

    max_sent = float(
        row.get(
            "max val sent",
            0,
        )
    )

    avg_sent = float(
        row.get(
            "avg val sent",
            0,
        )
    )

    total_sent_contracts = float(
        row.get(
            "total ether sent contracts",
            0,
        )
    )

    total_created_contracts = float(
        row.get(
            "Number of Created Contracts",
            0,
        )
    )

    erc20_received = float(
        row.get(
            " ERC20 total Ether received",
            0,
        )
    )

    erc20_sent = float(
        row.get(
            " ERC20 total ether sent",
            0,
        )
    )

    erc20_sent_contract = float(
        row.get(
            " ERC20 total Ether sent contract",
            0,
        )
    )

    erc20_unique_sent = float(
        row.get(
            " ERC20 uniq sent addr",
            0,
        )
    )

    erc20_unique_received = float(
        row.get(
            " ERC20 uniq rec addr",
            0,
        )
    )

    # ------------------------------------------------------------
    # Transaction activity
    # ------------------------------------------------------------

    transaction_count = total_transactions

    incoming_transaction_count = received_tnx

    outgoing_transaction_count = sent_tnx

    activity_duration_seconds = (
        first_last_minutes
        * 60.0
    )

    # ------------------------------------------------------------
    # Value flow
    # ------------------------------------------------------------

    incoming_outgoing_ratio = safe_divide(
        total_received,
        total_sent,
    )

    # The source dataset does not contain the
    # per-counterparty transaction-value distribution
    # needed to calculate true concentration.
    #
    # Therefore these are kept as 0 in this
    # dataset adapter rather than inventing a value.
    outgoing_value_concentration = 0.0
    incoming_value_concentration = 0.0

    # ------------------------------------------------------------
    # Counterparty / network
    # ------------------------------------------------------------

    total_unique_counterparties = (
        unique_received
        + unique_sent
    )

    fan_in = unique_received

    fan_out = unique_sent

    # The dataset does not explicitly identify
    # repeated counterparties.
    counterparty_reuse_count = 0.0

    # No Neo4j graph is used by this offline
    # dataset adapter.
    graph_multi_hop_exposure_count = 0.0

    # ------------------------------------------------------------
    # Fee behavior
    # ------------------------------------------------------------

    # IMPORTANT:
    #
    # The Ethereum Fraud Detection dataset does
    # not contain actual gas/transaction-fee fields.
    #
    # We therefore DO NOT manufacture fee values.
    #
    # These remain zero in this adapter and will be
    # populated by the real Crypto Guard EVM extractor
    # from blockchain transaction receipts.

    total_transaction_fees = 0.0
    average_transaction_fee = 0.0
    minimum_transaction_fee = 0.0
    maximum_transaction_fee = 0.0
    fee_to_value_ratio = 0.0

    # ------------------------------------------------------------
    # Temporal behavior
    # ------------------------------------------------------------

    average_gap = safe_divide(
        activity_duration_seconds,
        max(
            transaction_count - 1,
            1,
        ),
    )

    minimum_gap = 0.0
    maximum_gap = activity_duration_seconds

    # Aggregate source dataset does not preserve
    # individual timestamps, so burst detection cannot
    # be reconstructed safely here.
    transaction_burst_count = 0.0
    rapid_transaction_sequence_count = 0.0

    # ------------------------------------------------------------
    # Return standardized schema
    # ------------------------------------------------------------

    return {
        "transaction_count": transaction_count,
        "incoming_transaction_count": (
            incoming_transaction_count
        ),
        "outgoing_transaction_count": (
            outgoing_transaction_count
        ),
        "unique_incoming_counterparties": (
            unique_received
        ),
        "unique_outgoing_counterparties": (
            unique_sent
        ),
        "activity_duration_seconds": (
            activity_duration_seconds
        ),
        "total_incoming_value": (
            total_received
        ),
        "total_outgoing_value": (
            total_sent
        ),
        "average_incoming_value": (
            avg_received
        ),
        "average_outgoing_value": (
            avg_sent
        ),
        "maximum_incoming_value": (
            max_received
        ),
        "maximum_outgoing_value": (
            max_sent
        ),
        "incoming_outgoing_value_ratio": (
            incoming_outgoing_ratio
        ),
        "outgoing_value_concentration": (
            outgoing_value_concentration
        ),
        "incoming_value_concentration": (
            incoming_value_concentration
        ),
        "total_unique_counterparties": (
            total_unique_counterparties
        ),
        "counterparty_reuse_count": (
            counterparty_reuse_count
        ),
        "fan_in": fan_in,
        "fan_out": fan_out,
        "graph_multi_hop_exposure_count": (
            graph_multi_hop_exposure_count
        ),
        "total_transaction_fees": (
            total_transaction_fees
        ),
        "average_transaction_fee": (
            average_transaction_fee
        ),
        "minimum_transaction_fee": (
            minimum_transaction_fee
        ),
        "maximum_transaction_fee": (
            maximum_transaction_fee
        ),
        "fee_to_value_ratio": (
            fee_to_value_ratio
        ),
        "average_transaction_gap_seconds": (
            average_gap
        ),
        "minimum_transaction_gap_seconds": (
            minimum_gap
        ),
        "maximum_transaction_gap_seconds": (
            maximum_gap
        ),
        "transaction_burst_count": (
            transaction_burst_count
        ),
        "rapid_transaction_sequence_count": (
            rapid_transaction_sequence_count
        ),
    }


def main() -> None:

    print("=" * 75)
    print("CRYPTO GUARD FEATURE EXTRACTION")
    print("=" * 75)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input dataset not found:\n{INPUT_PATH}"
        )

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Feature schema not found:\n{SCHEMA_PATH}"
        )

    print("\nLoading source dataset...")

    df = pd.read_csv(
        INPUT_PATH
    )

    print(
        f"Rows: {len(df):,}"
    )

    with SCHEMA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        schema = json.load(file)

    schema_features = []

    for group_features in (
        schema["groups"].values()
    ):
        for feature in group_features:
            schema_features.append(
                feature["name"]
            )

    print(
        f"Schema features: "
        f"{len(schema_features)}"
    )

    # ------------------------------------------------------------
    # Build features
    # ------------------------------------------------------------

    records = []

    for _, row in df.iterrows():

        features = build_features(
            row
        )

        records.append(
            features
        )

    features_df = pd.DataFrame(
        records
    )

    # ------------------------------------------------------------
    # Ensure exact schema order
    # ------------------------------------------------------------

    missing_features = [
        feature
        for feature in schema_features
        if feature not in features_df.columns
    ]

    extra_features = [
        feature
        for feature in features_df.columns
        if feature not in schema_features
    ]

    if missing_features:
        raise ValueError(
            "Missing schema features:\n"
            + "\n".join(
                missing_features
            )
        )

    if extra_features:
        print(
            "\nWARNING: Extra generated features:"
        )

        for feature in extra_features:
            print(
                f"  - {feature}"
            )

    features_df = features_df[
        schema_features
    ].copy()

    # ------------------------------------------------------------
    # Add metadata
    # ------------------------------------------------------------

    if "Address" in df.columns:
        features_df.insert(
            0,
            "address",
            df["Address"].values,
        )

    if "FLAG" in df.columns:
        features_df["target"] = (
            df["FLAG"].values
        )

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------

    numeric_columns = [
        column
        for column in features_df.columns
        if column not in {
            "address",
        }
    ]

    missing_count = int(
        features_df[
            numeric_columns
        ].isna().sum().sum()
    )

    infinite_count = int(
        np.isinf(
            features_df[
                numeric_columns
            ].to_numpy()
        ).sum()
    )

    print("\n" + "-" * 75)
    print("VALIDATION")
    print("-" * 75)

    print(
        f"Output rows:       "
        f"{len(features_df):,}"
    )

    print(
        f"Output features:   "
        f"{len(schema_features):,}"
    )

    print(
        f"Missing values:    "
        f"{missing_count:,}"
    )

    print(
        f"Infinite values:   "
        f"{infinite_count:,}"
    )

    if missing_count != 0:
        raise ValueError(
            "Missing values detected."
        )

    if infinite_count != 0:
        raise ValueError(
            "Infinite values detected."
        )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    features_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n" + "-" * 75)
    print("OUTPUT")
    print("-" * 75)

    print(
        f"Saved:\n{OUTPUT_PATH}"
    )

    print("\n" + "=" * 75)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()