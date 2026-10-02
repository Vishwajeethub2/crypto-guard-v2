from app.db.neo4j import (
    get_neo4j_session,
    get_bitcoin_transaction_details,
)


TEST_TXID = "cg_test_bitcoin_read_001"

INPUT_ADDRESS_1 = "bc1qtestinput111111111111111111111111111"
INPUT_ADDRESS_2 = "bc1qtestinput222222222222222222222222222"

OUTPUT_ADDRESS = "bc1qtestoutput11111111111111111111111111"


def cleanup():
    with get_neo4j_session() as session:
        session.run(
            """
            MATCH (bt:BitcoinTransaction {txid: $txid})
            DETACH DELETE bt
            """,
            txid=TEST_TXID,
        )

        session.run(
            """
            MATCH (w:Wallet {chain: "bitcoin"})
            WHERE w.address IN $addresses
            AND NOT (w)--()
            DELETE w
            """,
            addresses=[
                INPUT_ADDRESS_1,
                INPUT_ADDRESS_2,
                OUTPUT_ADDRESS,
            ],
        )


try:
    cleanup()

    with get_neo4j_session() as session:
        session.run(
            """
            MERGE (bt:BitcoinTransaction {txid: $txid})
            SET
                bt.block_height = $block_height,
                bt.block_time = $block_time,
                bt.confirmations = $confirmations,
                bt.fees = $fees
            """,
            txid=TEST_TXID,
            block_height=900000,
            block_time=1760000000,
            confirmations=10,
            fees=1500,
        )

        session.run(
            """
            MERGE (w:Wallet {
                address: $address,
                chain: "bitcoin"
            })

            MERGE (bt:BitcoinTransaction {txid: $txid})

            MERGE (w)-[r:BITCOIN_INPUT {
                txid: $txid,
                previous_txid: $previous_txid,
                previous_vout: $previous_vout
            }]->(bt)

            SET r.value = $value
            """,
            address=INPUT_ADDRESS_1,
            txid=TEST_TXID,
            previous_txid="previous_tx_001",
            previous_vout=0,
            value=500000,
        )

        session.run(
            """
            MERGE (w:Wallet {
                address: $address,
                chain: "bitcoin"
            })

            MERGE (bt:BitcoinTransaction {txid: $txid})

            MERGE (w)-[r:BITCOIN_INPUT {
                txid: $txid,
                previous_txid: $previous_txid,
                previous_vout: $previous_vout
            }]->(bt)

            SET r.value = $value
            """,
            address=INPUT_ADDRESS_2,
            txid=TEST_TXID,
            previous_txid="previous_tx_002",
            previous_vout=1,
            value=300000,
        )

        session.run(
            """
            MERGE (bt:BitcoinTransaction {txid: $txid})

            MERGE (w:Wallet {
                address: $address,
                chain: "bitcoin"
            })

            MERGE (bt)-[r:BITCOIN_OUTPUT {
                txid: $txid,
                vout: $vout
            }]->(w)

            SET r.value = $value
            """,
            address=OUTPUT_ADDRESS,
            txid=TEST_TXID,
            vout=0,
            value=798500,
        )

    result = get_bitcoin_transaction_details(TEST_TXID)

    print("\n=== BITCOIN NEO4J READ TEST ===")
    print(result)

    assert result is not None
    assert result["txid"] == TEST_TXID
    assert result["block_height"] == 900000
    assert result["block_time"] == 1760000000
    assert result["confirmations"] == 10
    assert result["fees"] == 1500

    assert len(result["inputs"]) == 2
    assert len(result["outputs"]) == 1

    input_addresses = {
        item["address"]
        for item in result["inputs"]
    }

    assert INPUT_ADDRESS_1 in input_addresses
    assert INPUT_ADDRESS_2 in input_addresses

    assert result["outputs"][0]["address"] == OUTPUT_ADDRESS
    assert result["outputs"][0]["vout"] == 0
    assert result["outputs"][0]["value"] == 798500

    print("\nPASS: Bitcoin transaction was correctly read from Neo4j.")

finally:
    cleanup()

    print("PASS: Synthetic Bitcoin test data cleaned up.")