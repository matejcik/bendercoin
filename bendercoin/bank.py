from datetime import datetime

import ed25519
import attr
from flask import Flask
from flask import json, jsonify
from flask import request, abort

from .transaction import Transaction
from .util import TransactionJSONEncoder
from .util import _check, to_base64
from . import storage
from .block import Block

app = Flask(__name__)
app.json_encoder = TransactionJSONEncoder
storage.load_transactions()

BENDER_KEY = ed25519.SigningKey(
    b"6db72cfc2b48ab152b5b25a0e8396403b4b10f803fb09c61cac10a7955bbb28f",
    encoding="hex",
)

TX_BY_HASH = {}
CURRENT_BLOCK = Block(transactions=[])
SPENT = set()


def load_transactions():
    global TX_BY_HASH, SPENT
    storage.load_transactions()
    TX_BY_HASH = {}
    SPENT = set()
    blocks = list(storage.BLOCKS.values())
    all_txs = []
    for bl in blocks:
        all_txs.append(bl.coinbase)
        all_txs.extend(bl.transactions)
    all_txs.extend(CURRENT_BLOCK.transactions)
    for tx in all_txs:
        h = to_base64(tx.hash())
        addr = tx.from_address()
        TX_BY_HASH[h] = tx
        for inp in tx.inputs:
            out = (inp.hash, addr)
            SPENT.add(out)


load_transactions()


def get_history(account):
    hist = []
    for tx in TX_BY_HASH.values():
        if (
            tx.from_address() == account
            or account in tx.to_addresses()
        ):
            hist.append(tx)
    return hist


def get_balance(account):
    hist = get_history(account)
    total = 0
    for tx in hist:
        if tx.from_address() == account:
            total -= tx.sent()
        else:
            total += tx.received(account)
    return total


def transact(tx: Transaction):
    tx.validate()
    addr = tx.from_address()

    if tx.coinbase is not None:
        spent = (tx.coinbase, addr)
        _check(
            spent not in SPENT,
            "this coinbase is already spent",
        )
        tx.validate_coinbase(
            storage.BLOCKS[tx.coinbase]
        )

    else:
        tx.validate_previous(TX_BY_HASH)
        for inp in tx.inputs:
            spent = (inp.hash, addr)
            _check(
                spent not in SPENT,
                "this hash is already spent",
            )

    tx.datetime = datetime.now()
    CURRENT_BLOCK.transactions.append(tx)

    TX_BY_HASH[to_base64(tx.hash())] = tx
    for inp in tx.inputs:
        spent = (inp.hash, addr)
        SPENT.add(spent)


@app.route("/")
def hello():
    return "Welcome to BenderBank!!"


@app.route("/history/<account>")
def history(account):
    return jsonify(get_history(account))


@app.route("/balance/<account>")
def balance(account):
    return jsonify(get_balance(account))


@app.route("/send_tx", methods=["POST"])
def send_tx():
    data = request.get_json(force=True)
    tx = Transaction.from_dict(data)

    try:
        transact(tx)
        return jsonify(status="ok")
    except Exception as e:
        return jsonify(status="err", error=str(e))


@app.route("/reload")
def reload():
    load_transactions()
    return jsonify(status="ok")


@app.route("/tx/<hash>")
def get_tx(hash):
    try:
        return jsonify(TX_BY_HASH[hash])
    except Exception as e:
        return jsonify(status="err", error=str(e))


@app.route("/make_block")
def make_block():
    global CURRENT_BLOCK
    if storage.BLOCKS:
        all_blocks = list(storage.BLOCKS.values())
        prev_block = all_blocks[-1]
        prev_hdr = prev_block.header
    else:
        prev_hdr = None

    CURRENT_BLOCK.mine(BENDER_KEY, prev_hdr)
    hdr = CURRENT_BLOCK.header
    storage.BLOCKS[hdr.num] = CURRENT_BLOCK
    CURRENT_BLOCK = Block(transactions=[])
    storage.save_transactions()
    load_transactions()
    return jsonify(status="ok")
