from app.db.neo4j import (
    get_neo4j_session,
    ingest_transfer_batch,
)

from app.services.blockchain import (
    build_graph_transactions,
    get_address_transfers,
    get_address_transfers_live,
    get_saved_parsed_transfers,
    parse_transfer_data,
    validate_wallet_address,
)


def get_existing_transaction_keys(
    transactions: list[dict],
) -> set[tuple[str, str]]:
    """
    Find transactions that already exist in Neo4j.

    Transaction identity is based on:
        chain + transaction_hash
    """

    transaction_keys = {
        (
            transaction.get("chain", "ethereum").lower(),
            transaction["transaction_hash"],
        )
        for transaction in transactions
        if transaction.get("transaction_hash")
    }

    if not transaction_keys:
        return set()

    transaction_hashes = {
        transaction_hash
        for _, transaction_hash in transaction_keys
    }

    with get_neo4j_session() as session:
        result = session.run(
            """
            MATCH ()-[t:TRANSFER]->()
            WHERE t.transaction_hash IN $transaction_hashes
            RETURN
                t.chain AS chain,
                t.transaction_hash AS transaction_hash
            """,
            transaction_hashes=list(transaction_hashes),
        )

        existing_keys = set()

        for record in result:
            chain = record["chain"]
            transaction_hash = record["transaction_hash"]

            if chain and transaction_hash:
                existing_keys.add(
                    (
                        str(chain).lower(),
                        transaction_hash,
                    )
                )

        return existing_keys


def validate_graph_transaction(
    transaction: dict,
) -> tuple[bool, str | None]:
    """
    Validate a normalized graph transaction.

    Returns:
        (True, None) when valid.
        (False, reason) when invalid.
    """

    transaction_hash = transaction.get(
        "transaction_hash"
    )

    if not transaction_hash:
        return False, "Missing transaction hash"

    chain = transaction.get("chain")

    if not chain:
        return False, "Missing chain"

    chain = chain.lower()

    supported_chains = {
        "ethereum",
        "polygon",
        "arbitrum",
        "optimism",
        "base",
    }

    if chain not in supported_chains:
        return False, "Unsupported chain"

    from_address = transaction.get(
        "from_address"
    )

    if not from_address:
        return False, "Missing sender address"

    if not validate_wallet_address(
        from_address
    ):
        return False, "Invalid sender address"

    to_address = transaction.get(
        "to_address"
    )

    if not to_address:
        return False, "Missing receiver address"

    if not validate_wallet_address(
        to_address
    ):
        return False, "Invalid receiver address"

    if transaction.get("block_number") is None:
        return False, "Missing block number"

    return True, None


def ingest_saved_transfers(
    chain: str = "ethereum",
):
    """
    Ingest saved blockchain transfer data into Neo4j.

    This function uses saved sample data and does not make
    a live Alchemy API request.
    """

    chain = chain.lower()

    transfers = get_saved_parsed_transfers()

    for transfer in transfers:
        transfer["chain"] = chain

    graph_transactions = build_graph_transactions(
        transfers
    )

    valid_transactions = []
    invalid_transactions = []

    for transaction in graph_transactions:
        is_valid, reason = validate_graph_transaction(
            transaction
        )

        if is_valid:
            valid_transactions.append(
                transaction
            )
        else:
            invalid_transactions.append(
                {
                    "transaction_hash": transaction.get(
                        "transaction_hash"
                    ),
                    "reason": reason,
                }
            )

    existing_keys = get_existing_transaction_keys(
        valid_transactions
    )

    new_transactions = [
        transaction
        for transaction in valid_transactions
        if (
            transaction.get(
                "chain",
                "ethereum",
            ).lower(),
            transaction["transaction_hash"],
        )
        not in existing_keys
    ]

    if new_transactions:
        result = ingest_transfer_batch(
            new_transactions
        )
        ingested_count = result[
            "ingested_count"
        ]
    else:
        ingested_count = 0

    return {
        "chain": chain,
        "source": "saved_data",
        "total_found": len(transfers),
        "normalized_count": len(
            graph_transactions
        ),
        "valid_count": len(
            valid_transactions
        ),
        "invalid_count": len(
            invalid_transactions
        ),
        "new_count": len(
            new_transactions
        ),
        "duplicate_count": len(
            existing_keys
        ),
        "ingested_count": ingested_count,
        "invalid_records": invalid_transactions,
    }


def ingest_live_transfers(
    chain: str,
    address: str,
    max_count: int = 20,
):
    """
    Fetch live transfer data from Alchemy and ingest
    only valid, non-duplicate transactions into Neo4j.
    """

    chain = chain.lower()

    if not validate_wallet_address(
        address
    ):
        raise ValueError(
            "Invalid wallet address"
        )

    if max_count < 1 or max_count > 100:
        raise ValueError(
            "max_count must be between 1 and 100"
        )

    alchemy_response = get_address_transfers(
        chain=chain,
        address=address,
        max_count=max_count,
    )

    raw_transfers = (
        alchemy_response["transfers"]
    )

    parsed_transfers = parse_transfer_data(
        raw_transfers
    )

    for transfer in parsed_transfers:
        transfer["chain"] = chain

    graph_transactions = build_graph_transactions(
        parsed_transfers
    )

    valid_transactions = []
    invalid_transactions = []

    for transaction in graph_transactions:
        is_valid, reason = validate_graph_transaction(
            transaction
        )

        if is_valid:
            valid_transactions.append(
                transaction
            )
        else:
            invalid_transactions.append(
                {
                    "transaction_hash": transaction.get(
                        "transaction_hash"
                    ),
                    "reason": reason,
                }
            )

    existing_keys = get_existing_transaction_keys(
        valid_transactions
    )

    new_transactions = [
        transaction
        for transaction in valid_transactions
        if (
            transaction.get(
                "chain",
                "ethereum",
            ).lower(),
            transaction["transaction_hash"],
        )
        not in existing_keys
    ]

    if new_transactions:
        result = ingest_transfer_batch(
            new_transactions
        )
        ingested_count = result[
            "ingested_count"
        ]
    else:
        ingested_count = 0

    return {
        "chain": chain,
        "source": "alchemy",
        "address": address,
        "total_found": len(raw_transfers),
        "normalized_count": len(
            graph_transactions
        ),
        "valid_count": len(
            valid_transactions
        ),
        "invalid_count": len(
            invalid_transactions
        ),
        "new_count": len(
            new_transactions
        ),
        "duplicate_count": len(
            existing_keys
        ),
        "ingested_count": ingested_count,
        "invalid_records": invalid_transactions,
    }


def ingest_live_transfers_bidirectional(
    chain: str,
    address: str,
    max_count: int = 10,
):
    """
    Fetch a bounded set of real incoming and outgoing transfers
    from Alchemy and persist only valid, non-duplicate transactions
    into Neo4j.

    This is the advanced live-tracing ingestion path.
    The existing ingest_live_transfers() function remains unchanged.
    """

    chain = chain.lower()

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    if max_count < 1 or max_count > 100:
        raise ValueError(
            "max_count must be between 1 and 100"
        )

    alchemy_response = get_address_transfers_live(
        chain=chain,
        address=address,
        direction="both",
        max_count=max_count,
    )

    raw_transfers = alchemy_response["transfers"]

    parsed_transfers = parse_transfer_data(
        raw_transfers
    )

    for transfer in parsed_transfers:
        transfer["chain"] = chain

    graph_transactions = build_graph_transactions(
        parsed_transfers
    )

    valid_transactions = []
    invalid_transactions = []

    for transaction in graph_transactions:
        is_valid, reason = validate_graph_transaction(
            transaction
        )

        if is_valid:
            valid_transactions.append(
                transaction
            )
        else:
            invalid_transactions.append(
                {
                    "transaction_hash": transaction.get(
                        "transaction_hash"
                    ),
                    "reason": reason,
                }
            )

    existing_keys = get_existing_transaction_keys(
        valid_transactions
    )

    new_transactions = [
        transaction
        for transaction in valid_transactions
        if (
            transaction.get(
                "chain",
                "ethereum",
            ).lower(),
            transaction["transaction_hash"],
        )
        not in existing_keys
    ]

    if new_transactions:
        result = ingest_transfer_batch(
            new_transactions
        )
        ingested_count = result["ingested_count"]
    else:
        ingested_count = 0

    return {
        "chain": chain,
        "source": "alchemy",
        "address": address,
        "direction": "both",
        "total_found": len(raw_transfers),
        "normalized_count": len(graph_transactions),
        "valid_count": len(valid_transactions),
        "invalid_count": len(invalid_transactions),
        "new_count": len(new_transactions),
        "duplicate_count": len(existing_keys),
        "ingested_count": ingested_count,
        "invalid_transactions": invalid_transactions,
    }
