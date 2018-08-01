import json
import sys
import click
import requests
from termcolor import cprint
from .util import print_json, to_base64
from . import bank
from .transaction import Transaction, TxInput, TxOutput, address_from_pubkey
import ed25519

# fmt: off
LOGINS = {
    "fry": ed25519.SigningKey(b"4f1156f60557ebb8d9eab50621b0b250a191b05965fcaf799786c0a38b0bd9e07d8e33b6e68b8e9c69cec242ba1a69ee60e9e70e06070e39f9770bbf96942d24", encoding="hex"),
    "leela": ed25519.SigningKey(b"48248840dfc08040cdeabde3872947d2c04cfa36729cd7a613db33bd113814e1048423bbeda5e7a8f41a78dedc9a787fead95498058955aa091a996945b10289", encoding="hex"),
    "bender": bank.BENDER_KEY,
}
# fmt: on

BANK_URL = "http://localhost:5000"


def print_tx(tx, account):
    h = to_base64(tx.hash())
    cprint(f"tx {h}:", color="blue", end="")
    if tx.message:
        print(" " + tx.message)
    else:
        print()

    if tx.from_address() == account and tx.coinbase is None:
        for out in tx.outputs:
            if out.address == account:
                continue
            txt = f"-{out.amount} >> {out.address}"
            cprint(txt, color="red")

    elif account in tx.to_addresses():
        amount = tx.received(account)
        addr = tx.from_address()
        txt = f"+{amount} << {addr}"
        cprint(txt, color="green")

    else:
        from_account = tx.from_address()
        amount = tx.total_in()
        print(f"from {from_account}: {amount})")
        for o in tx.outputs:
            print(f"to {o.address}: {o.amount})")

    try:
        tx.validate()
        prev_tx = {}
        for inp in tx.inputs:
            prev_tx[inp.hash] = get_tx(inp.hash)
        tx.validate_previous(prev_tx)
        cprint("TX: OK", "blue")
    except Exception as e:
        cprint("TX: INVALID", "red", attrs=["bold"])
        print(e)
    print()


def address(login):
    priv = LOGINS[login]
    pub = priv.get_verifying_key()
    return address_from_pubkey(pub)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("account")
def balance(account):
    addr = address(account)
    r = requests.get(BANK_URL + "/balance/" + addr)
    print_json(r)


def get_tx(hash):
    r = requests.get(BANK_URL + "/tx/" + hash)
    try:
        j = r.json()
    except Exception as e:
        print("failed to decode json")
        print(r.text)
        raise click.ClickException(e)

    return Transaction.from_dict(j)


def get_history(addr):
    r = requests.get(BANK_URL + "/history/" + addr)
    try:
        j = r.json()
    except Exception as e:
        print("failed to decode json")
        print(r.text)
        raise click.ClickException(e)

    res = []
    for item in j:
        res.append(Transaction.from_dict(item))
    return res


def get_unspent(addr):
    hist = get_history(addr)
    possible = set()
    spent = set()
    for tx in hist:
        hash = to_base64(tx.hash())
        for inp in tx.inputs:
            spent.add(inp)
        for idx, out in enumerate(tx.outputs):
            if out.address == addr:
                inp = TxInput(hash=hash, index=idx, amount=out.amount)
                possible.add(inp)

    return possible - spent


@cli.command()
@click.argument("account")
def history(account):
    addr = address(account)
    for tx in get_history(addr):
        print_tx(tx, addr)


@cli.command()
@click.argument("sender")
@click.argument("recipient")
@click.argument("amount", type=int)
@click.option("-m", "--message", default="")
def send(sender, recipient, amount, message):
    if amount <= 0:
        raise click.ClickException("bad amount")

    priv = LOGINS[sender]
    unspent = get_unspent(address(sender))
    inputs = []
    total = 0
    for inp in unspent:
        inputs.append(inp)
        total += inp.amount
        if total >= amount:
            break

    if total < amount:
        raise click.ClickException("not enough money")

    output_send = TxOutput(amount=amount, address=address(recipient))
    if amount < total:
        output_change = TxOutput(amount=total - amount, address=address(sender))
        outputs = [output_send, output_change]
    else:
        outputs = [output_send]

    tx = Transaction(message=message, inputs=inputs, outputs=outputs)
    tx.sign(priv)
    data = tx.to_dict()
    print("signed transaction:")
    print_json(data)
    r = requests.post(BANK_URL + "/send_tx", json=data)
    print_json(r)


@cli.command()
@click.argument("file", type=click.File("r"), default=sys.stdin)
def send_raw(file):
    j = json.load(file)
    r = requests.post(BANK_URL + "/send_tx", json=j)
    print_json(r)


@cli.command()
def reload():
    r = requests.get(BANK_URL + "/reload")
    print_json(r)


@cli.command()
def make_block():
    r = requests.get(BANK_URL + "/make_block")
    print_json(r)


if __name__ == "__main__":
    cli()
