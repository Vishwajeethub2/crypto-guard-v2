from app.services.bitcoin.provider import (
    get_address_transaction_ids,
    get_transaction,
)

TEST_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"


txids = get_address_transaction_ids(
    TEST_ADDRESS,
    page=1,
    limit=1,
)

print("\n=== BITCOIN PROVIDER PIPELINE TEST ===")
print("Address:", TEST_ADDRESS)
print("TXIDs:", txids)

assert isinstance(txids, list)
assert len(txids) == 1

txid = txids[0]

print("\nSelected TXID:", txid)

transaction = get_transaction(txid)
print("\n=== PARSED TRANSACTION OBJECT ===")
print(transaction)

print("\n=== ALCHEMY TRANSACTION RESULT ===")
print("TXID:", transaction.txid)
print("Inputs:", len(transaction.inputs))
print("Outputs:", len(transaction.outputs))
print("Block height:", transaction.block_height)
print("Confirmations:", transaction.confirmations)
print("Block time:", transaction.block_time)
print("Fees:", transaction.fees)

assert transaction.txid == txid
assert isinstance(transaction.inputs, list)
assert isinstance(transaction.outputs, list)
assert len(transaction.inputs) > 0
assert len(transaction.outputs) > 0

print("\nPASS: Bitaps address discovery → Alchemy transaction retrieval works.")