from neo4j import GraphDatabase

from app.core.config import settings


NEO4J_DATABASE = "52840a9c"


driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(
        settings.neo4j_username,
        settings.neo4j_password,
    ),
    connection_timeout=30,
    max_connection_lifetime=300,
    max_connection_pool_size=50,
)


def get_neo4j_driver():
    return driver


def get_neo4j_session():
    return driver.session(database=NEO4J_DATABASE)


def test_neo4j_connection():
    with get_neo4j_session() as session:
        result = session.run("RETURN 1 AS number")
        return result.single()["number"]


def create_wallet_node(
    address: str,
    chain: str,
    label: str | None = None,
):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MERGE (w:Wallet {
                address: $address,
                chain: $chain
            })
            SET w.label = $label

            RETURN
                w.address AS address,
                w.chain AS chain,
                w.label AS label
            """,
            address=address,
            chain=chain.lower(),
            label=label,
        )

        return result.single()


def create_transfer_relationship(transaction: dict):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MERGE (sender:Wallet {
                address: $from_address,
                chain: $chain
            })

            MERGE (receiver:Wallet {
                address: $to_address,
                chain: $chain
            })

            MERGE (sender)-[
                t:TRANSFER {
                    chain: $chain,
                    transaction_hash: $transaction_hash
                }
            ]->(receiver)

            SET
                t.asset = $asset,
                t.value = $value,
                t.category = $category,
                t.block_number = $block_number,
                t.timestamp = $timestamp,
                t.contract_address = $contract_address

            RETURN
                sender.address AS from_address,
                receiver.address AS to_address,
                t.chain AS chain,
                t.transaction_hash AS transaction_hash
            """,
            from_address=transaction["from_address"],
            to_address=transaction["to_address"],
            chain=transaction.get(
                "chain",
                "ethereum",
            ).lower(),
            transaction_hash=transaction["transaction_hash"],
            asset=transaction["asset"],
            value=transaction["value"],
            category=transaction["category"],
            block_number=transaction["block_number"],
            timestamp=transaction["timestamp"],
            contract_address=transaction["contract_address"],
        )

        return result.single()


def ingest_transfer_batch(transactions: list[dict]):
    with get_neo4j_session() as session:
        for transaction in transactions:
            session.run(
                """
                MERGE (sender:Wallet {
                    address: $from_address,
                    chain: $chain
                })

                MERGE (receiver:Wallet {
                    address: $to_address,
                    chain: $chain
                })

                MERGE (sender)-[
                    t:TRANSFER {
                        chain: $chain,
                        transaction_hash: $transaction_hash
                    }
                ]->(receiver)

                SET
                    t.asset = $asset,
                    t.value = $value,
                    t.category = $category,
                    t.block_number = $block_number,
                    t.timestamp = $timestamp,
                    t.contract_address = $contract_address
                """,
                from_address=transaction["from_address"],
                to_address=transaction["to_address"],
                chain=transaction.get(
                    "chain",
                    "ethereum",
                ).lower(),
                transaction_hash=transaction["transaction_hash"],
                asset=transaction["asset"],
                value=transaction["value"],
                category=transaction["category"],
                block_number=transaction["block_number"],
                timestamp=transaction["timestamp"],
                contract_address=transaction["contract_address"],
            )

    return {
        "ingested_count": len(transactions)
    }


def get_connected_wallets(
    address: str,
    chain: str,
):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MATCH (
                source:Wallet {
                    address: $address,
                    chain: $chain
                }
            )-[t:TRANSFER]-(connected:Wallet)

            RETURN
                connected.address AS address,
                connected.chain AS chain,
                t.transaction_hash AS transaction_hash,
                t.asset AS asset,
                t.value AS value,
                t.category AS category,
                t.block_number AS block_number,
                t.timestamp AS timestamp
            """,
            address=address,
            chain=chain.lower(),
        )

        return [dict(record) for record in result]


def get_two_hop_wallets(
    address: str,
    chain: str,
):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MATCH (
                source:Wallet {
                    address: $address,
                    chain: $chain
                }
            )-[:TRANSFER*1..2]-(connected:Wallet)

            WHERE connected.address <> source.address

            RETURN DISTINCT
                connected.address AS address,
                connected.chain AS chain
            """,
            address=address,
            chain=chain.lower(),
        )

        return [dict(record) for record in result]


def get_two_hop_paths(
    address: str,
    chain: str,
):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MATCH path = (
                source:Wallet {
                    address: $address,
                    chain: $chain
                }
            )-[:TRANSFER*1..2]-(connected:Wallet)

            WHERE connected.address <> source.address

            RETURN
                [node IN nodes(path) | node.address] AS wallets,

                [rel IN relationships(path) |
                    {
                        transaction_hash: rel.transaction_hash,
                        asset: rel.asset,
                        value: rel.value,
                        category: rel.category,
                        block_number: rel.block_number,
                        timestamp: rel.timestamp
                    }
                ] AS transfers
            """,
            address=address,
            chain=chain.lower(),
        )

        return [dict(record) for record in result]


def trace_wallet(
    address: str,
    chain: str,
    direction: str = "both",
    max_hops: int = 2,
):
    direction = direction.lower()
    chain = chain.lower()
    address = address.lower()

    if direction not in {"incoming", "outgoing", "both"}:
        raise ValueError(
            "direction must be incoming, outgoing, or both"
        )

    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")

    if max_hops > 5:
        raise ValueError(
            "max_hops cannot exceed 5 for the current implementation"
        )

    if direction == "outgoing":
        query = f"""
        MATCH path = (
            source:Wallet {{
                address: $address,
                chain: $chain
            }}
        )-[:TRANSFER*1..{max_hops}]->(target:Wallet)

        WHERE target.address <> source.address
          AND ALL(
              node IN nodes(path)
              WHERE SINGLE(
                  other IN nodes(path)
                  WHERE other.address = node.address
              )
          )

        RETURN
            [node IN nodes(path) | node.address] AS wallets,

            [rel IN relationships(path) |
                {{
                    transaction_hash: rel.transaction_hash,
                    asset: rel.asset,
                    value: rel.value,
                    category: rel.category,
                    block_number: rel.block_number,
                    timestamp: rel.timestamp,
                    contract_address: rel.contract_address
                }}
            ] AS transfers
        """

    elif direction == "incoming":
        query = f"""
        MATCH path = (
            source:Wallet {{
                address: $address,
                chain: $chain
            }}
        )<-[:TRANSFER*1..{max_hops}]-(target:Wallet)

        WHERE target.address <> source.address
          AND ALL(
              node IN nodes(path)
              WHERE SINGLE(
                  other IN nodes(path)
                  WHERE other.address = node.address
              )
          )

        RETURN
            [node IN nodes(path) | node.address] AS wallets,

            [rel IN relationships(path) |
                {{
                    transaction_hash: rel.transaction_hash,
                    asset: rel.asset,
                    value: rel.value,
                    category: rel.category,
                    block_number: rel.block_number,
                    timestamp: rel.timestamp,
                    contract_address: rel.contract_address
                }}
            ] AS transfers
        """

    else:
        # "both" means the union of two directional flow traversals:
        #   1. source -> outgoing flow
        #   2. source <- incoming flow
        #
        # This avoids the expensive undirected traversal:
        #   -[:TRANSFER*1..N]-
        #
        # which allows Neo4j to reverse relationship direction at every hop
        # and can create a large number of zig-zag path combinations.
        query = f"""
        CALL () {{
            MATCH path = (
                source:Wallet {{
                    address: $address,
                    chain: $chain
                }}
            )-[:TRANSFER*1..{max_hops}]->(target:Wallet)

            WHERE target.address <> source.address
              AND ALL(
                  node IN nodes(path)
                  WHERE SINGLE(
                      other IN nodes(path)
                      WHERE other.address = node.address
                  )
              )

            RETURN
                [node IN nodes(path) | node.address] AS wallets,

                [rel IN relationships(path) |
                    {{
                        transaction_hash: rel.transaction_hash,
                        asset: rel.asset,
                        value: rel.value,
                        category: rel.category,
                        block_number: rel.block_number,
                        timestamp: rel.timestamp,
                        contract_address: rel.contract_address
                    }}
                ] AS transfers

            UNION ALL

            MATCH path = (
                source:Wallet {{
                    address: $address,
                    chain: $chain
                }}
            )<-[:TRANSFER*1..{max_hops}]-(target:Wallet)

            WHERE target.address <> source.address
              AND ALL(
                  node IN nodes(path)
                  WHERE SINGLE(
                      other IN nodes(path)
                      WHERE other.address = node.address
                  )
              )

            RETURN
                [node IN nodes(path) | node.address] AS wallets,

                [rel IN relationships(path) |
                    {{
                        transaction_hash: rel.transaction_hash,
                        asset: rel.asset,
                        value: rel.value,
                        category: rel.category,
                        block_number: rel.block_number,
                        timestamp: rel.timestamp,
                        contract_address: rel.contract_address
                    }}
                ] AS transfers
        }}

        RETURN wallets, transfers
        """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain,
        )

        # Group traces by their wallet sequence.
        #
        # Example:
        #
        # A -> B -> C
        # A -> B -> C
        # A -> B -> C
        #
        # becomes one displayed path while all transaction
        # variants remain available in "path_variants".
        # Keep the total number of unique transaction sequences for
        # each wallet path, but return only a bounded number of examples.
        # This prevents large relationship combinations from creating
        # unnecessarily large API responses.
        MAX_PATH_VARIANTS = 10
        grouped_paths = {}

        for record in result:
            wallets = list(record["wallets"] or [])
            transfers = list(record["transfers"] or [])

            if len(wallets) < 2:
                continue

            # Wallet sequence is the presentation-level path identity.
            path_key = tuple(
                wallet.lower() if isinstance(wallet, str) else wallet
                for wallet in wallets
            )

            # Build a stable identity for this transaction sequence.
            transfer_key = tuple(
                transfer.get("transaction_hash")
                for transfer in transfers
            )

            if path_key not in grouped_paths:
                grouped_paths[path_key] = {
                    "wallets": wallets,
                    "transfers": transfers,
                    "path_count": 1,
                    "path_variants": [
                        {
                            "transfers": transfers,
                        }
                    ],
                    # Keep every unique transaction sequence key separately
                    # from the bounded response variants.
                    "_variant_keys": {transfer_key},
                }
            else:
                # Deduplicate against ALL previously seen transaction
                # sequences, not just the first MAX_PATH_VARIANTS returned.
                variant_keys = grouped_paths[path_key]["_variant_keys"]

                if transfer_key not in variant_keys:
                    variant_keys.add(transfer_key)

                    # path_count is the total number of unique transaction
                    # sequences for this wallet path.
                    grouped_paths[path_key]["path_count"] += 1

                    # Keep only a bounded sample in the API response.
                    if (
                        len(grouped_paths[path_key]["path_variants"])
                        < MAX_PATH_VARIANTS
                    ):
                        grouped_paths[path_key]["path_variants"].append(
                            {
                                "transfers": transfers,
                            }
                        )

        # Remove internal deduplication state before returning the response.
        for path in grouped_paths.values():
            path.pop("_variant_keys", None)

        traces = list(grouped_paths.values())

        # Keep the response bounded even when the graph contains
        # a very large number of unique wallet paths.
        traces = traces[:500]

        for trace in traces:
            trace["hop_count"] = len(trace["wallets"]) - 1
            trace["direction"] = direction

            # Useful frontend-friendly indicator.
            # path_count == 1 means there was only one transaction
            # sequence for this wallet path.
            trace["has_multiple_transaction_paths"] = (
                trace["path_count"] > 1
            )

        return traces

def get_peel_chain_candidates(
    address: str,
    chain: str = "ethereum",
    max_hops: int = 5,
):
    """
    Retrieve directional outgoing paths from a wallet for peel-chain analysis.

    This function ONLY reads existing Neo4j data.
    It does NOT call Alchemy or any external blockchain API.

    For every sequential hop, the returned transfer data contains:
    - sender wallet
    - receiver wallet
    - transaction hash
    - asset
    - value
    - timestamp
    - block number
    - contract address

    The explicit sender/receiver fields allow the service layer to verify
    that each outgoing transfer actually originates from the intermediate
    wallet reached by the previous transfer.
    """

    if not address:
        raise ValueError("Wallet address is required")

    chain = chain.lower().strip()
    address = address.lower().strip()

    if max_hops < 2:
        raise ValueError("max_hops must be at least 2")

    if max_hops > 5:
        raise ValueError("max_hops cannot exceed 5")

    query = f"""
    MATCH path =
        (source:Wallet {{address: $address, chain: $chain}})
        -[:TRANSFER*2..{max_hops}]->
        (target:Wallet)

    WHERE
        target.address <> source.address
        AND ALL(
            node IN nodes(path)
            WHERE SINGLE(
                other IN nodes(path)
                WHERE other.address = node.address
            )
        )

    WITH
        path,
        nodes(path) AS wallets,
        relationships(path) AS transfers

    RETURN
        [
            wallet IN wallets |
            {{
                address: wallet.address,
                chain: wallet.chain
            }}
        ] AS wallets,

        [
            index IN range(0, size(transfers) - 1) |
            {{
                from_address: wallets[index].address,
                to_address: wallets[index + 1].address,

                from_chain: wallets[index].chain,
                to_chain: wallets[index + 1].chain,

                transaction_hash: transfers[index].transaction_hash,
                chain: transfers[index].chain,
                asset: transfers[index].asset,
                value: transfers[index].value,
                category: transfers[index].category,
                block_number: transfers[index].block_number,
                timestamp: transfers[index].timestamp,
                contract_address: transfers[index].contract_address
            }}
        ] AS transfers

    LIMIT 500
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain,
        )

        return [record.data() for record in result]


def get_cross_chain_transfer_candidates(
    address: str,
    source_chain: str = "ethereum",
    target_chain: str | None = None,
    time_window_minutes: int = 120,
    value_tolerance: float = 0.20,
    limit: int = 250,
):
    """
    Retrieve cross-chain transfer pairs from existing Neo4j data.

    This function ONLY reads transfers already stored in Neo4j.
    It does NOT call Alchemy or any external blockchain API.

    A candidate is formed when:
    - the source wallet sends a transfer on source_chain;
    - another transfer exists on a different chain;
    - the two transfers occur within the requested time window;
    - their values are within the requested relative tolerance.

    The result is a research candidate, not confirmed bridge attribution.
    """

    if not address:
        raise ValueError("Wallet address is required")

    source_chain = source_chain.lower().strip()
    target_chain = target_chain.lower().strip() if target_chain else None

    if time_window_minutes < 1 or time_window_minutes > 1440:
        raise ValueError("time_window_minutes must be between 1 and 1440")

    if value_tolerance < 0 or value_tolerance > 1:
        raise ValueError("value_tolerance must be between 0 and 1")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    address = address.lower().strip()
    window_seconds = time_window_minutes * 60

    query = """
    MATCH (
        source_wallet:Wallet {
            address: $address,
            chain: $source_chain
        }
    )-[outgoing:TRANSFER]->(source_receiver:Wallet)

    WHERE outgoing.chain = $source_chain
      AND outgoing.timestamp IS NOT NULL
      AND outgoing.value IS NOT NULL

    MATCH (
        destination_sender:Wallet
    )-[incoming:TRANSFER]->(destination_wallet:Wallet)

    WHERE incoming.chain <> $source_chain
      AND ($target_chain IS NULL OR incoming.chain = $target_chain)
      AND incoming.timestamp IS NOT NULL
      AND incoming.value IS NOT NULL

    WITH
        source_wallet,
        source_receiver,
        outgoing,
        destination_sender,
        destination_wallet,
        incoming,
        abs(
            duration.inSeconds(
                datetime(outgoing.timestamp),
                datetime(incoming.timestamp)
            ).seconds
        ) AS time_gap_seconds

    WHERE time_gap_seconds <= $window_seconds

    WITH
        source_wallet,
        source_receiver,
        outgoing,
        destination_sender,
        destination_wallet,
        incoming,
        time_gap_seconds,
        abs(
            toFloat(outgoing.value) - toFloat(incoming.value)
        ) AS value_difference,
        CASE
            WHEN abs(toFloat(outgoing.value)) = 0
            THEN NULL
            ELSE abs(
                toFloat(outgoing.value) - toFloat(incoming.value)
            ) / abs(toFloat(outgoing.value))
        END AS value_difference_ratio

    WHERE value_difference_ratio IS NULL
       OR value_difference_ratio <= $value_tolerance

    RETURN
        source_wallet.address AS source_address,
        source_wallet.chain AS source_chain,
        source_receiver.address AS source_receiver_address,
        outgoing.chain AS source_transfer_chain,
        outgoing.transaction_hash AS source_transaction_hash,
        outgoing.asset AS source_asset,
        outgoing.value AS source_value,
        outgoing.category AS source_category,
        outgoing.block_number AS source_block_number,
        outgoing.timestamp AS source_timestamp,
        outgoing.contract_address AS source_contract_address,

        destination_sender.address AS destination_sender_address,
        destination_sender.chain AS destination_sender_chain,
        destination_wallet.address AS destination_address,
        destination_wallet.chain AS destination_chain,
        incoming.chain AS destination_transfer_chain,
        incoming.transaction_hash AS destination_transaction_hash,
        incoming.asset AS destination_asset,
        incoming.value AS destination_value,
        incoming.category AS destination_category,
        incoming.block_number AS destination_block_number,
        incoming.timestamp AS destination_timestamp,
        incoming.contract_address AS destination_contract_address,

        time_gap_seconds,
        value_difference
        ,
        value_difference_ratio

    ORDER BY
        time_gap_seconds ASC,
        value_difference_ratio ASC

    LIMIT $limit
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            source_chain=source_chain,
            target_chain=target_chain,
            window_seconds=window_seconds,
            value_tolerance=value_tolerance,
            limit=limit,
        )

        return [dict(record) for record in result]

def create_test_chain():
    transactions = [
        {
            "from_address": (
                "0x3c770607ee15cffef99672722845b0c397130abd"
            ),
            "to_address": (
                "0x1111111111111111111111111111111111111111"
            ),
            "transaction_hash": (
                "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            ),
            "asset": "TEST",
            "value": 50.0,
            "category": "erc20",
            "block_number": 999999,
            "timestamp": "2026-01-01T00:00:00Z",
            "contract_address": (
                "0x2222222222222222222222222222222222222222"
            ),
            "chain": "ethereum",
        }
    ]

    return ingest_transfer_batch(transactions)


def analyze_wallet_behavior(address: str, chain: str):
    chain = chain.lower()

    with get_neo4j_session() as session:
        wallet_result = session.run(
            """
            MATCH (wallet:Wallet {
                address: $address,
                chain: $chain
            })
            RETURN wallet.address AS address,
                   wallet.chain AS chain
            """,
            address=address,
            chain=chain,
        )

        wallet = wallet_result.single()

        if wallet is None:
            return None

        outgoing_connections_result = session.run(
            """
            MATCH (
                wallet:Wallet {
                    address: $address,
                    chain: $chain
                }
            )-[:TRANSFER {chain: $chain}]->(connected:Wallet)
            RETURN count(DISTINCT connected) AS count
            """,
            address=address,
            chain=chain,
        )

        incoming_connections_result = session.run(
            """
            MATCH (
                connected:Wallet
            )-[:TRANSFER {chain: $chain}]->(
                wallet:Wallet {
                    address: $address,
                    chain: $chain
                }
            )
            RETURN count(DISTINCT connected) AS count
            """,
            address=address,
            chain=chain,
        )

        outgoing_transaction_result = session.run(
            """
            MATCH (
                wallet:Wallet {
                    address: $address,
                    chain: $chain
                }
            )-[t:TRANSFER {chain: $chain}]->()
            RETURN count(t) AS count,
                   coalesce(sum(t.value), 0.0) AS value
            """,
            address=address,
            chain=chain,
        )

        incoming_transaction_result = session.run(
            """
            MATCH ()-[t:TRANSFER {chain: $chain}]->(
                wallet:Wallet {
                    address: $address,
                    chain: $chain
                }
            )
            RETURN count(t) AS count,
                   coalesce(sum(t.value), 0.0) AS value
            """,
            address=address,
            chain=chain,
        )

        outgoing_connections = (
            outgoing_connections_result.single()["count"]
        )

        incoming_connections = (
            incoming_connections_result.single()["count"]
        )

        outgoing_data = outgoing_transaction_result.single()
        incoming_data = incoming_transaction_result.single()

        outgoing_transaction_count = outgoing_data["count"]
        incoming_transaction_count = incoming_data["count"]

        outgoing_value = float(outgoing_data["value"] or 0.0)
        incoming_value = float(incoming_data["value"] or 0.0)

        asset_result = session.run(
            """
            MATCH (
                wallet:Wallet {
                    address: $address,
                    chain: $chain
                }
            )-[t:TRANSFER {chain: $chain}]-()
            RETURN DISTINCT t.asset AS asset
            """,
            address=address,
            chain=chain,
        )

        unique_assets = {
            record["asset"]
            for record in asset_result
            if record["asset"] is not None
        }

        return {
            "address": wallet["address"],
            "chain": wallet["chain"],
            "outgoing_connections": outgoing_connections,
            "incoming_connections": incoming_connections,
            "total_connections": (
                outgoing_connections + incoming_connections
            ),
            "outgoing_transaction_count": outgoing_transaction_count,
            "incoming_transaction_count": incoming_transaction_count,
            "total_transaction_count": (
                outgoing_transaction_count
                + incoming_transaction_count
            ),
            "outgoing_value": outgoing_value,
            "incoming_value": incoming_value,
            "unique_assets": len(unique_assets),
        }


def create_risk_entity(
    address: str,
    chain: str,
    entity_type: str,
    name: str,
    source: str,
    risk_category: str | None = None,
    confidence: float | None = None,
    evidence: str | None = None,
    updated_at: str | None = None,
):
    chain = chain.lower()

    intelligence_id = "|".join(
        [
            chain,
            address.lower(),
            entity_type.lower(),
            source.lower(),
            risk_category.lower()
            if risk_category
            else "",
        ]
    )

    with get_neo4j_session() as session:
        result = session.run(
            """
            MERGE (entity:RiskEntity {
                intelligence_id: $intelligence_id
            })

            SET
                entity.address = $address,
                entity.chain = $chain,
                entity.entity_type = $entity_type,
                entity.entity_name = $name,
                entity.intelligence_source = $source,
                entity.risk_category = $risk_category,
                entity.confidence = $confidence,
                entity.evidence = $evidence,
                entity.updated_at = $updated_at

            MERGE (wallet:Wallet {
                address: $address,
                chain: $chain
            })

            MERGE (wallet)-[:EXPOSED_TO]->(entity)

            RETURN
                entity.address AS address,
                entity.chain AS chain,
                entity.entity_type AS entity_type,
                entity.entity_name AS name,
                entity.intelligence_source AS source,
                entity.risk_category AS risk_category,
                entity.confidence AS confidence,
                entity.evidence AS evidence,
                entity.updated_at AS updated_at
            """,
            intelligence_id=intelligence_id,
            address=address,
            chain=chain,
            entity_type=entity_type,
            name=name,
            source=source,
            risk_category=risk_category,
            confidence=confidence,
            evidence=evidence,
            updated_at=updated_at,
        )

        return result.single()

def get_risk_entity_exposure(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    if max_hops < 0:
        raise ValueError("max_hops cannot be negative")

    if max_hops > 2:
        raise ValueError(
            "max_hops cannot exceed 2 for the current implementation"
        )

    with get_neo4j_session() as session:
        result = session.run(
            f"""
            MATCH transfer_path = (
                source:Wallet {{
                    address: $address,
                    chain: $chain
                }}
            )-[:TRANSFER*0..{max_hops}]-
            (wallet:Wallet)

            MATCH (wallet)-[:EXPOSED_TO]->(entity:RiskEntity)

            WITH
                entity,
                transfer_path,
                length(transfer_path) AS hop_count

            ORDER BY hop_count ASC

            WITH
                entity,
                collect(transfer_path)[0] AS shortest_path,
                hop_count

            RETURN
                entity.address AS risk_entity_address,
                entity.chain AS risk_entity_chain,
                entity.entity_type AS entity_type,
                entity.entity_name AS entity_name,
                entity.intelligence_source AS source,
                entity.risk_category AS risk_category,
                entity.confidence AS confidence,
                entity.evidence AS evidence,
                entity.updated_at AS updated_at,

                [node IN nodes(shortest_path) | node.address]
                    AS wallets,

                [
                    rel IN relationships(shortest_path) |
                    {{
                        transaction_hash: rel.transaction_hash,
                        asset: rel.asset,
                        value: rel.value,
                        category: rel.category,
                        block_number: rel.block_number,
                        timestamp: rel.timestamp,
                        contract_address: rel.contract_address
                    }}
                ] AS transfers,

                hop_count
            """,
            address=address,
            chain=chain.lower(),
        )

        exposures = []

        seen = set()

        for record in result:
            key = (
                record["risk_entity_address"],
                record["risk_entity_chain"],
                record["entity_type"],
                record["source"],
                record["risk_category"],
            )

            if key in seen:
                continue

            seen.add(key)

            exposures.append(
                {
                    "risk_entity_address": record[
                        "risk_entity_address"
                    ],
                    "risk_entity_chain": record[
                        "risk_entity_chain"
                    ],
                    "entity_type": record["entity_type"],
                    "entity_name": record["entity_name"],
                    "source": record["source"],
                    "risk_category": record["risk_category"],
                    "confidence": record["confidence"],
                    "evidence": record["evidence"],
                    "updated_at": record["updated_at"],
                    "wallets": record["wallets"],
                    "transfers": record["transfers"],
                    "hop_count": record["hop_count"],
                }
            )

        return exposures


def get_transaction_details(transaction_hash: str):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MATCH (sender:Wallet)-[t:TRANSFER {
                transaction_hash: $transaction_hash
            }]->(receiver:Wallet)

            RETURN
                t.transaction_hash AS transaction_hash,
                sender.address AS from_address,
                receiver.address AS to_address,
                sender.chain AS chain,
                t.asset AS asset,
                t.value AS value,
                t.category AS category,
                t.block_number AS block_number,
                t.timestamp AS timestamp,
                t.contract_address AS contract_address
            """,
            transaction_hash=transaction_hash,
        )

        record = result.single()

        if record is None:
            return None

        return dict(record)

def list_risk_entities(
    chain: str | None = None,
    entity_type: str | None = None,
    source: str | None = None,
    risk_category: str | None = None,
):
    query = """
        MATCH (entity:RiskEntity)
        WHERE
            ($chain IS NULL OR entity.chain = $chain)
            AND ($entity_type IS NULL OR entity.entity_type = $entity_type)
            AND ($source IS NULL OR entity.intelligence_source = $source)
            AND ($risk_category IS NULL OR entity.risk_category = $risk_category)

        RETURN
            entity.address AS address,
            entity.chain AS chain,
            entity.entity_type AS entity_type,
            entity.entity_name AS name,
            entity.intelligence_source AS source,
            entity.risk_category AS risk_category,
            entity.confidence AS confidence,
            entity.evidence AS evidence,
            entity.updated_at AS updated_at

        ORDER BY entity.chain, entity.entity_type, entity.entity_name
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            chain=chain.lower() if chain else None,
            entity_type=entity_type.lower() if entity_type else None,
            source=source.lower() if source else None,
            risk_category=risk_category.lower()
            if risk_category
            else None,
        )

        return [dict(record) for record in result]

def get_risk_entity(
    address: str,
    chain: str,
):
    query = """
        MATCH (entity:RiskEntity)
        WHERE
            entity.address = $address
            AND entity.chain = $chain

        RETURN
            entity.address AS address,
            entity.chain AS chain,
            entity.entity_type AS entity_type,
            entity.entity_name AS name,
            entity.intelligence_source AS source,
            entity.risk_category AS risk_category,
            entity.confidence AS confidence,
            entity.evidence AS evidence,
            entity.updated_at AS updated_at
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain.lower(),
        )

        record = result.single()

        if record is None:
            return None

        return dict(record)

def update_risk_entity(
    address: str,
    chain: str,
    entity_type: str | None = None,
    name: str | None = None,
    source: str | None = None,
    risk_category: str | None = None,
    confidence: float | None = None,
    evidence: str | None = None,
    updated_at: str | None = None,
):
    query = """
        MATCH (entity:RiskEntity)
        WHERE
            entity.address = $address
            AND entity.chain = $chain

        SET
            entity.entity_type =
                CASE
                    WHEN $entity_type IS NOT NULL
                    THEN $entity_type
                    ELSE entity.entity_type
                END,

            entity.entity_name =
                CASE
                    WHEN $name IS NOT NULL
                    THEN $name
                    ELSE entity.entity_name
                END,

            entity.intelligence_source =
                CASE
                    WHEN $source IS NOT NULL
                    THEN $source
                    ELSE entity.intelligence_source
                END,

            entity.risk_category =
                CASE
                    WHEN $risk_category IS NOT NULL
                    THEN $risk_category
                    ELSE entity.risk_category
                END,

            entity.confidence =
                CASE
                    WHEN $confidence IS NOT NULL
                    THEN $confidence
                    ELSE entity.confidence
                END,

            entity.evidence =
                CASE
                    WHEN $evidence IS NOT NULL
                    THEN $evidence
                    ELSE entity.evidence
                END,

            entity.updated_at =
                CASE
                    WHEN $updated_at IS NOT NULL
                    THEN $updated_at
                    ELSE entity.updated_at
                END

        RETURN
            entity.address AS address,
            entity.chain AS chain,
            entity.entity_type AS entity_type,
            entity.entity_name AS name,
            entity.intelligence_source AS source,
            entity.risk_category AS risk_category,
            entity.confidence AS confidence,
            entity.evidence AS evidence,
            entity.updated_at AS updated_at
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain.lower(),
            entity_type=entity_type.lower()
            if entity_type
            else None,
            name=name,
            source=source.lower()
            if source
            else None,
            risk_category=risk_category.lower()
            if risk_category
            else None,
            confidence=confidence,
            evidence=evidence,
            updated_at=updated_at,
        )

        record = result.single()

        if record is None:
            return None

        return dict(record)

def delete_risk_entity(
    address: str,
    chain: str,
):
    query = """
        MATCH (entity:RiskEntity)
        WHERE
            entity.address = $address
            AND entity.chain = $chain

        DETACH DELETE entity

        RETURN count(entity) AS deleted
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain.lower(),
        )

        record = result.single()

        if record is None:
            return 0

        return record["deleted"]

def analyze_wallet_graph(address: str, chain: str, max_hops: int = 2):
    chain = chain.lower()
    address = address.lower()

    query = """
    MATCH (wallet:Wallet {address: $address, chain: $chain})

    OPTIONAL MATCH (wallet)-[outgoing:TRANSFER {chain: $chain}]->(outgoing_wallet:Wallet)
    WITH wallet,
         collect({
             address: outgoing_wallet.address,
             transaction_hash: outgoing.transaction_hash,
             value: outgoing.value
         }) AS outgoing_transfers

    OPTIONAL MATCH (incoming_wallet:Wallet)-[incoming:TRANSFER {chain: $chain}]->(wallet)
    WITH wallet,
         outgoing_transfers,
         collect({
             address: incoming_wallet.address,
             transaction_hash: incoming.transaction_hash,
             value: incoming.value
         }) AS incoming_transfers

    RETURN
        wallet.address AS address,
        wallet.chain AS chain,
        outgoing_transfers,
        incoming_transfers
    """

    with get_neo4j_session() as session:
        record = session.run(
            query,
            address=address,
            chain=chain,
        ).single()

        if record is None:
            return None

        outgoing_transfers = [
            item
            for item in record["outgoing_transfers"]
            if item["address"] is not None
        ]

        incoming_transfers = [
            item
            for item in record["incoming_transfers"]
            if item["address"] is not None
        ]

        return {
            "address": record["address"],
            "chain": record["chain"],
            "outgoing_transfers": outgoing_transfers,
            "incoming_transfers": incoming_transfers,
        }

def get_multi_hop_risk_paths(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    chain = chain.lower()
    address = address.lower()

    if max_hops < 1:
        return []

    max_hops = min(max_hops, 2)

    query = f"""
    MATCH (wallet:Wallet {{address: $address, chain: $chain}})

    MATCH path =
        (wallet)-[:TRANSFER*1..{max_hops}]->(risk_wallet:Wallet)

    MATCH (risk_wallet)-[:EXPOSED_TO]->(entity:RiskEntity)

    WITH
        entity,
        path,
        length(path) AS hop_count,
        [node IN nodes(path) | node.address] AS wallets

    RETURN
        entity.address AS risk_entity_address,
        entity.chain AS risk_entity_chain,
        entity.entity_type AS entity_type,
        entity.entity_name AS entity_name,
        hop_count,
        wallets,
        [
            relationship IN relationships(path) |
            {{
                transaction_hash: relationship.transaction_hash,
                chain: relationship.chain,
                value: relationship.value,
                asset: relationship.asset,
                block_number: relationship.block_number,
                timestamp: relationship.timestamp,
                contract_address: relationship.contract_address
            }}
        ] AS transfers

    ORDER BY hop_count ASC
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain,
        )

        return [dict(record) for record in result]

def get_wallet_timeline(
    address: str,
    chain: str,
):
    address = address.lower()
    chain = chain.lower()

    query = """
    MATCH (wallet:Wallet {
        address: $address,
        chain: $chain
    })

    OPTIONAL MATCH (wallet)-[outgoing:TRANSFER {chain: $chain}]->(outgoing_wallet:Wallet)

    WITH wallet,
         collect({
             transaction_hash: outgoing.transaction_hash,
             chain: outgoing.chain,
             direction: "outgoing",
             counterparty: outgoing_wallet.address,
             asset: outgoing.asset,
             value: outgoing.value,
             block_number: outgoing.block_number,
             timestamp: outgoing.timestamp,
             contract_address: outgoing.contract_address
         }) AS outgoing_transactions

    OPTIONAL MATCH (incoming_wallet:Wallet)-[incoming:TRANSFER {chain: $chain}]->(wallet)

    WITH wallet,
         outgoing_transactions,
         collect({
             transaction_hash: incoming.transaction_hash,
             chain: incoming.chain,
             direction: "incoming",
             counterparty: incoming_wallet.address,
             asset: incoming.asset,
             value: incoming.value,
             block_number: incoming.block_number,
             timestamp: incoming.timestamp,
             contract_address: incoming.contract_address
         }) AS incoming_transactions

    RETURN
        wallet.address AS address,
        wallet.chain AS chain,
        outgoing_transactions,
        incoming_transactions
    """

    with get_neo4j_session() as session:
        record = session.run(
            query,
            address=address,
            chain=chain,
        ).single()

        if record is None:
            return None

        outgoing_transactions = [
            item
            for item in record["outgoing_transactions"]
            if item["transaction_hash"] is not None
        ]

        incoming_transactions = [
            item
            for item in record["incoming_transactions"]
            if item["transaction_hash"] is not None
        ]

        return {
            "address": record["address"],
            "chain": record["chain"],
            "outgoing_transactions": outgoing_transactions,
            "incoming_transactions": incoming_transactions,
        }






