"""Pomocni skript za glasanje zaposlenih nad kreiranim pametnim ugovorom.

Servis direktora vraca dve nepotpisane transakcije (approve_transaction i
reject_transaction). Zaposleni glasa tako sto jednu od njih posalje sa svog
Ethereum racuna. Ovaj skript to radi koristeci racune koje simulator otkljuca
prilikom pokretanja.

Primeri:

    # ispis dostupnih racuna
    python scripts/vote.py accounts --url http://localhost:30004

    # glasanje racunom sa indeksom 1, transakcija se cita iz datoteke
    python scripts/vote.py send --url http://localhost:30004 --account 1 --file approve.json

    # transakcija se cita sa standardnog ulaza
    cat approve.json | python scripts/vote.py send --account 2
"""

import argparse
import json
import sys

from web3 import Web3


def connect(url):
    web3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 30}))
    if not web3.is_connected():
        print(f"Nije moguce povezati se na simulator: {url}", file=sys.stderr)
        sys.exit(1)
    return web3


def command_accounts(arguments):
    web3 = connect(arguments.url)
    for index, account in enumerate(web3.eth.accounts):
        balance = web3.from_wei(web3.eth.get_balance(account), "ether")
        print(f"[{index:2}] {account}  {balance} ETH")


def command_send(arguments):
    web3 = connect(arguments.url)

    if arguments.file:
        with open(arguments.file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = json.load(sys.stdin)

    # dozvoljeno je proslediti i ceo odgovor servisa direktora
    if "approve_transaction" in payload or "reject_transaction" in payload:
        key = "reject_transaction" if arguments.reject else "approve_transaction"
        transaction = payload[key]
    else:
        transaction = payload

    accounts = web3.eth.accounts
    if arguments.address:
        sender = Web3.to_checksum_address(arguments.address)
    else:
        if arguments.account >= len(accounts):
            print("Racun sa datim indeksom ne postoji.", file=sys.stderr)
            sys.exit(1)
        sender = accounts[arguments.account]

    transaction = dict(transaction)
    transaction["from"] = sender
    transaction.pop("chainId", None)

    print(f"Saljem glas sa racuna {sender} ...")
    try:
        transaction_hash = web3.eth.send_transaction(transaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=120)
        print(f"Transakcija: {receipt['transactionHash'].hex()}  status={receipt['status']}")
    except Exception as exception:  # noqa: BLE001
        print(f"Glasanje odbijeno: {exception}", file=sys.stderr)
        sys.exit(1)


def main():
    # --url se navodi i pre i posle podkomande, pa je definisan u zajednickom
    # roditeljskom parseru koji nasledjuju sve podkomande
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--url", default="http://localhost:30004", help="adresa Ethereum simulatora")

    parser = argparse.ArgumentParser(description="Glasanje nad pametnim ugovorom.", parents=[common])

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("accounts", help="ispis dostupnih Ethereum racuna", parents=[common])

    send_parser = subparsers.add_parser("send", help="slanje glasa", parents=[common])
    send_parser.add_argument("--account", type=int, default=1, help="indeks racuna glasaca")
    send_parser.add_argument("--address", help="eksplicitna adresa racuna glasaca")
    send_parser.add_argument("--file", help="datoteka sa transakcijom u JSON formatu")
    send_parser.add_argument(
        "--reject",
        action="store_true",
        help="ako je prosledjen ceo odgovor servisa, salje se glas za odbijanje",
    )

    arguments = parser.parse_args()

    if arguments.command == "accounts":
        command_accounts(arguments)
    else:
        command_send(arguments)


if __name__ == "__main__":
    main()
