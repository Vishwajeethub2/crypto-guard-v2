from app.services.bitcoin.provider import _get_raw_transaction


TXID = "fa4d9b53c4851b8d6b69bab622ce484ed6897ac50b09c25cbc5bc86cd9bc35fe"


data = _get_raw_transaction(TXID)

print("\n=== RAW ALCHEMY BITCOIN TRANSACTION ===")

print("txid:", data.get("txid"))
print("blockhash:", data.get("blockhash"))
print("confirmations:", data.get("confirmations"))
print("blocktime:", data.get("blocktime"))
print("time:", data.get("time"))
print("blockheight:", data.get("blockheight"))

print("\n=== ALL TOP-LEVEL FIELDS ===")
for key, value in data.items():
    print(f"{key}: {value}")