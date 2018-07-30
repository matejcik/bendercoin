import json
import click
import requests
from termcolor import cprint
from .util import print_json, from_dict
from .transaction import Transaction

LOGINS = {
    "fry": ("555", "fry"),
    "leela": ("333", "leela"),
}

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

    for item in r.json():
        tx = from_dict(Transaction, item)
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
