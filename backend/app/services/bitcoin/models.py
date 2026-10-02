from dataclasses import dataclass, field


@dataclass
class BitcoinInput:
    previous_txid: str
    previous_vout: int
    addresses: list[str] = field(default_factory=list)
    value: int = 0


@dataclass
class BitcoinOutput:
    vout: int
    addresses: list[str] = field(default_factory=list)
    value: int = 0
    spent_txid: str | None = None
    spent_index: int | None = None
    spent_height: int | None = None


@dataclass
class BitcoinTransaction:
    txid: str
    inputs: list[BitcoinInput] = field(default_factory=list)
    outputs: list[BitcoinOutput] = field(default_factory=list)
    block_height: int | None = None
    confirmations: int | None = None
    block_time: int | None = None
    fees: int = 0