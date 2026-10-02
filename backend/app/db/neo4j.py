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











def ingest_bitcoin_transaction_batch(transactions: list[dict]):
    """
    Ingest Bitcoin UTXO evidence without modifying the existing TRANSFER graph.

    Each transaction is represented as a BitcoinTransaction node. Known input
    addresses connect to that node through BITCOIN_INPUT relationships, and
    known output addresses connect through BITCOIN_OUTPUT relationships.

    This preserves Bitcoin's multi-input/multi-output structure instead of
    fabricating direct wallet-to-wallet TRANSFER relationships.
    """
    with get_neo4j_session() as session:
        ingested_count = 0
        input_link_count = 0
        output_link_count = 0

        for transaction in transactions:
            txid = transaction.get("txid")

            if not txid:
                raise ValueError("Bitcoin transaction is missing txid")

            # Create/update the Bitcoin transaction node once.
            session.run(
                """
                MERGE (bt:BitcoinTransaction {txid: $txid})
                SET
                    bt.block_height = $block_height,
                    bt.block_time = $block_time,
                    bt.confirmations = $confirmations,
                    bt.fees = $fees
                """,
                txid=txid,
                block_height=transaction.get("block_height"),
                block_time=transaction.get("block_time"),
                confirmations=transaction.get("confirmations"),
                fees=transaction.get("fees", 0),
            ).consume()

            # Prepare all input rows first.
            input_rows = []

            for item in transaction.get("inputs", []):
                addresses = item.get("addresses") or []

                for address in addresses:
                    if not address:
                        continue

                    input_rows.append(
                        {
                            "address": address,
                            "txid": txid,
                            "previous_txid": item.get("previous_txid", ""),
                            "previous_vout": int(
                                item.get("previous_vout", 0)
                            ),
                            "value": int(item.get("value", 0)),
                        }
                    )

            # Ingest all input relationships in one Cypher query.
            if input_rows:
                session.run(
                    """
                    UNWIND $rows AS row

                    MERGE (w:Wallet {
                        address: row.address,
                        chain: "bitcoin"
                    })

                    MATCH (bt:BitcoinTransaction {
                        txid: row.txid
                    })

                    MERGE (w)-[r:BITCOIN_INPUT {
                        txid: row.txid,
                        previous_txid: row.previous_txid,
                        previous_vout: row.previous_vout
                    }]->(bt)

                    SET r.value = row.value
                    """,
                    rows=input_rows,
                ).consume()

                input_link_count += len(input_rows)

            # Prepare all output rows first.
            output_rows = []

            for item in transaction.get("outputs", []):
                addresses = item.get("addresses") or []

                for address in addresses:
                    if not address:
                        continue

                    output_rows.append(
                        {
                            "address": address,
                            "txid": txid,
                            "vout": int(item.get("vout", 0)),
                            "value": int(item.get("value", 0)),
                        }
                    )

            # Ingest all output relationships in one Cypher query.
            if output_rows:
                session.run(
                    """
                    UNWIND $rows AS row

                    MATCH (bt:BitcoinTransaction {
                        txid: row.txid
                    })

                    MERGE (w:Wallet {
                        address: row.address,
                        chain: "bitcoin"
                    })

                    MERGE (bt)-[r:BITCOIN_OUTPUT {
                        txid: row.txid,
                        vout: row.vout
                    }]->(w)

                    SET r.value = row.value
                    """,
                    rows=output_rows,
                ).consume()

                output_link_count += len(output_rows)

            ingested_count += 1

    return {
        "ingested_count": ingested_count,
        "input_link_count": input_link_count,
        "output_link_count": output_link_count,
    }


def get_bitcoin_transaction_details(txid: str):

    """

    Retrieve one Bitcoin transaction and its known input/output

    wallet relationships from the Bitcoin-specific Neo4j graph.



    This function is intentionally separate from the existing

    EVM TRANSFER graph queries.

    """

    if not txid or not txid.strip():

        raise ValueError("Bitcoin transaction ID is required")



    txid = txid.strip()



    query = """

        MATCH (bt:BitcoinTransaction {txid: $txid})



        OPTIONAL MATCH (input_wallet:Wallet)

            -[input_rel:BITCOIN_INPUT {txid: $txid}]->

            (bt)



        OPTIONAL MATCH (bt)

            -[output_rel:BITCOIN_OUTPUT {txid: $txid}]->

            (output_wallet:Wallet)



        RETURN

            bt.txid AS txid,

            bt.block_height AS block_height,

            bt.block_time AS block_time,

            bt.confirmations AS confirmations,

            bt.fees AS fees,



            collect(DISTINCT {

                address: input_wallet.address,

                previous_txid: input_rel.previous_txid,

                previous_vout: input_rel.previous_vout,

                value: input_rel.value

            }) AS inputs,



            collect(DISTINCT {

                address: output_wallet.address,

                vout: output_rel.vout,

                value: output_rel.value

            }) AS outputs

    """



    with get_neo4j_session() as session:

        result = session.run(

            query,

            txid=txid,

        )



        record = result.single()



    if record is None:

        return None



    inputs = [

        item

        for item in record["inputs"]

        if item["address"] is not None

    ]



    outputs = [

        item

        for item in record["outputs"]

        if item["address"] is not None

    ]



    return {

        "txid": record["txid"],

        "block_height": record["block_height"],

        "block_time": record["block_time"],

        "confirmations": record["confirmations"],

        "fees": record["fees"],

        "inputs": inputs,

        "outputs": outputs,

    }





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











def trace_bitcoin_wallet(
    address: str,
    direction: str = "both",
    max_hops: int = 2,
):
    """
    Trace a Bitcoin wallet through the normalized UTXO graph.

    Bitcoin is stored as:
        Wallet -BITCOIN_INPUT-> BitcoinTransaction
        BitcoinTransaction -BITCOIN_OUTPUT-> Wallet

    A Wallet -> BitcoinTransaction -> Wallet pattern is counted as one
    logical wallet hop. Because Bitcoin transactions can contain multiple
    inputs and outputs, the returned transfer value is transaction-level
    output evidence and does not claim an exact input-to-output fund flow.

    Bitcoin tracing is intentionally bounded to two logical wallet hops.
    """
    direction = direction.lower()
    address = address.strip()

    if direction not in {"incoming", "outgoing", "both"}:
        raise ValueError(
            "direction must be incoming, outgoing, or both"
        )

    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")

    if max_hops > 2:
        raise ValueError(
            "Bitcoin tracing currently supports max_hops up to 2"
        )

    query_parts = []

    # Outgoing from the requested wallet:
    # requested -> transaction -> destination
    if direction in {"outgoing", "both"}:
        query_parts.append(
            """
            MATCH (source:Wallet {
                address: $address,
                chain: "bitcoin"
            })-[:BITCOIN_INPUT]->(tx1:BitcoinTransaction)
            WITH DISTINCT source, tx1
            MATCH (tx1)-[output1:BITCOIN_OUTPUT]->(target:Wallet {
                chain: "bitcoin"
            })
            WHERE target.address <> source.address
            WITH
                source,
                tx1,
                target,
                sum(output1.value) AS value1_satoshis
            RETURN
                [source.address, target.address] AS wallets,
                [{
                    transaction_hash: tx1.txid,
                    asset: "BTC",
                    value: value1_satoshis / 100000000.0,
                    value_satoshis: toInteger(value1_satoshis),
                    category: "bitcoin_utxo",
                    block_number: tx1.block_height,
                    timestamp: tx1.block_time,
                    contract_address: NULL
                }] AS transfers
            """
        )

        if max_hops >= 2:
            query_parts.append(
                """
                MATCH (source:Wallet {
                    address: $address,
                    chain: "bitcoin"
                })-[:BITCOIN_INPUT]->(tx1:BitcoinTransaction)
                WITH DISTINCT source, tx1
                MATCH (tx1)-[output1:BITCOIN_OUTPUT]->(middle:Wallet {
                    chain: "bitcoin"
                })
                WHERE middle.address <> source.address
                WITH
                    source,
                    tx1,
                    middle,
                    sum(output1.value) AS value1_satoshis
                MATCH (middle)-[:BITCOIN_INPUT]->(tx2:BitcoinTransaction)
                WHERE tx2.txid <> tx1.txid
                WITH DISTINCT
                    source,
                    tx1,
                    middle,
                    value1_satoshis,
                    tx2
                MATCH (tx2)-[output2:BITCOIN_OUTPUT]->(target:Wallet {
                    chain: "bitcoin"
                })
                WHERE
                    target.address <> source.address
                    AND target.address <> middle.address
                WITH
                    source,
                    tx1,
                    middle,
                    value1_satoshis,
                    tx2,
                    target,
                    sum(output2.value) AS value2_satoshis
                RETURN
                    [source.address, middle.address, target.address] AS wallets,
                    [
                        {
                            transaction_hash: tx1.txid,
                            asset: "BTC",
                            value: value1_satoshis / 100000000.0,
                            value_satoshis: toInteger(value1_satoshis),
                            category: "bitcoin_utxo",
                            block_number: tx1.block_height,
                            timestamp: tx1.block_time,
                            contract_address: NULL
                        },
                        {
                            transaction_hash: tx2.txid,
                            asset: "BTC",
                            value: value2_satoshis / 100000000.0,
                            value_satoshis: toInteger(value2_satoshis),
                            category: "bitcoin_utxo",
                            block_number: tx2.block_height,
                            timestamp: tx2.block_time,
                            contract_address: NULL
                        }
                    ] AS transfers
                """
            )

    # Incoming to the requested wallet:
    # source -> transaction -> requested
    # The presentation path starts at the requested wallet to preserve the
    # existing trace API convention for incoming traces.
    if direction in {"incoming", "both"}:
        query_parts.append(
            """
            MATCH (source:Wallet {
                address: $address,
                chain: "bitcoin"
            })<-[output1:BITCOIN_OUTPUT]-(tx1:BitcoinTransaction)
            WITH source, tx1, sum(output1.value) AS value1_satoshis
            MATCH (input1:Wallet {
                chain: "bitcoin"
            })-[:BITCOIN_INPUT]->(tx1)
            WHERE input1.address <> source.address
            RETURN
                [source.address, input1.address] AS wallets,
                [{
                    transaction_hash: tx1.txid,
                    asset: "BTC",
                    value: value1_satoshis / 100000000.0,
                    value_satoshis: toInteger(value1_satoshis),
                    category: "bitcoin_utxo",
                    block_number: tx1.block_height,
                    timestamp: tx1.block_time,
                    contract_address: NULL
                }] AS transfers
            """
        )

        if max_hops >= 2:
            query_parts.append(
                """
                MATCH (source:Wallet {
                    address: $address,
                    chain: "bitcoin"
                })<-[output1:BITCOIN_OUTPUT]-(tx1:BitcoinTransaction)
                WITH source, tx1, sum(output1.value) AS value1_satoshis
                MATCH (middle:Wallet {
                    chain: "bitcoin"
                })-[:BITCOIN_INPUT]->(tx1)
                WHERE middle.address <> source.address
                WITH DISTINCT source, tx1, middle, value1_satoshis
                MATCH (middle)<-[output2:BITCOIN_OUTPUT]-(tx2:BitcoinTransaction)
                WHERE tx2.txid <> tx1.txid
                WITH source, tx1, middle, value1_satoshis, tx2, sum(output2.value) AS value2_satoshis
                MATCH (target:Wallet {
                    chain: "bitcoin"
                })-[:BITCOIN_INPUT]->(tx2)
                WHERE
                    target.address <> source.address
                    AND target.address <> middle.address
                WITH DISTINCT source, tx1, middle, value1_satoshis, tx2, value2_satoshis, target
                RETURN
                    [source.address, middle.address, target.address] AS wallets,
                    [
                        {
                            transaction_hash: tx1.txid,
                            asset: "BTC",
                            value: value1_satoshis / 100000000.0,
                            value_satoshis: toInteger(value1_satoshis),
                            category: "bitcoin_utxo",
                            block_number: tx1.block_height,
                            timestamp: tx1.block_time,
                            contract_address: NULL
                        },
                        {
                            transaction_hash: tx2.txid,
                            asset: "BTC",
                            value: value2_satoshis / 100000000.0,
                            value_satoshis: toInteger(value2_satoshis),
                            category: "bitcoin_utxo",
                            block_number: tx2.block_height,
                            timestamp: tx2.block_time,
                            contract_address: NULL
                        }
                    ] AS transfers
                """
            )

    query = "\nUNION ALL\n".join(query_parts)

    from datetime import datetime, timezone

    with get_neo4j_session() as session:
        result = session.run(query, address=address)

        MAX_PATH_VARIANTS = 10
        grouped_paths = {}

        for record in result:
            wallets = list(record["wallets"] or [])
            transfers = list(record["transfers"] or [])

            # Normalize raw Bitcoin block timestamps to the same
            # JSON-friendly ISO-8601 representation used by the
            # other Bitcoin graph helpers.
            for transfer in transfers:
                block_time = transfer.get("timestamp")

                if block_time is None:
                    continue

                try:
                    transfer["timestamp"] = (
                        datetime.fromtimestamp(
                            int(block_time),
                            tz=timezone.utc,
                        )
                        .isoformat()
                        .replace("+00:00", "Z")
                    )
                except (TypeError, ValueError, OverflowError):
                    transfer["timestamp"] = None

            if len(wallets) < 2:
                continue

            # Bitcoin addresses are case-sensitive for Base58 forms, so do
            # not lowercase the wallet sequence used as the grouping key.
            path_key = tuple(wallets)
            transfer_key = tuple(
                transfer.get("transaction_hash")
                for transfer in transfers
            )

            if path_key not in grouped_paths:
                grouped_paths[path_key] = {
                    "wallets": wallets,
                    "transfers": transfers,
                    "path_count": 1,
                    "path_variants": [{"transfers": transfers}],
                    "_variant_keys": {transfer_key},
                }
            else:
                variant_keys = grouped_paths[path_key]["_variant_keys"]

                if transfer_key not in variant_keys:
                    variant_keys.add(transfer_key)
                    grouped_paths[path_key]["path_count"] += 1

                    if len(grouped_paths[path_key]["path_variants"]) < MAX_PATH_VARIANTS:
                        grouped_paths[path_key]["path_variants"].append(
                            {"transfers": transfers}
                        )

    for path in grouped_paths.values():
        path.pop("_variant_keys", None)

    traces = list(grouped_paths.values())[:500]

    for trace in traces:
        trace["hop_count"] = len(trace["wallets"]) - 1
        trace["direction"] = direction
        trace["has_multiple_transaction_paths"] = trace["path_count"] > 1

    return traces


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











def get_bitcoin_peel_chain_candidates(
    address: str,
    max_hops: int = 5,
):
    """
    Retrieve Bitcoin peel-chain candidates from the normalized UTXO graph.

    Bitcoin is represented as:
        Wallet -BITCOIN_INPUT-> BitcoinTransaction
        BitcoinTransaction -BITCOIN_OUTPUT-> Wallet

    One logical wallet hop is:
        Wallet -> BitcoinTransaction -> Wallet

    The query is generated for the requested hop count. Each output
    relationship is bound directly in the path so the returned transfer
    evidence is guaranteed to belong to the corresponding transaction.

    This preserves Bitcoin's UTXO model and does not claim that a
    particular input funded a particular output in a multi-input /
    multi-output transaction.
    """
    if not address:
        raise ValueError("Wallet address is required")

    address = address.strip()

    if max_hops < 2:
        raise ValueError("max_hops must be at least 2")

    if max_hops > 5:
        raise ValueError("max_hops cannot exceed 5")

    # Build an explicitly directed UTXO path:
    #
    # source -> tx1 -> wallet1 -> tx2 -> wallet2 -> ...
    #
    # Each BITCOIN_OUTPUT relationship is named so its value can be
    # returned without issuing additional MATCH clauses.
    wallet_names = ["source"]
    path_parts = [
        '(source:Wallet {address: $address, chain: "bitcoin"})'
    ]
    output_rel_names = []

    for hop in range(1, max_hops + 1):
        tx_name = f"tx{hop}"
        wallet_name = "target" if hop == max_hops else f"wallet{hop}"
        output_rel_name = f"output_rel{hop}"

        wallet_names.append(wallet_name)
        output_rel_names.append(output_rel_name)

        path_parts.append(
            f"-[:BITCOIN_INPUT]->({tx_name}:BitcoinTransaction)"
        )
        path_parts.append(
            f'-[{output_rel_name}:BITCOIN_OUTPUT]->'
            f'({wallet_name}:Wallet {{chain: "bitcoin"}})'
        )

    pattern = "".join(path_parts)

    # Do not allow the same wallet to appear twice in one candidate path.
    uniqueness_conditions = []
    for index in range(1, len(wallet_names)):
        for previous_index in range(index):
            uniqueness_conditions.append(
                f"{wallet_names[index]}.address <> "
                f"{wallet_names[previous_index]}.address"
            )

    uniqueness_clause = " AND\n        ".join(uniqueness_conditions)

    wallet_return = ",\n".join(
        f"""            {{
                address: {wallet_name}.address,
                chain: {wallet_name}.chain
            }}"""
        for wallet_name in wallet_names
    )

    transfer_return = ",\n".join(
        f"""            {{
                from_address: {wallet_names[index]}.address,
                to_address: {wallet_names[index + 1]}.address,
                from_chain: "bitcoin",
                to_chain: "bitcoin",
                transaction_hash: tx{index + 1}.txid,
                chain: "bitcoin",
                asset: "BTC",
                value: toFloat({output_rel_names[index]}.value) / 100000000.0,
                value_satoshis: toInteger({output_rel_names[index]}.value),
                category: "bitcoin_utxo",
                block_number: tx{index + 1}.block_height,
                timestamp: tx{index + 1}.block_time,
                contract_address: NULL
            }}"""
        for index in range(max_hops)
    )

    query = f"""
    MATCH {pattern}

    WHERE
        {uniqueness_clause}

    RETURN
        [
{wallet_return}
        ] AS wallets,

        [
{transfer_return}
        ] AS transfers

    LIMIT 500
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
        )
        return [record.data() for record in result]


def get_bitcoin_cross_chain_transfer_candidates(
    address: str,
    target_chain: str | None = None,
    time_window_minutes: int = 120,
    value_tolerance: float = 0.20,
    limit: int = 250,
):
    """
    Retrieve Bitcoin-to-EVM cross-chain research candidates from Neo4j.

    Bitcoin is read from the normalized UTXO graph:
        Wallet -> BitcoinTransaction -> Wallet

    The Bitcoin source value is converted from satoshis to BTC. The
    destination side uses the existing TRANSFER graph used by EVM chains.

    This is transaction-graph correlation only. It does not prove that a
    specific Bitcoin input funded a specific output or that a bridge was used.
    """
    if not address:
        raise ValueError("Wallet address is required")

    address = address.strip()
    target_chain = target_chain.lower().strip() if target_chain else None

    if time_window_minutes < 1 or time_window_minutes > 1440:
        raise ValueError("time_window_minutes must be between 1 and 1440")

    if value_tolerance < 0 or value_tolerance > 1:
        raise ValueError("value_tolerance must be between 0 and 1")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    window_seconds = time_window_minutes * 60

    query = """
    MATCH (
        source_wallet:Wallet {
            address: $address,
            chain: "bitcoin"
        }
    )-[:BITCOIN_INPUT]->(source_tx:BitcoinTransaction)

    WITH DISTINCT source_wallet, source_tx

    MATCH (source_tx)-[source_output:BITCOIN_OUTPUT]->(
        source_receiver:Wallet {chain: "bitcoin"}
    )

    WHERE source_receiver.address <> source_wallet.address
      AND source_tx.block_time IS NOT NULL
      AND source_output.value IS NOT NULL

    WITH
        source_wallet,
        source_tx,
        source_receiver,
        sum(toInteger(source_output.value)) / 100000000.0 AS source_value_btc,
        datetime({epochSeconds: toInteger(source_tx.block_time)}) AS source_datetime

    MATCH (
        destination_sender:Wallet
    )-[incoming:TRANSFER]->(destination_wallet:Wallet)

    WHERE incoming.chain <> "bitcoin"
      AND ($target_chain IS NULL OR incoming.chain = $target_chain)
      AND incoming.timestamp IS NOT NULL
      AND incoming.value IS NOT NULL

    WITH
        source_wallet,
        source_tx,
        source_receiver,
        source_value_btc,
        source_datetime,
        destination_sender,
        destination_wallet,
        incoming,
        abs(
            duration.inSeconds(
                source_datetime,
                datetime(incoming.timestamp)
            ).seconds
        ) AS time_gap_seconds

    WHERE time_gap_seconds <= $window_seconds

    WITH
        source_wallet,
        source_tx,
        source_receiver,
        source_value_btc,
        source_datetime,
        destination_sender,
        destination_wallet,
        incoming,
        time_gap_seconds

    RETURN
        source_wallet.address AS source_address,
        "bitcoin" AS source_chain,
        source_receiver.address AS source_receiver_address,
        "bitcoin" AS source_transfer_chain,
        source_tx.txid AS source_transaction_hash,
        "BTC" AS source_asset,
        source_value_btc AS source_value,
        "bitcoin_utxo" AS source_category,
        source_tx.block_height AS source_block_number,
        toString(source_datetime) AS source_timestamp,
        NULL AS source_contract_address,

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
        NULL AS value_difference,
        NULL AS value_difference_ratio,
        false AS value_comparable

    ORDER BY
        time_gap_seconds ASC

    LIMIT $limit
    """

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            target_chain=target_chain,
            window_seconds=window_seconds,
            value_tolerance=value_tolerance,
            limit=limit,
        )
        return [dict(record) for record in result]

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












def _analyze_bitcoin_wallet_behavior(address: str):
    """
    Calculate wallet behavior from the Bitcoin UTXO graph.

    Bitcoin is represented as:
        Wallet -BITCOIN_INPUT-> BitcoinTransaction
        BitcoinTransaction -BITCOIN_OUTPUT-> Wallet

    Values are transaction-level output evidence and do not claim an
    exact input-to-output fund flow for multi-input/multi-output
    transactions.
    """
    address = address.strip()

    neighbors = _get_bitcoin_wallet_neighbors(address)

    outgoing = [
        item
        for item in neighbors
        if item.get("direction") == "outgoing"
    ]

    incoming = [
        item
        for item in neighbors
        if item.get("direction") == "incoming"
    ]

    outgoing_connections = {
        item.get("address")
        for item in outgoing
        if item.get("address")
    }

    incoming_connections = {
        item.get("address")
        for item in incoming
        if item.get("address")
    }

    outgoing_transactions = {
        item.get("transaction_hash")
        for item in outgoing
        if item.get("transaction_hash")
    }

    incoming_transactions = {
        item.get("transaction_hash")
        for item in incoming
        if item.get("transaction_hash")
    }

    outgoing_value = sum(
        float(item.get("value") or 0.0)
        for item in outgoing
    )

    incoming_value = sum(
        float(item.get("value") or 0.0)
        for item in incoming
    )

    return {
        "address": address,
        "chain": "bitcoin",
        "outgoing_connections": len(outgoing_connections),
        "incoming_connections": len(incoming_connections),
        "total_connections": (
            len(outgoing_connections)
            + len(incoming_connections)
        ),
        "outgoing_transaction_count": len(outgoing_transactions),
        "incoming_transaction_count": len(incoming_transactions),
        "total_transaction_count": (
            len(outgoing_transactions)
            + len(incoming_transactions)
        ),
        "outgoing_value": outgoing_value,
        "incoming_value": incoming_value,
        "unique_assets": 1 if neighbors else 0,
    }

def analyze_wallet_behavior(address: str, chain: str):



    chain = chain.lower()

    if chain == "bitcoin":
        return _analyze_bitcoin_wallet_behavior(address)








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

    address = address.lower().strip()
    chain = chain.lower().strip()

    if chain == "bitcoin":
        return _get_bitcoin_risk_entity_exposure(
            address=address,
            max_hops=max_hops,
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
            chain=chain,
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
                    "risk_entity_address": record["risk_entity_address"],
                    "risk_entity_chain": record["risk_entity_chain"],
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








def _bitcoin_transaction_timestamp(block_time):
    """Return a timeline-compatible ISO-8601 timestamp for a Unix block time."""
    if block_time is None:
        return None

    from datetime import datetime, timezone

    try:
        return datetime.fromtimestamp(
            int(block_time),
            tz=timezone.utc,
        ).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError):
        return None


def _get_bitcoin_wallet_neighbors(address: str):
    """
    Return one logical Bitcoin wallet-to-wallet connection per
    counterparty + transaction.

    Bitcoin remains represented in Neo4j as:
        Wallet -BITCOIN_INPUT-> BitcoinTransaction
        BitcoinTransaction -BITCOIN_OUTPUT-> Wallet

    A Bitcoin transaction can have many inputs and outputs, so this helper
    deliberately does not claim an exact input-to-output fund flow. It
    collapses multiple UTXO rows into one transaction-level connection for
    each counterparty.
    """
    address = address.strip()

    query_outgoing = """
    MATCH (source:Wallet {
        address: $address,
        chain: "bitcoin"
    })-[:BITCOIN_INPUT]->(tx:BitcoinTransaction)
    WITH DISTINCT source, tx
    MATCH (tx)-[output:BITCOIN_OUTPUT]->(destination:Wallet {
        chain: "bitcoin"
    })
    WHERE destination.address <> source.address
    WITH
        destination.address AS address,
        tx.txid AS transaction_hash,
        sum(output.value) AS value_satoshis,
        tx.block_height AS block_number,
        tx.block_time AS block_time
    RETURN
        address,
        transaction_hash,
        value_satoshis,
        block_number,
        block_time,
        "outgoing" AS direction
    ORDER BY block_number, transaction_hash, address
    """

    query_incoming = """
    MATCH (source:Wallet {
        chain: "bitcoin"
    })-[:BITCOIN_INPUT]->(tx:BitcoinTransaction)
    WITH DISTINCT source, tx
    MATCH (tx)-[output:BITCOIN_OUTPUT]->(destination:Wallet {
        address: $address,
        chain: "bitcoin"
    })
    WHERE source.address <> destination.address
    WITH
        source.address AS address,
        tx.txid AS transaction_hash,
        sum(output.value) AS value_satoshis,
        tx.block_height AS block_number,
        tx.block_time AS block_time
    RETURN
        address,
        transaction_hash,
        value_satoshis,
        block_number,
        block_time,
        "incoming" AS direction
    ORDER BY block_number, transaction_hash, address
    """

    neighbors = []

    with get_neo4j_session() as session:
        for query in (query_outgoing, query_incoming):
            result = session.run(query, address=address)

            for record in result:
                item = dict(record)
                value_satoshis = item.get("value_satoshis")

                try:
                    value_satoshis = int(value_satoshis or 0)
                except (TypeError, ValueError):
                    value_satoshis = 0

                neighbors.append(
                    {
                        "address": item.get("address"),
                        "transaction_hash": item.get("transaction_hash"),
                        "value": value_satoshis / 100_000_000,
                        "value_satoshis": value_satoshis,
                        "chain": "bitcoin",
                        "asset": "BTC",
                        "category": "bitcoin_utxo",
                        "block_number": item.get("block_number"),
                        "timestamp": _bitcoin_transaction_timestamp(
                            item.get("block_time")
                        ),
                        "contract_address": None,
                        "direction": item.get("direction"),
                    }
                )

    return [item for item in neighbors if item["address"]]

def _get_bitcoin_risk_entities(address: str):
    """Return risk intelligence directly attached to a Bitcoin wallet."""
    query = """
    MATCH (wallet:Wallet {
        address: $address,
        chain: "bitcoin"
    })
    MATCH (wallet)-[:EXPOSED_TO]->(entity:RiskEntity)
    RETURN
        entity.address AS risk_entity_address,
        entity.chain AS risk_entity_chain,
        entity.entity_type AS entity_type,
        entity.entity_name AS entity_name,
        entity.intelligence_source AS source,
        entity.risk_category AS risk_category,
        entity.confidence AS confidence,
        entity.evidence AS evidence,
        entity.updated_at AS updated_at
    """

    with get_neo4j_session() as session:
        return [dict(record) for record in session.run(query, address=address)]


def _analyze_bitcoin_wallet_graph(address: str):
    neighbors = _get_bitcoin_wallet_neighbors(address)

    outgoing_transfers = [
        {
            key: item[key]
            for key in (
                "address",
                "transaction_hash",
                "value",
                "value_satoshis",
                "chain",
                "asset",
                "category",
                "block_number",
                "timestamp",
                "contract_address",
            )
        }
        for item in neighbors
        if item["direction"] == "outgoing"
    ]

    incoming_transfers = [
        {
            key: item[key]
            for key in (
                "address",
                "transaction_hash",
                "value",
                "value_satoshis",
                "chain",
                "asset",
                "category",
                "block_number",
                "timestamp",
                "contract_address",
            )
        }
        for item in neighbors
        if item["direction"] == "incoming"
    ]

    return {
        "address": address,
        "chain": "bitcoin",
        "outgoing_transfers": outgoing_transfers,
        "incoming_transfers": incoming_transfers,
    }


def _get_bitcoin_multi_hop_risk_paths(
    address: str,
    max_hops: int = 2,
    max_results: int = 100,
):
    """
    Resolve Bitcoin multi-hop risk paths with one bounded Neo4j request.

    Bitcoin wallet hops are counted as:
        Wallet -> BitcoinTransaction -> Wallet = 1 hop

    The traversal is capped at two wallet hops and the returned risk-path
    set is capped to keep API response size predictable for the UI.
    """
    if max_hops < 1:
        return []

    max_hops = min(max_hops, 2)
    max_results = max(1, min(max_results, 1000))
    address = address.strip()

    query_parts = []

    if max_hops >= 1:
        query_parts.append(
            """
            MATCH (source:Wallet {
                address: $address,
                chain: "bitcoin"
            })-[:BITCOIN_INPUT]->(tx1:BitcoinTransaction)
            WITH DISTINCT source, tx1
            MATCH (tx1)-[output1:BITCOIN_OUTPUT]->(target:Wallet {
                chain: "bitcoin"
            })
            WHERE target.address <> source.address
            WITH
                source,
                tx1,
                target,
                sum(output1.value) AS value1_satoshis
            MATCH (target)-[:EXPOSED_TO]->(entity:RiskEntity)
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
                1 AS hop_count,
                [source.address, target.address] AS wallets,
                [{
                    transaction_hash: tx1.txid,
                    chain: "bitcoin",
                    value: value1_satoshis / 100000000.0,
                    value_satoshis: toInteger(value1_satoshis),
                    asset: "BTC",
                    category: "bitcoin_utxo",
                    block_number: tx1.block_height,
                    timestamp: CASE
                        WHEN tx1.block_time IS NULL THEN NULL
                        ELSE datetime({epochSeconds: tx1.block_time})
                    END,
                    contract_address: NULL
                }] AS transfers
            """
        )

    if max_hops >= 2:
        query_parts.append(
            """
            MATCH (source:Wallet {
                address: $address,
                chain: "bitcoin"
            })-[:BITCOIN_INPUT]->(tx1:BitcoinTransaction)
            WITH DISTINCT source, tx1
            MATCH (tx1)-[output1:BITCOIN_OUTPUT]->(middle:Wallet {
                chain: "bitcoin"
            })
            WHERE middle.address <> source.address
            WITH
                source,
                tx1,
                middle,
                sum(output1.value) AS value1_satoshis
            MATCH (middle)-[:BITCOIN_INPUT]->(tx2:BitcoinTransaction)
            WHERE tx2.txid <> tx1.txid
            WITH DISTINCT
                source,
                tx1,
                middle,
                value1_satoshis,
                tx2
            MATCH (tx2)-[output2:BITCOIN_OUTPUT]->(target:Wallet {
                chain: "bitcoin"
            })
            WHERE
                target.address <> middle.address
                AND target.address <> source.address
            WITH
                source,
                tx1,
                middle,
                value1_satoshis,
                tx2,
                target,
                sum(output2.value) AS value2_satoshis
            MATCH (target)-[:EXPOSED_TO]->(entity:RiskEntity)
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
                2 AS hop_count,
                [source.address, middle.address, target.address] AS wallets,
                [
                    {
                        transaction_hash: tx1.txid,
                        chain: "bitcoin",
                        value: value1_satoshis / 100000000.0,
                        value_satoshis: toInteger(value1_satoshis),
                        asset: "BTC",
                        category: "bitcoin_utxo",
                        block_number: tx1.block_height,
                        timestamp: CASE
                            WHEN tx1.block_time IS NULL THEN NULL
                            ELSE datetime({epochSeconds: tx1.block_time})
                        END,
                        contract_address: NULL
                    },
                    {
                        transaction_hash: tx2.txid,
                        chain: "bitcoin",
                        value: value2_satoshis / 100000000.0,
                        value_satoshis: toInteger(value2_satoshis),
                        asset: "BTC",
                        category: "bitcoin_utxo",
                        block_number: tx2.block_height,
                        timestamp: CASE
                            WHEN tx2.block_time IS NULL THEN NULL
                            ELSE datetime({epochSeconds: tx2.block_time})
                        END,
                        contract_address: NULL
                    }
                ] AS transfers
            """
        )

    # UNION ALL keeps each hop pattern set-based. The final cap prevents a
    # large RiskEntity fan-out from producing an unbounded API response.
    query = (
        "\nUNION ALL\n".join(query_parts)
        + "\nORDER BY hop_count ASC\nLIMIT $max_results"
    )

    with get_neo4j_session() as session:
        result = session.run(
            query,
            address=address,
            max_results=max_results,
        )

        rows = [dict(record) for record in result]

    # Keep the nearest path for each RiskEntity. This is performed after the
    # database-side result cap so the API payload stays bounded.
    results = []
    seen_entities = set()

    for entity in rows:
        key = (
            entity.get("risk_entity_address"),
            entity.get("risk_entity_chain"),
            entity.get("entity_type"),
            entity.get("source"),
            entity.get("risk_category"),
        )

        if key in seen_entities:
            continue

        seen_entities.add(key)
        results.append(entity)

    return results


def _get_bitcoin_wallet_timeline(address: str):
    neighbors = _get_bitcoin_wallet_neighbors(address)

    outgoing_transactions = []
    incoming_transactions = []

    for item in neighbors:
        transaction = {
            "transaction_hash": item["transaction_hash"],
            "chain": "bitcoin",
            "direction": item["direction"],
            "counterparty": item["address"],
            "asset": "BTC",
            "value": item["value"],
            "value_satoshis": item["value_satoshis"],
            "block_number": item["block_number"],
            "timestamp": item["timestamp"],
            "contract_address": None,
        }

        if item["direction"] == "outgoing":
            outgoing_transactions.append(transaction)
        else:
            incoming_transactions.append(transaction)

    return {
        "address": address,
        "chain": "bitcoin",
        "outgoing_transactions": outgoing_transactions,
        "incoming_transactions": incoming_transactions,
    }


def _get_bitcoin_risk_entity_exposure(
    address: str,
    max_hops: int = 2,
):
    return _get_bitcoin_multi_hop_risk_paths(
        address=address,
        max_hops=max_hops,
    )


def analyze_wallet_graph(address: str, chain: str, max_hops: int = 2):
    chain = chain.lower()

    if chain == "bitcoin":
        return _analyze_bitcoin_wallet_graph(address.strip())

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

    if chain == "bitcoin":
        bitcoin_address = address.strip()
    else:
        address = address.lower()
        bitcoin_address = None

    if max_hops < 1:
        return []

    max_hops = min(max_hops, 2)

    if chain == "bitcoin":
        return _get_bitcoin_multi_hop_risk_paths(
            address=bitcoin_address,
            max_hops=max_hops,
        )

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
    chain = chain.lower()

    if chain == "bitcoin":
        return _get_bitcoin_wallet_timeline(address.strip())

    address = address.lower()

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
