from pathlib import Path

import pandas as pd


DATA_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_wallet_validation.csv"
)


def find_columns(df, keywords):
    matches = []

    for column in df.columns:
        name = column.lower()

        if any(keyword in name for keyword in keywords):
            matches.append(column)

    return matches


def main():
    print("=" * 75)
    print("ELLIPTIC++ / CRYPTO GUARD FEATURE COMPATIBILITY AUDIT")
    print("=" * 75)

    df = pd.read_csv(DATA_PATH)

    print("\nDataset:")
    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    feature_columns = [
        column
        for column in df.columns
        if column not in ["address", "target"]
    ]

    print(f"Behavioral features: {len(feature_columns)}")

    print("\n--- CRYPTO GUARD CONCEPT: TRANSACTION ACTIVITY ---")

    activity_columns = find_columns(
        df,
        [
            "txs",
            "transaction",
            "lifetime",
            "timesteps",
        ],
    )

    for column in activity_columns:
        print(f"  - {column}")

    print("\n--- CRYPTO GUARD CONCEPT: OUTGOING / SENT ACTIVITY ---")

    sent_columns = find_columns(
        df,
        [
            "sent",
            "sender",
            "output",
        ],
    )

    for column in sent_columns:
        print(f"  - {column}")

    print("\n--- CRYPTO GUARD CONCEPT: INCOMING / RECEIVED ACTIVITY ---")

    received_columns = find_columns(
        df,
        [
            "received",
            "receiver",
            "input",
        ],
    )

    for column in received_columns:
        print(f"  - {column}")

    print("\n--- CRYPTO GUARD CONCEPT: VALUE FLOW ---")

    value_columns = find_columns(
        df,
        [
            "btc_",
            "value",
        ],
    )

    for column in value_columns:
        print(f"  - {column}")

    print("\n--- CRYPTO GUARD CONCEPT: FEES ---")

    fee_columns = find_columns(
        df,
        [
            "fee",
        ],
    )

    for column in fee_columns:
        print(f"  - {column}")

    print("\n--- CRYPTO GUARD CONCEPT: COUNTERPARTY / NETWORK ACTIVITY ---")

    counterparty_columns = find_columns(
        df,
        [
            "addr",
            "address",
            "transacted",
        ],
    )

    for column in counterparty_columns:
        print(f"  - {column}")

    print("\n--- CRYPTO GUARD CONCEPT: TEMPORAL ACTIVITY ---")

    temporal_columns = find_columns(
        df,
        [
            "time",
            "block",
            "lifetime",
        ],
    )

    for column in temporal_columns:
        print(f"  - {column}")

    print("\n--- TARGET ---")

    print(df["target"].value_counts().sort_index())

    print("\nTarget means for selected behavioral features:")

    selected = [
        column
        for column in (
            activity_columns
            + sent_columns
            + received_columns
            + value_columns
            + fee_columns
            + counterparty_columns
            + temporal_columns
        )
        if column in df.columns
        and column != "address"
        and pd.api.types.is_numeric_dtype(df[column])
    ]

    # Remove duplicate columns while preserving order.
    selected = list(dict.fromkeys(selected))

    if selected:
        summary = (
            df.groupby("target")[selected]
            .mean()
            .transpose()
        )

        print(summary.to_string())

    print("\n--- FEATURE CORRELATION WITH TARGET ---")

    numeric_features = df.select_dtypes(include="number").columns.tolist()

    numeric_features = [
        column
        for column in numeric_features
        if column != "target"
    ]

    correlations = (
        df[numeric_features + ["target"]]
        .corr(numeric_only=True)["target"]
        .drop("target")
        .sort_values(key=abs, ascending=False)
    )

    print(correlations.head(25).to_string())

    print("\n--- FEATURE RANGE CHECK ---")

    print(
        df[numeric_features]
        .describe()
        .transpose()
        .head(25)
        .to_string()
    )

    print("\n" + "=" * 75)
    print("COMPATIBILITY AUDIT COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()