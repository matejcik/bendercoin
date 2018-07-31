from hashlib import sha256
from flask import json
import attr
import ed25519
from .util import _check, from_dict
from .util import from_base64, to_base64
import base58


def address_from_pubkey(pub: ed25519.VerifyingKey):
    key_hash = sha256(pub.to_bytes()).digest()
    enc = base58.b58encode_check(key_hash[:8])
    return enc.decode("ascii")


@attr.s(frozen=True)
class TxInput:
    hash = attr.ib()
    index = attr.ib()
    amount = attr.ib()


@attr.s(frozen=True)
class TxOutput:
    address = attr.ib()
    amount = attr.ib()


@attr.s
class Transaction:
    inputs = attr.ib()
    outputs = attr.ib()
    message = attr.ib()

    from_address = attr.ib(default=None)
    to_addresses = attr.ib(default=None)
    datetime = attr.ib(default=None)

    pubkey = attr.ib(default=None)
    signature = attr.ib(default=None)

    def total_in(self):
        return sum(i.amount for i in self.inputs)

    def total_out(self):
        return sum(o.amount for o in self.inputs)

    def validate(self):
        # fmt: off
        _check(self.inputs, "no inputs")
        _check(self.outputs, "no outputs")

        for i in self.inputs:
            _check(i.hash, "missing hash")
            _check(isinstance(i.index, int), "bad index")
            _check(i.index >= 0, "index must not be negative")
            _check(isinstance(i.amount, int), "bad amount")
            _check(i.amount > 0, "amount must be positive")

        in_hashes = set(i.hash for i in self.inputs)
        _check(len(in_hashes) == len(self.inputs), "input txes must not repeat")

        for o in self.outputs:
            _check(o.address, "missing address")
            _check(isinstance(o.amount, int), "bad output amount")
            _check(o.amount > 0, "amount must be positive")

        out_addrs = set(o.address for o in self.outputs)
        _check(len(out_addrs) == len(self.outputs), "output addreses must not repeat")

        _check(self.total_in() == self.total_out(), "mismatched in/out")

        _check(len(self.message) <= 140, "message too long")
        _check(self.pubkey and self.signature, "transaction isn't signed")

        # verify signature
        self.pubkey.verify(self.signature, self.hash())
        # fmt: on

    def hash(self):
        hashables = dict(
            inputs=self.inputs,
            outputs=self.outputs,
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
        for n, i in enumerate(tx.inputs):
            tx.inputs[n] = TxInput(**i)
        for n, o in enumerate(tx.outputs):
            tx.outputs[n] = TxOutput(**o)
        return tx

    def to_dict(self):
        d = attr.asdict(self)
        if self.pubkey:
            b = self.pubkey.to_bytes()
            d["pubkey"] = to_base64(b)
        if self.signature:
            d["signature"] = to_base64(self.signature)
        ins = [attr.asdict(i) for i in self.inputs]
        outs = [attr.asdict(o) for o in self.outputs]
        d["inputs"] = ins
        d["outputs"] = outs
        return d
