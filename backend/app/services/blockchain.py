import json
from pathlib import Path

from web3 import Web3
import httpx

from app.core.config import settings


CHAIN_RPC_URLS = {
    "ethereum": f"https://eth-mainnet.g.alchemy.com/v2/{settings.alchemy_api_key}",
    "polygon": f"https://polygon-mainnet.g.alchemy.com/v2/{settings.alchemy_api_key}",
    "arbitrum": f"https://arb-mainnet.g.alchemy.com/v2/{settings.alchemy_api_key}",
    "optimism": f"https://opt-mainnet.g.alchemy.com/v2/{settings.alchemy_api_key}",
    "base": f"https://base-mainnet.g.alchemy.com/v2/{settings.alchemy_api_key}",
}


def get_web3(chain: str) -> Web3:
    chain = chain.lower()

    if chain not in CHAIN_RPC_URLS:
        raise ValueError(f"Unsupported chain: {chain}")

    return Web3(Web3.HTTPProvider(CHAIN_RPC_URLS[chain]))


def validate_wallet_address(address: str) -> bool:
    return Web3.is_address(address)


def get_native_balance(chain: str, address: str):
    w3 = get_web3(chain)

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    checksum_address = w3.to_checksum_address(address)
    balance_wei = w3.eth.get_balance(checksum_address)

    return w3.from_wei(balance_wei, "ether")


def get_wallet_snapshot(chain: str, address: str):
    w3 = get_web3(chain)

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    checksum_address = w3.to_checksum_address(address)

    balance_wei = w3.eth.get_balance(checksum_address)
    latest_block = w3.eth.block_number
    transaction_count = w3.eth.get_transaction_count(checksum_address)
    latest_block_data = w3.eth.get_block(latest_block)

    return {
        "chain": chain.lower(),
        "address": checksum_address,
        "native_balance": str(w3.from_wei(balance_wei, "ether")),
        "latest_block": latest_block,
        "transaction_count": transaction_count,
        "latest_block_timestamp": latest_block_data["timestamp"],
        "latest_block_hash": latest_block_data["hash"].hex(),
    }


def build_transaction_snapshot(transactions: list[dict]):
    return {
        "transaction_count": len(transactions),
        "transactions": transactions,
    }


def get_recent_transactions(
    chain: str,
    address: str,
    block_count: int = 10,
):
    w3 = get_web3(chain)

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    checksum_address = w3.to_checksum_address(address)

    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - block_count)

    transactions = []

    for block_number in range(start_block, latest_block + 1):
        block = w3.eth.get_block(
            block_number,
            full_transactions=True,
        )

        for tx in block["transactions"]:
            if (
                tx["from"].lower() == checksum_address.lower()
                or (
                    tx["to"]
                    and tx["to"].lower() == checksum_address.lower()
                )
            ):
                transactions.append(
                    {
                        "hash": tx["hash"].hex(),
                        "from": tx["from"],
                        "to": tx["to"],
                        "value": str(
                            w3.from_wei(
                                tx["value"],
                                "ether",
                            )
                        ),
                        "block_number": block_number,
                    }
                )

    return build_transaction_snapshot(transactions)


def get_saved_wallet_snapshot():
    file_path = (
        Path(__file__).resolve().parents[2]
        / "sample_data"
        / "ethereum_wallet_snapshot.json"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_address_transfers(
    chain: str,
    address: str,
    max_count: int = 20,
):
    chain = chain.lower()

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    alchemy_chain_names = {
        "ethereum": "eth-mainnet",
        "polygon": "polygon-mainnet",
        "arbitrum": "arb-mainnet",
        "optimism": "opt-mainnet",
        "base": "base-mainnet",
    }

    if chain not in alchemy_chain_names:
        raise ValueError(f"Unsupported chain: {chain}")

    url = (
        f"https://{alchemy_chain_names[chain]}.g.alchemy.com/v2/"
        f"{settings.alchemy_api_key}"
    )

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromBlock": "0x0",
                "toBlock": "latest",
                "fromAddress": address,
                "category": [
                    "external",
                    "internal",
                    "erc20",
                    "erc721",
                    "erc1155",
                ],
                "withMetadata": True,
                "excludeZeroValue": True,
                "maxCount": hex(max_count),
            }
        ],
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise ValueError(data["error"]["message"])

    transfers = data.get("result", {}).get("transfers", [])

    return {
        "chain": chain,
        "address": address,
        "transfer_count": len(transfers),
        "transfers": transfers,
    }

def get_address_transfers_live(
    chain: str,
    address: str,
    direction: str = "both",
    max_count: int = 20,
):
    """
    Fetch real blockchain transfer data from Alchemy for live tracing.

    Supports:
    - outgoing transfers
    - incoming transfers
    - both directions
    """

    chain = chain.lower()
    direction = direction.lower()

    if not validate_wallet_address(address):
        raise ValueError("Invalid wallet address")

    if direction not in {"incoming", "outgoing", "both"}:
        raise ValueError(
            "direction must be incoming, outgoing, or both"
        )

    if max_count < 1 or max_count > 1000:
        raise ValueError(
            "max_count must be between 1 and 1000"
        )

    alchemy_chain_names = {
        "ethereum": "eth-mainnet",
        "polygon": "polygon-mainnet",
        "arbitrum": "arb-mainnet",
        "optimism": "opt-mainnet",
        "base": "base-mainnet",
    }

    if chain not in alchemy_chain_names:
        raise ValueError(
            f"Unsupported chain: {chain}"
        )

    url = (
        f"https://{alchemy_chain_names[chain]}"
        f".g.alchemy.com/v2/"
        f"{settings.alchemy_api_key}"
    )

    categories = [
        "external",
        "internal",
        "erc20",
        "erc721",
        "erc1155",
    ]

    def fetch_transfers(
        address_field: str,
    ) -> list[dict]:

        params = {
            "fromBlock": "0x0",
            "toBlock": "latest",
            address_field: address,
            "category": categories,
            "withMetadata": True,
            "excludeZeroValue": True,
            "maxCount": hex(max_count),
        }

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [params],
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise ValueError(
                data["error"]["message"]
            )

        return data.get(
            "result",
            {},
        ).get(
            "transfers",
            [],
        )

    transfers = []

    if direction in {"outgoing", "both"}:
        transfers.extend(
            fetch_transfers("fromAddress")
        )

    if direction in {"incoming", "both"}:
        transfers.extend(
            fetch_transfers("toAddress")
        )

    return {
        "chain": chain,
        "address": address,
        "direction": direction,
        "transfer_count": len(transfers),
        "transfers": transfers,
    }

def parse_transfer_data(transfers: list[dict]):
    parsed_transfers = []

    for transfer in transfers:
        parsed_transfers.append(
            {
                "hash": transfer.get("hash"),
                "from": transfer.get("from"),
                "to": transfer.get("to"),
                "asset": transfer.get("asset"),
                "value": transfer.get("value"),
                "category": transfer.get("category"),
                "block_number": int(transfer["blockNum"], 16)
                if transfer.get("blockNum")
                else None,
                "timestamp": transfer.get("metadata", {}).get("blockTimestamp"),
                "contract_address": transfer.get("rawContract", {}).get("address"),
            }
        )

    return parsed_transfers

def get_saved_parsed_transfers():
    file_path = (
        Path(__file__).resolve().parents[2]
        / "sample_data"
        / "ethereum_transfers.json"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return parse_transfer_data(data["transfers"])

def build_graph_transactions(transfers: list[dict]):
    graph_transactions = []

    for transfer in transfers:
        graph_transactions.append(
            {
                "chain": transfer.get(
                    "chain",
                    "ethereum",
                ).lower(),
                "from_address": transfer["from"],
                "to_address": transfer["to"],
                "transaction_hash": transfer["hash"],
                "asset": transfer["asset"],
                "value": transfer["value"],
                "category": transfer["category"],
                "block_number": transfer["block_number"],
                "timestamp": transfer["timestamp"],
                "contract_address": transfer["contract_address"],
            }
        )

    return graph_transactions