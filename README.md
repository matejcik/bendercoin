# BenderCoin

A simple implementation of a cryptocurrency, intended for teaching.

The Git history is structured in logical steps, building from a simple
"bank" server to a fully trustless currency. At the tagged steps, the code is
fully functional and can be used to demonstrate.

Storage is inefficient, intended for reading by humans (and modifying and seeing
what happens). There is currently no distributed communication; the intention
is to broadcast transactions and blocks to a known fixed set of servers.

## Installation

BenderCoin requires Python 3.6 and `pipenv`. It uses the following libraries:

* [Flask](http://flask.pocoo.org) for the webserver
* [Click](http://click.pocoo.org) for command-line client
* [requests](http://docs.python-requests.org) for communication
* [Ed25519](https://github.com/warner/python-ed25519) for signatures
* [base58](https://github.com/keis/base58) for addresses
* [attrs](http://www.attrs.org) for classes without boilerplate
* termcolor for pretty colors

With existing Python 3.6 installation, you can get all of it like this:

```sh
python3.6 -m ensurepip
# use "python3.6 -m ensurepip --user" if you don't have root
python3.6 -m pip install pipenv
# again, add "--user" if you don't have root
cd /path/to/bendercoin
pipenv install
```

## Usage

From the checkout directory, run the server:
```sh
export FLASK_APP="bendercoin/bank.py"
# add the following if you want live-reload
# export FLASK_DEBUG=1
# but note that clever people will hack your server with it :)
pipenv run python -m flask run
```

Run commands from the client:
```sh
pipenv shell
# show list of commands
python -m bendercoin.client
# run a command
python -m bendercoin.client send fry leela 500 -m "money"
```

## License

The code is available under MIT license.
