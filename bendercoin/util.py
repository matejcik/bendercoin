from flask import json
import attr
import requests


def from_dict(cls, data):
    fields = attr.fields(cls)
    init_args = {}
    for field in fields:
        init_args[field.name] = data.get(field.name)
    return cls(**init_args)


def _check(what: bool, error: str):
    if not what:
        raise ValueError(error)


def print_json(j):
    try:
        if isinstance(j, requests.Response):
            j = j.json()
        s = json.dumps(j, sort_keys=True, indent=4)
        print(s)
    except Exception as e:
        print("could not decode json:", e)
        print(j)

class TransactionJSONEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=E0202
        from .transaction import Transaction
        if isinstance(obj, Transaction):
            return attr.asdict(obj)
        return super().default(obj)
