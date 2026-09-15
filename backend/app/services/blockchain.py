from web3 import Web3

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