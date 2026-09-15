from pydantic import BaseModel


class WalletCreate(BaseModel):
    address: str
    chain: str
    label: str | None = None