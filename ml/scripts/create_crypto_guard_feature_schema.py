from pathlib import Path
import json


OUTPUT_PATH = Path(
    "ml/feature_schema/crypto_guard_features_v1.json"
)


SCHEMA = {
    "schema_version": "1.0",
    "name": "Crypto Guard Behavioral ML Feature Schema",
    "description": (
        "Production-oriented behavioral feature contract for "
        "Crypto Guard wallet risk modeling."
    ),
    "status": "candidate",
    "target": {
        "name": "illicit_activity",
        "type": "binary",
        "values": {
            "0": "non_illicit",
            "1": "illicit",
        },
    },
    "groups": {
        "transaction_activity": [
            {
                "name": "transaction_count",
                "type": "numeric",
                "description": "Total observed blockchain transactions.",
            },
            {
                "name": "incoming_transaction_count",
                "type": "numeric",
                "description": "Number of incoming transactions.",
            },
            {
                "name": "outgoing_transaction_count",
                "type": "numeric",
                "description": "Number of outgoing transactions.",
            },
            {
                "name": "unique_incoming_counterparties",
                "type": "numeric",
                "description": "Unique addresses sending funds to the wallet.",
            },
            {
                "name": "unique_outgoing_counterparties",
                "type": "numeric",
                "description": "Unique addresses receiving funds from the wallet.",
            },
            {
                "name": "activity_duration_seconds",
                "type": "numeric",
                "description": "Time between first and last observed activity.",
            },
        ],
        "value_flow": [
            {
                "name": "total_incoming_value",
                "type": "numeric",
                "description": "Total observed incoming value.",
            },
            {
                "name": "total_outgoing_value",
                "type": "numeric",
                "description": "Total observed outgoing value.",
            },
            {
                "name": "average_incoming_value",
                "type": "numeric",
                "description": "Average value of incoming transactions.",
            },
            {
                "name": "average_outgoing_value",
                "type": "numeric",
                "description": "Average value of outgoing transactions.",
            },
            {
                "name": "maximum_incoming_value",
                "type": "numeric",
                "description": "Largest observed incoming transaction.",
            },
            {
                "name": "maximum_outgoing_value",
                "type": "numeric",
                "description": "Largest observed outgoing transaction.",
            },
            {
                "name": "incoming_outgoing_value_ratio",
                "type": "numeric",
                "description": "Relationship between incoming and outgoing value.",
            },
            {
                "name": "outgoing_value_concentration",
                "type": "numeric",
                "description": "Concentration of outgoing value among counterparties.",
            },
            {
                "name": "incoming_value_concentration",
                "type": "numeric",
                "description": "Concentration of incoming value among counterparties.",
            },
        ],
        "counterparty_network": [
            {
                "name": "total_unique_counterparties",
                "type": "numeric",
                "description": "Total unique counterparties.",
            },
            {
                "name": "counterparty_reuse_count",
                "type": "numeric",
                "description": "Number of counterparties involved in repeated transactions.",
            },
            {
                "name": "fan_in",
                "type": "numeric",
                "description": "Number of incoming counterparties.",
            },
            {
                "name": "fan_out",
                "type": "numeric",
                "description": "Number of outgoing counterparties.",
            },
            {
                "name": "graph_multi_hop_exposure_count",
                "type": "numeric",
                "description": "Observed risk-related multi-hop graph exposure.",
            },
        ],
        "fee_behavior": [
            {
                "name": "total_transaction_fees",
                "type": "numeric",
                "description": "Total observed transaction fees.",
            },
            {
                "name": "average_transaction_fee",
                "type": "numeric",
                "description": "Average observed transaction fee.",
            },
            {
                "name": "minimum_transaction_fee",
                "type": "numeric",
                "description": "Minimum observed transaction fee.",
            },
            {
                "name": "maximum_transaction_fee",
                "type": "numeric",
                "description": "Maximum observed transaction fee.",
            },
            {
                "name": "fee_to_value_ratio",
                "type": "numeric",
                "description": "Transaction fee relative to transferred value.",
            },
        ],
        "temporal_behavior": [
            {
                "name": "average_transaction_gap_seconds",
                "type": "numeric",
                "description": "Average time between observed transactions.",
            },
            {
                "name": "minimum_transaction_gap_seconds",
                "type": "numeric",
                "description": "Shortest observed transaction gap.",
            },
            {
                "name": "maximum_transaction_gap_seconds",
                "type": "numeric",
                "description": "Longest observed transaction gap.",
            },
            {
                "name": "transaction_burst_count",
                "type": "numeric",
                "description": "Number of detected transaction bursts.",
            },
            {
                "name": "rapid_transaction_sequence_count",
                "type": "numeric",
                "description": "Number of rapid transaction sequences.",
            },
        ],
    },
}


def main() -> None:
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            SCHEMA,
            file,
            indent=2,
        )

    feature_count = sum(
        len(features)
        for features in SCHEMA["groups"].values()
    )

    print("=" * 75)
    print("CRYPTO GUARD ML FEATURE SCHEMA")
    print("=" * 75)

    print(
        f"\nSchema version: "
        f"{SCHEMA['schema_version']}"
    )

    print(
        f"Feature groups: "
        f"{len(SCHEMA['groups'])}"
    )

    print(
        f"Total features: "
        f"{feature_count}"
    )

    print("\nGroups:")

    for group_name, features in (
        SCHEMA["groups"].items()
    ):
        print(
            f"  {group_name}: "
            f"{len(features)}"
        )

    print("\nSaved:")
    print(f"  {OUTPUT_PATH}")

    print("\n" + "=" * 75)
    print("FEATURE SCHEMA CREATED")
    print("=" * 75)


if __name__ == "__main__":
    main()