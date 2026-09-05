"""Veb servis sa funkcionalnostima dostupnim zaposlenima investicionog fonda."""

import json
import re
import uuid as uuid_module

from bson import ObjectId
from flask import Flask, request
from flask_jwt_extended import JWTManager

from application.configuration import Configuration
from application.db import assets, cache
from application.responses import empty_ok, error, json_response
from application.security import role_required
from application.serialization import parse_iso_datetime, serialize_asset
from application.validation import (
    MAX_LENGTH,
    first_missing,
    normalize_operator,
    valid_categories,
    valid_object_id,
    valid_price,
)

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def build_search_query(payload):
    """Sastavlja MongoDB upit na osnovu opcionih filtera iz tela zahteva.

    Vraca (query, error_message). Sva filtriranja se izvrsavaju u bazi.
    """
    conditions = []

    name = payload.get("name")
    if isinstance(name, str) and len(name) > 0:
        if len(name) > MAX_LENGTH:
            return None, "Invalid name."
        conditions.append({"name": {"$regex": re.escape(name)}})

    category = payload.get("category")
    if isinstance(category, str) and len(category) > 0:
        if len(category) > MAX_LENGTH:
            return None, "Invalid category."
        conditions.append({"categories": category})

    if payload.get("buying_date") not in (None, ""):
        buying_date = parse_iso_datetime(payload.get("buying_date"))
        if buying_date is None:
            return None, "Invalid buying date."
        # samo imovine kupljene nakon zadatog datuma
        conditions.append({"buying_date": {"$gte": buying_date}})

    if payload.get("selling_date") not in (None, ""):
        selling_date = parse_iso_datetime(payload.get("selling_date"))
        if selling_date is None:
            return None, "Invalid selling date."
        # samo imovine prodate pre zadatog datuma; neprodate se ne ukljucuju
        conditions.append({"selling_date": {"$ne": None, "$lte": selling_date}})

    info_filters = payload.get("info_filters")
    if info_filters is not None:
        if not isinstance(info_filters, list):
            return None, "Invalid info filters."
        for info_filter in info_filters:
            if not isinstance(info_filter, dict):
                return None, "Invalid info filters."

            field = info_filter.get("field")
            if not isinstance(field, str) or len(field) == 0:
                return None, "Invalid info filter field."
            if field.startswith("$") or ".." in field or field.startswith(".") or field.endswith("."):
                return None, "Invalid info filter field."

            operator = normalize_operator(info_filter.get("operator"))
            if operator is None:
                return None, "Invalid info filter operator."

            if "value" not in info_filter:
                return None, "Invalid info filter value."

            # putanja je relativna u odnosu na info polje imovine
            conditions.append({f"info.{field}": {operator: info_filter["value"]}})

    if len(conditions) == 0:
        return {}, None
    return {"$and": conditions}, None


@application.route("/search", methods=["POST"])
@role_required(Configuration.ROLE_EMPLOYEE)
def search():
    payload = request.get_json(silent=True) or {}

    query, message = build_search_query(payload)
    if message is not None:
        return error(message)

    documents = assets().find(query)
    return json_response({"assets": [serialize_asset(document) for document in documents]})


@application.route("/create_buy_order", methods=["POST"])
@role_required(Configuration.ROLE_EMPLOYEE)
def create_buy_order():
    payload = request.get_json(silent=True) or {}

    fields = ["name", "categories", "buying_price", "info"]

    missing = first_missing(payload, fields)
    if missing is not None:
        return error(f"Field {missing} is missing.")

    if not isinstance(payload["name"], str) or len(payload["name"]) > MAX_LENGTH:
        return error("Field name is missing.")

    if not isinstance(payload["categories"], list):
        return error("Field categories is missing.")

    if len(payload["categories"]) == 0:
        return error("Categories list is empty.")

    if not valid_categories(payload["categories"]):
        return error("Field categories is missing.")

    if not valid_price(payload["buying_price"]):
        return error("Invalid buying price.")

    if not isinstance(payload["info"], dict):
        return error("Field info is missing.")

    order_uuid = str(uuid_module.uuid4())
    order = {
        "uuid": order_uuid,
        "order_type": "BUY",
        "name": payload["name"],
        "categories": payload["categories"],
        "info": payload["info"],
        "buying_price": payload["buying_price"],
    }

    cache().hset(Configuration.REDIS_ORDERS_KEY, order_uuid, json.dumps(order))

    return empty_ok()


@application.route("/create_sell_order", methods=["POST"])
@role_required(Configuration.ROLE_EMPLOYEE)
def create_sell_order():
    payload = request.get_json(silent=True) or {}

    fields = ["id", "selling_price"]

    missing = first_missing(payload, fields)
    if missing is not None:
        return error(f"Field {missing} is missing.")

    if not valid_object_id(payload["id"]):
        return error("Invalid id.")

    asset = assets().find_one({"_id": ObjectId(payload["id"])}, {"_id": 1})
    if asset is None:
        return error("Invalid id.")

    if not valid_price(payload["selling_price"]):
        return error("Invalid selling price.")

    order_uuid = str(uuid_module.uuid4())
    order = {
        "uuid": order_uuid,
        "order_type": "SELL",
        "id": payload["id"],
        "selling_price": payload["selling_price"],
    }

    cache().hset(Configuration.REDIS_ORDERS_KEY, order_uuid, json.dumps(order))

    return empty_ok()


@application.route("/health", methods=["GET"])
def health():
    return json_response({"status": "ok", "service": "employee"})


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
