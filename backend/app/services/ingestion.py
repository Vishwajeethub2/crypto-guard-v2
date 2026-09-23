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

    Returns the normalized valid transactions as `transactions`
    so recursive discovery can reuse the same Alchemy response
    without making another API request for the same wallet.
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

    # Keep live-refresh accounting internally consistent.
    #
    # valid_transactions = transactions that passed validation.
    # Some of those may already exist in Neo4j, while the remainder
    # are candidates for ingestion. The batch writer returns the
    # number it actually processed.
    #
    # Treat every valid transaction not reported as newly ingested
    # as a duplicate/already-present transaction for reporting.
    # This guarantees:
    #
    # total_found == ingested_count + duplicate_count + invalid_count
    #
    # whenever normalized_count == total_found.

    effective_ingested_count = min(
        ingested_count,
        len(new_transactions),
    )

    effective_duplicate_count = (
        len(valid_transactions)
        - effective_ingested_count
    )

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
        "duplicate_count": effective_duplicate_count,
        "ingested_count": effective_ingested_count,
        "invalid_transactions": invalid_transactions,
        "transactions": valid_transactions,
    }


def ingest_live_transfers_recursive(
    chain: str,
    address: str,
    max_hops: int = 2,
    max_wallets: int = 25,
    max_transfers_per_wallet: int = 10,
):
    """
    Controlled recursive live blockchain discovery.

    Starts from the target wallet and recursively discovers
    counterparties through live Alchemy transfers.

    Safety controls:
        max_hops:
            Maximum graph depth. Hard maximum is 5.

        max_wallets:
            Maximum number of unique wallets processed.

        max_transfers_per_wallet:
            Maximum live transfers requested per wallet.

    Each wallet is processed at most once.

    The same Alchemy response is used for both:
        1. Neo4j ingestion
        2. Counterparty discovery

    This prevents duplicate API calls for the same wallet.
    """

    chain = chain.lower()
    address = address.lower()

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    if max_hops < 1:
        raise ValueError(
            "max_hops must be at least 1"
        )

    if max_hops > 5:
        raise ValueError(
            "max_hops cannot exceed 5"
        )

    if max_wallets < 1:
        raise ValueError(
            "max_wallets must be at least 1"
        )

    if max_wallets > 100:
        raise ValueError(
            "max_wallets cannot exceed 100"
        )

    if max_transfers_per_wallet < 1:
        raise ValueError(
            "max_transfers_per_wallet must be at least 1"
        )

    if max_transfers_per_wallet > 100:
        raise ValueError(
            "max_transfers_per_wallet cannot exceed 100"
        )

    queue = [
        {
            "address": address,
            "hop": 0,
        }
    ]

    visited = set()

    discovered_wallets = []

    total_found = 0
    total_ingested = 0
    total_duplicates = 0
    total_invalid = 0
    api_calls = 0

    while queue and len(visited) < max_wallets:
        current = queue.pop(0)

        current_address = current["address"].lower()
        current_hop = current["hop"]

        if current_address in visited:
            continue

        visited.add(current_address)

        discovered_wallets.append(
            {
                "address": current_address,
                "hop": current_hop,
            }
        )

        # Do not fetch beyond the requested hop depth.
        if current_hop >= max_hops:
            continue

        result = ingest_live_transfers_bidirectional(
            chain=chain,
            address=current_address,
            max_count=max_transfers_per_wallet,
        )

        api_calls += 1

        total_found += result.get(
            "total_found",
            0,
        )

        total_ingested += result.get(
            "ingested_count",
            0,
        )

        total_duplicates += result.get(
            "duplicate_count",
            0,
        )

        total_invalid += result.get(
            "invalid_count",
            0,
        )

        # Reuse the same normalized transactions returned
        # by the Alchemy request. No second API call.
        transactions = result.get(
            "transactions",
            [],
        )

        for transaction in transactions:
            from_address = transaction.get(
                "from_address"
            )

            to_address = transaction.get(
                "to_address"
            )

            counterparties = []

            if from_address:
                counterparties.append(
                    from_address.lower()
                )

            if to_address:
                counterparties.append(
                    to_address.lower()
                )

            for counterparty in counterparties:
                if counterparty == current_address:
                    continue

                if counterparty in visited:
                    continue

                if any(
                    queued["address"] == counterparty
                    for queued in queue
                ):
                    continue

                if (
                    len(visited) + len(queue)
                    >= max_wallets
                ):
                    continue

                queue.append(
                    {
                        "address": counterparty,
                        "hop": current_hop + 1,
                    }
                )

    return {
        "chain": chain,
        "source": "alchemy",
        "address": address,
        "max_hops": max_hops,
        "max_wallets": max_wallets,
        "max_transfers_per_wallet": max_transfers_per_wallet,
        "wallets_discovered": len(
            discovered_wallets
        ),
        "wallets_processed": len(
            visited
        ),
        "transfers_found": total_found,
        "transfers_ingested": total_ingested,
        "duplicate_transfers": total_duplicates,
        "invalid_transfers": total_invalid,
        "api_calls": api_calls,
        "max_hops_reached": any(
            wallet["hop"] >= max_hops
            for wallet in discovered_wallets
        ),
        "wallets": discovered_wallets,
    }