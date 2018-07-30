from datetime import datetime

import attr
from flask import Flask
from flask import json, jsonify
from flask import request, abort

from .transaction import Transaction
from .util import TransactionJSONEncoder
from .util import from_dict, _check
from . import storage

app = Flask(__name__)
app.json_encoder = TransactionJSONEncoder
storage.load_transactions()


def get_history(account):
    hist = []
    for tx in storage.TRANSACTIONS:
        if (
            tx.from_account == account
            or tx.to_account == account
        ):
            hist.append(tx)
    return hist


def get_balance(account):
    hist = get_history(account)
    total = 0
    for tx in hist:
        if tx.to_account == account:
            total += tx.amount
        elif tx.from_account == account:
            total -= tx.amount
        else:
            raise RuntimeError("( ≖_≖)")
    return total


def transact(tx: Transaction):
    tx.validate()
    balance = get_balance(tx.from_account)
    _check(tx.amount <= balance, "not enough money")

    tx.datetime = datetime.now()
    storage.TRANSACTIONS.append(tx)
    storage.save_transactions()


def check_login(account, password):
    if account == "555" and password == "fry":
        return True
    if account == "333" and password == "leela":
        return True
    return False


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
    tx = from_dict(Transaction, data)

    account = tx.from_account
    if not check_login(account, data["password"]):
        abort(401)  # 401 Unauthorized

    try:
        transact(tx)
        return jsonify(status="ok")
    except Exception as e:
        return jsonify(status="err", error=str(e))


@app.route("/reload")
def reload():
    storage.load_transactions()
    return jsonify(status="ok")
