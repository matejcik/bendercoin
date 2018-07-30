import json
import click
import requests
from termcolor import cprint
from .util import print_json
from .transaction import Transaction
import ed25519

# fmt: off
LOGINS = {
    "fry": ed25519.SigningKey("4f1156f60557ebb8d9eab50621b0b250a191b05965fcaf799786c0a38b0bd9e07d8e33b6e68b8e9c69cec242ba1a69ee60e9e70e06070e39f9770bbf96942d24", encoding="hex"),
    "leela": ed25519.SigningKey("48248840dfc08040cdeabde3872947d2c04cfa36729cd7a613db33bd113814e1048423bbeda5e7a8f41a78dedc9a787fead95498058955aa091a996945b10289", encoding="hex"),
}
# fmt: on

BANK_URL = "http://localhost:5000"


def print_tx(tx, account):
    if tx.message:
        msg = f" (message: {tx.message})"
    else:
        msg = ""
    if tx.from_account == account:
        color = "red"
        out = f"-{tx.amount} >> {tx.to_account}"
    elif tx.to_account == account:
        color = "green"
        out = f"+{tx.amount} << {tx.from_account}"
    else:
        color = "blue"
        out = f"weird transaction: {tx}"
    cprint(out + msg, color=color)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("account")
def balance(account):
    num, _ = LOGINS[account]
    r = requests.get(BANK_URL + "/balance/" + num)
    print_json(r)


@cli.command()
@click.argument("account")
def history(account):
    num, _ = LOGINS[account]
    r = requests.get(BANK_URL + "/history/" + num)
    try:
        j = r.json()
    except Exception as e:
        print("failed to decode json")
        print(r.text)
        raise click.ClickException(e)

    for item in j:
        tx = Transaction.from_dict(item)
        print_tx(tx, num)


@cli.command()
@click.argument("sender")
@click.argument("recipient")
@click.argument("amount", type=int)
@click.option("-m", "--message", default="")
def send(sender, recipient, amount, message):
    from_acct, password = LOGINS[sender]
    to_acct, _ = LOGINS[recipient]
    data = dict(
        from_account=from_acct,
        to_account=to_acct,
        amount=amount,
        message=message,
        password=password,
    )
    r = requests.post(BANK_URL + "/send_tx", json=data)
    print_json(r)


@cli.command()
def reload():
    r = requests.get(BANK_URL + "/reload")
    print_json(r)


if __name__ == "__main__":
    cli()
