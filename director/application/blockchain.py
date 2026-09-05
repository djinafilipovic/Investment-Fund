"""Integracija sa Ethereum Blockchain platformom (ganache-cli simulator)."""

import json
import pathlib
import threading

from web3 import Web3

from application.configuration import Configuration

ARTIFACT_PATH = pathlib.Path(__file__).resolve().parent.parent / "contracts" / "Voting.json"

_lock = threading.Lock()
_web3_instance = None
_artifact = None


def get_web3():
    """Vraca (i po potrebi kreira) Web3 klijent povezan na simulator."""
    global _web3_instance
    with _lock:
        if _web3_instance is None:
            _web3_instance = Web3(Web3.HTTPProvider(Configuration.GANACHE_URL, request_kwargs={"timeout": 30}))
        return _web3_instance


def get_artifact():
    """Ucitava ABI i bytecode ugovora; kompajlira ga ako artefakt ne postoji."""
    global _artifact
    with _lock:
        if _artifact is None:
            if ARTIFACT_PATH.exists():
                _artifact = json.loads(ARTIFACT_PATH.read_text())
            else:
                from compile_contract import compile_contract

                _artifact = compile_contract()
        return _artifact


def get_contract(address):
    web3 = get_web3()
    artifact = get_artifact()
    return web3.eth.contract(address=Web3.to_checksum_address(address), abi=artifact["abi"])


def valid_address(address):
    return isinstance(address, str) and Web3.is_address(address)


def _encode_vote(contract, approve):
    """Kodira poziv funkcije vote(bool) u calldata (radi sa web3 v6 i v7)."""
    if hasattr(contract, "encode_abi"):
        try:
            return contract.encode_abi("vote", args=[approve])
        except TypeError:
            return contract.encode_abi(abi_element_identifier="vote", args=[approve])
    return contract.encodeABI(fn_name="vote", args=[approve])


def deploy_voting_contract(order_uuid, voters):
    """Kreira novi objekat pametnog ugovora za dati zahtev.

    Naknadu za kreiranje ugovora placa jedan od racuna koje simulator
    kreira prilikom pokretanja. Vraca adresu kreiranog ugovora.
    """
    web3 = get_web3()
    artifact = get_artifact()

    accounts = web3.eth.accounts
    if len(accounts) == 0:
        raise RuntimeError("Simulator nije vratio nijedan Ethereum racun.")

    deployer = accounts[min(Configuration.DEPLOYER_ACCOUNT_INDEX, len(accounts) - 1)]

    factory = web3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
    checksummed = [Web3.to_checksum_address(address) for address in voters]

    transaction_hash = factory.constructor(order_uuid, checksummed).transact(
        {
            "from": deployer,
            "gas": Configuration.CONTRACT_GAS_LIMIT,
            "gasPrice": web3.eth.gas_price,
        }
    )
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=120)

    if receipt is None or receipt.get("contractAddress") is None:
        raise RuntimeError("Kreiranje pametnog ugovora nije uspelo.")

    return Web3.to_checksum_address(receipt["contractAddress"])


def build_vote_transactions(address):
    """Priprema dve nepotpisane transakcije: glas za i glas protiv.

    Glasac transakciju salje sa svog racuna (dodaje polja from i nonce).
    """
    web3 = get_web3()
    contract = get_contract(address)

    def transaction(approve):
        return {
            "to": Web3.to_checksum_address(address),
            "data": _encode_vote(contract, approve),
            "value": 0,
            "gas": Configuration.VOTE_GAS_LIMIT,
            "gasPrice": int(web3.eth.gas_price),
            "chainId": int(web3.eth.chain_id),
        }

    return transaction(True), transaction(False)


def contract_status(address):
    """Vraca (finished, approved) stanje glasanja iz pametnog ugovora."""
    contract = get_contract(address)
    finished, approved, _approve_votes, _reject_votes, _majority = contract.functions.status().call()
    return bool(finished), bool(approved)
