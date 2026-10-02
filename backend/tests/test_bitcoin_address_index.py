from app.services.bitcoin.provider import (
    get_address_transaction_ids,
)


TEST_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

txids = get_address_transaction_ids(
    TEST_ADDRESS,
    page=1,
    limit=5,
)

print("\n=== BITCOIN ADDRESS INDEX TEST ===")
print("Address:", TEST_ADDRESS)
print("TXIDs:", txids)

assert isinstance(txids, list)
assert len(txids) > 0
assert len(txids) <= 5

for txid in txids:
    assert isinstance(txid, str)
    assert len(txid) == 64

print("\nPASS: Bitaps returned valid Bitcoin transaction IDs.")