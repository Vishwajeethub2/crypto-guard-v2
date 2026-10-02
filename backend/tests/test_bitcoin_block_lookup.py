from app.services.bitcoin.provider import _rpc_call


BLOCK_HASH = "00000000000000000002029b18371fa6948caf61e4ec1788ce6384dfacfce87d"


block = _rpc_call(
    "getblock",
    [BLOCK_HASH, 1],
)

print("\n=== BITCOIN BLOCK LOOKUP TEST ===")
print("Block hash:", BLOCK_HASH)
print("Block height:", block.get("height"))
print("Block time:", block.get("time"))
print("Confirmations:", block.get("confirmations"))
print("Transaction count:", len(block.get("tx", [])))

assert isinstance(block, dict)
assert block.get("height") is not None
assert isinstance(block.get("height"), int)

print("\nPASS: Alchemy returned the Bitcoin block height.")