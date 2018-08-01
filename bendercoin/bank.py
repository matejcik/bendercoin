from datetime import datetime

import attr
from flask import Flask
from flask import json, jsonify
from flask import request, abort

from .transaction import Transaction
from .util import TransactionJSONEncoder
from .util import _check, to_base64
from . import storage

app = Flask(__name__)
app.json_encoder = TransactionJSONEncoder
storage.load_transactions()

TX_BY_HASH = {}
SPENT = set()


def load_transactions():
    global TX_BY_HASH, SPENT
    storage.load_transactions()
    TX_BY_HASH = {}
    SPENT = set()
    for tx in storage.TRANSACTIONS:
        h = to_base64(tx.hash())
        addr = tx.from_address()
        TX_BY_HASH[h] = tx
        for inp in tx.inputs:
            out = (inp.hash, addr)
            SPENT.add(out)


load_transactions()


def get_history(account):
    hist = []
    for tx in storage.TRANSACTIONS:
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
    prev_hashes = {}
    for inp in tx.inputs:
        _check(
            inp.hash in TX_BY_HASH,
            "unknown previous hash",
        )
        spent = (inp.hash, addr)
        _check(
            spent not in SPENT,
            "this hash is already spent",
        )
        prev_hashes[inp.hash] = TX_BY_HASH[inp.hash]
    tx.validate_previous(prev_hashes)

    tx.datetime = datetime.now()
    storage.TRANSACTIONS.append(tx)
    storage.save_transactions()

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
