from hashlib import sha256
import attr
from .util import (
    _check,
    from_base64,
    to_base64,
    from_dict,
)
import ed25519
import os
import json
from .transaction import (
    Transaction,
    TxOutput,
    address_from_pubkey,
)


DIFFICULTY = 2
BLOCK_REWARD = 1000


@attr.s
class BlockHeader:
    num = attr.ib()
    pubkey = attr.ib()
    reward = attr.ib()
    tx_hashes = attr.ib()
    coinbase_hash = attr.ib()
    prev_hash = attr.ib()

    nonce = attr.ib(default=b"")
    signature = attr.ib(default=None)

    mined = attr.ib(default=False)

    def hash(self):
        base = dict(
            num=self.num,
            pubkey=to_base64(self.pubkey.to_bytes()),
            coinbase_hash=self.coinbase_hash,
            reward=self.reward,
            tx_hashes=self.tx_hashes,
            prev_hash=self.prev_hash,
        )
        data = json.dumps(base, sort_keys=True)
        encoded = data.encode("utf-8")
        hashable = encoded + self.nonce
        return sha256(hashable).digest()

    def mine(self, difficulty=DIFFICULTY):
        if self.mined:
            raise Exception("already mined")

        while True:
            self.nonce = os.urandom(64)
            h = self.hash()
            if all(
                h[i] == 0 for i in range(difficulty)
            ):
                self.mined = True
                break

    def sign(self, privkey):
        if not self.mined:
            raise Exception("don't sign unmined")
        self.signature = privkey.sign(self.hash())

    def to_dict(self):
        d = attr.asdict(self)
        d["pubkey"] = to_base64(self.pubkey.to_bytes())
        if self.signature:
            d["signature"] = to_base64(self.signature)
        d["nonce"] = to_base64(self.nonce)
        return d

    @classmethod
    def from_dict(cls, d):
        hdr = from_dict(cls, d)
        decoded = from_base64(hdr.pubkey)
        hdr.pubkey = ed25519.VerifyingKey(decoded)
        hdr.signature = from_base64(hdr.signature)
        hdr.nonce = from_base64(hdr.nonce)
        return hdr


@attr.s
class Block:
    transactions = attr.ib()
    header = attr.ib(default=None)
    coinbase = attr.ib(default=None)

    def make_header(self, privkey, prev_hdr):
        if not prev_hdr:
            prev_hash = ""
            num = 0
        else:
            prev_hash = to_base64(prev_hdr.hash())
            num = prev_hdr.num + 1

        reward = BLOCK_REWARD
        c = self.make_coinbase(privkey, num, reward)
        self.header = BlockHeader(
            num=num,
            prev_hash=prev_hash,
            pubkey=privkey.get_verifying_key(),
            reward=reward,
            tx_hashes=self.get_tx_hashes(),
            coinbase_hash=to_base64(c.hash()),
        )
        return self.header

    def make_coinbase(self, privkey, num, reward):
        pubkey = privkey.get_verifying_key()
        addr = address_from_pubkey(pubkey)
        out = TxOutput(address=addr, amount=reward)
        tx = Transaction(
            inputs=[],
            outputs=[out],
            message=f"coinbase {num}",
            coinbase=num,
        )
        tx.sign(privkey)
        self.coinbase = tx
        return tx

    def get_tx_hashes(self):
        result = self.coinbase.hash()
        for tx in self.transactions:
            result += tx.hash()
        all_hashes = sha256(result).digest()
        return to_base64(all_hashes)

    def mine(
        self, privkey, prev_hdr, difficulty=DIFFICULTY
    ):
        header = self.make_header(privkey, prev_hdr)
        header.mine(difficulty)
        header.sign(privkey)

    def to_dict(self):
        txes = [self.coinbase] + self.transactions
        d = {}
        d["transactions"] = [
            tx.to_dict() for tx in txes
        ]
        d["header"] = self.header.to_dict()
        return d

    @classmethod
    def from_dict(cls, d):
        transactions = [
            Transaction.from_dict(tx)
            for tx in d["transactions"]
        ]
        header = BlockHeader.from_dict(d["header"])
        return cls(
            coinbase=transactions[0],
            transactions=transactions[1:],
            header=header,
        )
