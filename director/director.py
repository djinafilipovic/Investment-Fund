"""Veb servis sa funkcionalnostima dostupnim direktoru investicionog fonda."""

import json

from flask import Flask, request
from flask_jwt_extended import JWTManager

from application.blockchain import build_vote_transactions, deploy_voting_contract, valid_address
from application.configuration import Configuration
from application.db import cache
from application.orders import category_statistics, finalize_order, load_order
from application.responses import empty_ok, error, json_response
from application.security import role_required
from application.validation import missing_field, valid_uuid
from application.watcher import register_contract, start_watcher

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

# nadzorna nit prati ugovore i zavrsava obradu zahteva kada glasanje bude zavrseno
start_watcher()


@application.route("/pending_orders", methods=["GET"])
@role_required(Configuration.ROLE_DIRECTOR)
def pending_orders():
    stored = cache().hgetall(Configuration.REDIS_ORDERS_KEY)
    orders = [json.loads(raw) for raw in stored.values()]
    return json_response({"orders": orders})


@application.route("/decision", methods=["POST"])
@role_required(Configuration.ROLE_DIRECTOR)
def decision():
    """Odobravanje zahteva glasanjem (kreira se pametni ugovor na Ethereum platformi)."""
    payload = request.get_json(silent=True) or {}

    if missing_field(payload, "uuid"):
        return error("Field uuid is missing.")

    order_uuid = payload["uuid"]
    if not valid_uuid(order_uuid):
        return error("Invalid uuid.")

    order = load_order(order_uuid)
    if order is None:
        return error("Invalid uuid.")

    voters = payload.get("voters")
    if voters is None or not isinstance(voters, list) or len(voters) == 0:
        return error("Field voters is missing.")

    for address in voters:
        if not valid_address(address):
            return error("Invalid voter address.")

    if len(voters) % 2 == 0:
        return error("Even number of voters.")

    try:
        contract_address = deploy_voting_contract(order_uuid, voters)
        approve_transaction, reject_transaction = build_vote_transactions(contract_address)
    except Exception as exception:  # noqa: BLE001
        application.logger.error("Kreiranje pametnog ugovora nije uspelo: %s", exception)
        return error("Smart contract deployment failed.", 500)

    register_contract(order_uuid, contract_address, order)

    return json_response(
        {
            "approve_transaction": approve_transaction,
            "reject_transaction": reject_transaction,
        }
    )


@application.route("/decision_basic", methods=["POST"])
@role_required(Configuration.ROLE_DIRECTOR)
def decision_basic():
    """Osnovna varijanta odlucivanja o ishodu zahteva, bez glasanja.

    Zadrzana je zbog demonstracije obaveznog dela projekta; prosirena
    varijanta sa glasanjem se nalazi na adresi /decision.
    """
    payload = request.get_json(silent=True) or {}

    if missing_field(payload, "uuid"):
        return error("Field uuid is missing.")

    order_uuid = payload["uuid"]
    if not valid_uuid(order_uuid):
        return error("Invalid uuid.")

    order = load_order(order_uuid)
    if order is None:
        return error("Invalid uuid.")

    if "approved" not in payload or payload["approved"] is None:
        return error("Field approved is missing.")

    if not isinstance(payload["approved"], bool):
        return error("Invalid decision.")

    finalize_order(order_uuid, payload["approved"], order)

    return empty_ok()


@application.route("/report", methods=["GET"])
@role_required(Configuration.ROLE_DIRECTOR)
def report():
    return json_response({"statistics": category_statistics()})


@application.route("/health", methods=["GET"])
def health():
    return json_response({"status": "ok", "service": "director"})


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=False)
