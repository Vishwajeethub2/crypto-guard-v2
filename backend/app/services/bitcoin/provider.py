import httpx



from app.core.config import settings

from app.services.bitcoin.models import (

    BitcoinInput,

    BitcoinOutput,

    BitcoinTransaction,

)





BITCOIN_RPC_URL = (

    "https://bitcoin-mainnet.g.alchemy.com/v2/"

    f"{settings.alchemy_api_key}"

)



BITAPS_API_URL = (

    "https://api.bitaps.com/btc/v1/blockchain"

)





def _rpc_call(

    method: str,

    params: list | None = None,

):

    payload = {

        "jsonrpc": "2.0",

        "id": 1,

        "method": method,

        "params": params or [],

    }



    with httpx.Client(timeout=30.0) as client:

        response = client.post(

            BITCOIN_RPC_URL,

            json=payload,

        )

        response.raise_for_status()



    data = response.json()



    if data.get("error"):

        raise ValueError(data["error"])



    if "result" not in data:

        raise ValueError(

            "Bitcoin RPC response is missing result"

        )



    return data["result"]

def _rpc_batch_call(
    calls: list[tuple[str, list | None]],
):
    """Execute multiple Bitcoin JSON-RPC calls in one HTTP request."""
    if not calls:
        return []

    payload = [
        {
            "jsonrpc": "2.0",
            "id": index,
            "method": method,
            "params": params or [],
        }
        for index, (method, params) in enumerate(calls, start=1)
    ]

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            BITCOIN_RPC_URL,
            json=payload,
        )
        response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Bitcoin RPC batch response must be an array")

    results_by_id = {}

    for item in data:
        if not isinstance(item, dict):
            raise ValueError(
                "Bitcoin RPC batch response item must be an object"
            )

        response_id = item.get("id")
        if (
            not isinstance(response_id, int)
            or response_id not in range(1, len(calls) + 1)
        ):
            raise ValueError(
                "Bitcoin RPC batch response contains an unknown request ID"
            )

        if item.get("error"):
            method = calls[response_id - 1][0]
            raise ValueError({"method": method, "error": item["error"]})

        if "result" not in item:
            method = calls[response_id - 1][0]
            raise ValueError(
                f"Bitcoin RPC batch response is missing result for {method}"
            )

        results_by_id[response_id] = item["result"]

    if len(results_by_id) != len(calls):
        raise ValueError(
            "Bitcoin RPC batch response is missing one or more results"
        )

    return [
        results_by_id[index]
        for index in range(1, len(calls) + 1)
    ]



def get_address_transaction_ids(

    address: str,

    page: int = 1,

    limit: int = 50,

) -> list[str]:

    """

    Retrieve Bitcoin transaction IDs associated with an address

    using the Bitaps address-indexing API.



    Bitaps is used only for address-to-transaction discovery.

    Full transaction retrieval remains handled by Alchemy

    Bitcoin JSON-RPC.

    """

    if not address:

        raise ValueError(

            "Bitcoin address is required"

        )



    if page < 1:

        raise ValueError(

            "Bitcoin address transaction page must be >= 1"

        )



    if limit < 1:

        raise ValueError(

            "Bitcoin address transaction limit must be >= 1"

        )



    url = (

        f"{BITAPS_API_URL}/address/transactions/"

        f"{address}"

    )



    with httpx.Client(timeout=30.0) as client:

        response = client.get(

            url,

            params={

                "page": page,

                "limit": limit,

                "order": "desc",

                "mode": "brief",

            },

        )

        response.raise_for_status()



    data = response.json()



    if not isinstance(data, dict):

        raise ValueError(

            "Bitaps address transaction response must be an object"

        )



    response_data = data.get("data")



    if not isinstance(response_data, dict):

        raise ValueError(

            "Bitaps address transaction response is missing data"

        )



    transactions = response_data.get("list")



    if transactions is None:

        return []



    if not isinstance(transactions, list):

        raise ValueError(

            "Bitaps address transaction list must be an array"

        )



    transaction_ids: list[str] = []



    for transaction in transactions:

        if not isinstance(transaction, dict):

            continue



        txid = transaction.get("txId")



        if txid:

            transaction_ids.append(str(txid))



    return transaction_ids





def _get_raw_transaction(

    txid: str,

    cache: dict[str, dict] | None = None,

):

    if not txid:

        raise ValueError(

            "Bitcoin transaction ID is required"

        )



    if cache is not None and txid in cache:

        return cache[txid]



    data = _rpc_call(

        "getrawtransaction",

        [txid, True],

    )



    if not isinstance(data, dict):

        raise ValueError(

            "Bitcoin RPC transaction result must be an object"

        )



    if cache is not None:

        cache[txid] = data



    return data

def _get_raw_transactions(
    txids: list[str],
    cache: dict[str, dict] | None = None,
):
    """
    Retrieve multiple Bitcoin transactions using JSON-RPC batching.

    Existing cached transactions are reused. Missing transactions are
    fetched in batches to avoid one HTTP request per Bitcoin input.
    """
    if not txids:
        return {}

    unique_txids = list(dict.fromkeys(txids))
    missing_txids = [
        txid
        for txid in unique_txids
        if cache is None or txid not in cache
    ]

    if missing_txids:
        batch_size = 50

        for start in range(0, len(missing_txids), batch_size):
            batch_txids = missing_txids[start:start + batch_size]
            results = _rpc_batch_call(
                [
                    ("getrawtransaction", [txid, True])
                    for txid in batch_txids
                ]
            )

            for txid, data in zip(batch_txids, results):
                if not isinstance(data, dict):
                    raise ValueError(
                        "Bitcoin RPC transaction result must be an object"
                    )

                if cache is not None:
                    cache[txid] = data

    if cache is not None:
        return {txid: cache[txid] for txid in unique_txids}

    return {}



def _get_block(

    blockhash: str,

    cache: dict[str, dict] | None = None,

):

    """

    Retrieve a Bitcoin block by hash using Alchemy Bitcoin

    JSON-RPC.



    This is used when getrawtransaction does not provide

    blockheight directly.

    """

    if not blockhash:

        raise ValueError(

            "Bitcoin block hash is required"

        )



    if cache is not None and blockhash in cache:

        return cache[blockhash]



    data = _rpc_call(

        "getblock",

        [blockhash, 1],

    )



    if not isinstance(data, dict):

        raise ValueError(

            "Bitcoin RPC block result must be an object"

        )



    if cache is not None:

        cache[blockhash] = data



    return data





def get_transaction(

    txid: str,

) -> BitcoinTransaction:

    """

    Retrieve and normalize a Bitcoin transaction using

    Alchemy Bitcoin JSON-RPC.



    Bitcoin inputs reference previous transaction outputs,

    so each input's previous transaction is resolved to obtain

    its address and value.



    When the transaction response does not provide block height

    directly, its block hash is resolved through getblock.

    """

    transaction_cache: dict[str, dict] = {}

    block_cache: dict[str, dict] = {}



    data = _get_raw_transaction(

        txid,

        cache=transaction_cache,

    )

    previous_txids = []

    for item in data.get("vin", []):
        if item.get("is_coinbase"):
            continue

        previous_txid = item.get("txid")
        if previous_txid:
            previous_txids.append(previous_txid)

    # Prefetch all previous transactions in batches. The parser then
    # reads them from transaction_cache instead of making one RPC
    # request per input.
    _get_raw_transactions(
        previous_txids,
        cache=transaction_cache,
    )



    return _parse_alchemy_transaction(

        data,

        cache=transaction_cache,

        block_cache=block_cache,

    )





def _btc_to_satoshis(

    value: int | float,

) -> int:

    """

    Convert BTC to satoshis.



    Bitcoin transaction values returned by the RPC are

    represented in BTC, while Crypto Guard stores normalized

    Bitcoin values as integer satoshis.

    """

    return int(

        round(float(value) * 100_000_000)

    )





def _extract_output_address(

    output: dict,

) -> str | None:

    """

    Extract a Bitcoin address from a transaction output.



    Supports the address fields returned by the Bitcoin RPC

    transaction representation.

    """

    script_pub_key = output.get(

        "scriptPubKey"

    ) or {}



    address = script_pub_key.get(

        "address"

    )



    if address:

        return address



    addresses = (

        script_pub_key.get("addresses")

        or []

    )



    if addresses:

        return addresses[0]



    return None





def _parse_alchemy_transaction(

    data: dict,

    cache: dict[str, dict] | None = None,

    block_cache: dict[str, dict] | None = None,

) -> BitcoinTransaction:

    """

    Convert an Alchemy Bitcoin JSON-RPC transaction into

    Crypto Guard's normalized BitcoinTransaction model.



    Bitcoin inputs contain references to previous transaction

    outputs. Those previous transactions are fetched so that

    the input address and value can be preserved.



    If block height is not included directly in the transaction

    response, the transaction's block hash is resolved through

    getblock.

    """

    if not isinstance(data, dict):

        raise ValueError(

            "Bitcoin RPC transaction data must be an object"

        )



    txid = data.get("txid")



    if not txid:

        raise ValueError(

            "Bitcoin transaction is missing txid"

        )



    inputs: list[BitcoinInput] = []



    for item in data.get("vin", []):

        if item.get("is_coinbase"):

            continue



        previous_txid = item.get("txid")

        previous_vout = item.get("vout")



        if not previous_txid:

            raise ValueError(

                "Bitcoin input is missing previous transaction ID"

            )



        if previous_vout is None:

            raise ValueError(

                "Bitcoin input is missing previous output index"

            )



        previous_transaction = _get_raw_transaction(

            previous_txid,

            cache=cache,

        )



        previous_outputs = (

            previous_transaction.get("vout")

            or []

        )



        matching_output = next(

            (

                output

                for output in previous_outputs

                if int(

                    output.get("n", -1)

                ) == int(previous_vout)

            ),

            None,

        )



        if matching_output is None:

            raise ValueError(

                "Referenced Bitcoin previous output was not found: "

                f"{previous_txid}:{previous_vout}"

            )



        address = _extract_output_address(

            matching_output

        )



        addresses = (

            [address]

            if address

            else []

        )



        inputs.append(

            BitcoinInput(

                previous_txid=previous_txid,

                previous_vout=int(

                    previous_vout

                ),

                addresses=addresses,

                value=_btc_to_satoshis(

                    matching_output.get(

                        "value",

                        0,

                    )

                ),

            )

        )



    outputs: list[BitcoinOutput] = []



    for item in data.get("vout", []):

        vout_index = int(

            item.get(

                "n",

                len(outputs),

            )

        )



        address = _extract_output_address(

            item

        )



        addresses = (

            [address]

            if address

            else []

        )



        outputs.append(

            BitcoinOutput(

                vout=vout_index,

                addresses=addresses,

                value=_btc_to_satoshis(

                    item.get(

                        "value",

                        0,

                    )

                ),

            )

        )



    total_input_value = sum(

        item.value

        for item in inputs

    )



    total_output_value = sum(

        item.value

        for item in outputs

    )



    fees = max(

        total_input_value

        - total_output_value,

        0,

    )



    block_height = data.get(

        "blockheight"

    )



    if block_height is None:

        block_height = data.get(

            "blockHeight"

        )



    blockhash = data.get(

        "blockhash"

    )



    if (

        block_height is None

        and blockhash

    ):

        block = _get_block(

            blockhash,

            cache=block_cache,

        )



        block_height = block.get(

            "height"

        )



    block_time = data.get(

        "blocktime"

    )



    if block_time is None:

        block_time = data.get(

            "blockTime"

        )



    confirmations = data.get(

        "confirmations"

    )



    return BitcoinTransaction(

        txid=txid,

        inputs=inputs,

        outputs=outputs,

        block_height=(

            int(block_height)

            if block_height is not None

            else None

        ),

        confirmations=(

            int(confirmations)

            if confirmations is not None

            else None

        ),

        block_time=(

            int(block_time)

            if block_time is not None

            else None

        ),

        fees=fees,

    )