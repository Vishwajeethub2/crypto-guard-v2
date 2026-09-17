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
                t.transaction_hash AS transaction_hash
            """,
            from_address=transaction["from_address"],
            to_address=transaction["to_address"],
            chain=transaction.get("chain", "ethereum").lower(),
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
                chain=transaction.get("chain", "ethereum").lower(),
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

    if direction not in {"incoming", "outgoing", "both"}:
        raise ValueError(
            "direction must be incoming, outgoing, or both"
        )

    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")

    if max_hops > 2:
        raise ValueError(
            "max_hops cannot exceed 2 for the current implementation"
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
        query = f"""
        MATCH path = (
            source:Wallet {{
                address: $address,
                chain: $chain
            }}
        )-[:TRANSFER*1..{max_hops}]-(target:Wallet)

        WHERE target.address <> source.address

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

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            chain=chain,
        )

        traces = []

        for record in result:
            traces.append(
                {
                    "wallets": record["wallets"],
                    "transfers": record["transfers"],
                    "hop_count": len(record["wallets"]) - 1,
                    "direction": direction,
                }
            )

        return traces


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
            )-[:TRANSFER]->(connected:Wallet)
            RETURN count(DISTINCT connected) AS count
            """,
            address=address,
            chain=chain,
        )

        incoming_connections_result = session.run(
            """
            MATCH (
                connected:Wallet
            )-[:TRANSFER]->(
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
            )-[t:TRANSFER]->()
            RETURN count(t) AS count,
                   coalesce(sum(t.value), 0.0) AS value
            """,
            address=address,
            chain=chain,
        )

        incoming_transaction_result = session.run(
            """
            MATCH ()-[t:TRANSFER]->(
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
            )-[t:TRANSFER]-()
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
):
    with get_neo4j_session() as session:
        result = session.run(
            """
            MERGE (w:Wallet {
                address: $address,
                chain: $chain
            })

            SET
                w:RiskEntity,
                w.entity_type = $entity_type,
                w.entity_name = $name,
                w.intelligence_source = $source

            RETURN
                w.address AS address,
                w.chain AS chain,
                w.entity_type AS entity_type,
                w.entity_name AS name,
                w.intelligence_source AS source
            """,
            address=address,
            chain=chain.lower(),
            entity_type=entity_type,
            name=name,
            source=source,
        )

        return result.single()


def get_risk_entity_exposure(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")

    if max_hops > 2:
        raise ValueError(
            "max_hops cannot exceed 2 for the current implementation"
        )

    with get_neo4j_session() as session:
        result = session.run(
            f"""
            MATCH path = (
                source:Wallet {{
                    address: $address,
                    chain: $chain
                }}
            )-[:TRANSFER*1..{max_hops}]-
            (entity:RiskEntity)

            RETURN
                entity.address AS risk_entity_address,
                entity.chain AS risk_entity_chain,
                entity.entity_type AS entity_type,
                entity.entity_name AS entity_name,
                entity.intelligence_source AS source,

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
            """,
            address=address,
            chain=chain.lower(),
        )

        exposures = []

        for record in result:
            exposures.append(
                {
                    "risk_entity_address": record["risk_entity_address"],
                    "risk_entity_chain": record["risk_entity_chain"],
                    "entity_type": record["entity_type"],
                    "entity_name": record["entity_name"],
                    "source": record["source"],
                    "wallets": record["wallets"],
                    "transfers": record["transfers"],
                    "hop_count": len(record["wallets"]) - 1,
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