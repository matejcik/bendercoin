from flask import json
from .transaction import Transaction
from .block import Block

BLOCKS = {}


def load_transactions():
    global BLOCKS
    BLOCKS = {}
    with open("transactions.json") as f:
        data = json.load(f)
    for key, val in data.items():
        bl = Block.from_dict(val)
        num = bl.header.num
        BLOCKS[num] = bl

    return BLOCKS


def save_transactions():
    global BLOCKS
    with open("transactions.json", "w") as f:
        json.dump(BLOCKS, f, indent=4)
