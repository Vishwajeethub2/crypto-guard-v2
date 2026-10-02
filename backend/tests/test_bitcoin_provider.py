from app.services.bitcoin.provider import (
    _parse_alchemy_transaction,
)


def test_parse_alchemy_transaction():
    previous_txid = (
        "0eb7b574373de2c88d0dc1444f49947c681d0437d21361f9ebb4dd09c62f2a66"
    )

    transaction_data = {
        "txid": (
            "8c1e3dec662d1f2a5e322ccef5eca263f98eb16723c6f990be0c88c1db113fb1"
        ),
        "vin": [
            {
                "txid": previous_txid,
                "vout": 1,
                "is_coinbase": False,
            }
        ],
        "vout": [
            {
                "n": 0,
                "value": 0.00175000,
                "scriptPubKey": {
                    "address": (
                        "1Nb1ykSD7J5k4RFjJQGsrD9gxBE6jzfNa"
                    )
                },
            },
            {
                "n": 1,
                "value": 0.09888100,
                "scriptPubKey": {
                    "address": (
                        "bc1qjmc49gy3jjrkyjl57yl5duxjp7ssmxkvh5t2q5"
                    )
                },
            },
        ],
        "confirmations": 108719,
        "blocktime": 1725956288,
    }

    previous_transaction_data = {
        "txid": previous_txid,
        "vout": [
            {
                "n": 0,
                "value": 0.00100000,
                "scriptPubKey": {
                    "address": (
                        "bc1qpreviousoutputaddress000000000000000"
                    )
                },
            },
            {
                "n": 1,
                "value": 0.10106300,
                "scriptPubKey": {
                    "address": (
                        "bc1qmgwnfjlda4ns3g6g3yz74w6scnn9yu2ts82yyc"
                    )
                },
            },
        ],
    }

    cache = {
        previous_txid: previous_transaction_data,
    }

    transaction = _parse_alchemy_transaction(
        transaction_data,
        cache=cache,
    )

    assert transaction.txid == (
        "8c1e3dec662d1f2a5e322ccef5eca263f98eb16723c6f990be0c88c1db113fb1"
    )

    assert len(transaction.inputs) == 1

    assert transaction.inputs[0].previous_txid == previous_txid
    assert transaction.inputs[0].previous_vout == 1

    assert transaction.inputs[0].addresses == [
        "bc1qmgwnfjlda4ns3g6g3yz74w6scnn9yu2ts82yyc"
    ]

    assert transaction.inputs[0].value == 10_106_300

    assert len(transaction.outputs) == 2

    assert transaction.outputs[0].vout == 0
    assert transaction.outputs[0].addresses == [
        "1Nb1ykSD7J5k4RFjJQGsrD9gxBE6jzfNa"
    ]
    assert transaction.outputs[0].value == 175_000

    assert transaction.outputs[1].vout == 1
    assert transaction.outputs[1].addresses == [
        "bc1qjmc49gy3jjrkyjl57yl5duxjp7ssmxkvh5t2q5"
    ]
    assert transaction.outputs[1].value == 9_888_100

    assert transaction.fees == 43_200

    assert transaction.block_height is None

    assert transaction.block_time == 1_725_956_288

    assert transaction.confirmations == 108_719