from hashlib import sha256
from flask import json
import attr
import ed25519
from .util import _check, from_dict
from .util import from_base64, to_base64


@attr.s
class Transaction:
    from_account = attr.ib()
    to_account = attr.ib()
    amount = attr.ib()
    message = attr.ib()

    datetime = attr.ib(default=None)

    pubkey = attr.ib(default=None)
    signature = attr.ib(default=None)

    def validate(self):
        # fmt: off
        _check(self.from_account, "missing from_account")
        _check(self.to_account, "missing to_account")
        _check(self.to_account != self.from_account, "don't send money to yourself")
        _check(isinstance(self.amount, int), "non-numeric amount")
        _check(self.amount > 0, "amount must be positive")
        _check(len(self.message) <= 140, "message too long")
        _check(self.pubkey and self.signature, "transaction isn't signed")

        # verify signature
        self.pubkey.verify(self.signature, self.hash())
        # fmt: on

    def hash(self):
        hashables = dict(
            from_account=self.from_account,
            to_account=self.to_account,
            amount=self.amount,
            message=self.message,
        )
        data = json.dumps(hashables, sort_keys=True)
        return sha256(data.encode("utf-8")).digest()

    def sign(self, priv: ed25519.SigningKey):
        self.pubkey = priv.get_verifying_key()
        self.signature = priv.sign(self.hash())

    # ====== encoding/decoding utilities =======

    @classmethod
    def from_dict(cls, d):
        tx = from_dict(cls, d)
        if tx.pubkey:
            decoded = from_base64(tx.pubkey)
            tx.pubkey = ed25519.VerifyingKey(decoded)
        if tx.signature:
            tx.signature = from_base64(tx.signature)
        return tx

    def to_dict(self):
        d = attr.asdict(self)
        if self.pubkey:
            b = self.pubkey.to_bytes()
            d["pubkey"] = to_base64(b)
        if self.signature:
            d["signature"] = to_base64(self.signature)
        return d
