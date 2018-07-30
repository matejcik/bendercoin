from flask import json
import attr
from .util import _check

@attr.s
class Transaction:
    from_account = attr.ib()
    to_account = attr.ib()
    amount = attr.ib()
    datetime = attr.ib()
    message = attr.ib()

    def validate(self):
        # fmt: off
        _check(self.from_account, "missing from_account")
        _check(self.to_account, "missing to_account")
        _check(self.to_account != self.from_account, "don't send money to yourself")
        _check(isinstance(self.amount, int), "non-numeric amount")
        _check(self.amount > 0, "amount must be positive")
        _check(len(self.message) <= 140, "message too long")
        # fmt: on


