"""Obrada odobrenih zahteva i formiranje izvestaja o poslovanju fonda."""

import json
from datetime import datetime, timezone

from bson import ObjectId

from application.configuration import Configuration
from application.db import assets, cache

PROCESSED_KEY_PREFIX = "processed_order:"
PROCESSED_TTL_SECONDS = 24 * 60 * 60


def load_order(order_uuid):
    """Cita zahtev iz Redis servisa; vraca None ako zahtev ne postoji."""
    raw = cache().hget(Configuration.REDIS_ORDERS_KEY, order_uuid)
    if raw is None:
        return None
    return json.loads(raw)


def remove_order(order_uuid):
    cache().hdel(Configuration.REDIS_ORDERS_KEY, order_uuid)
    cache().hdel(Configuration.REDIS_CONTRACTS_KEY, order_uuid)


def claim_order(order_uuid):
    """Sprecava dvostruku obradu istog zahteva (vise radnika / replika).

    Vraca True samo prvom pozivaocu za dati identifikator zahteva.
    """
    return bool(
        cache().set(PROCESSED_KEY_PREFIX + order_uuid, "1", nx=True, ex=PROCESSED_TTL_SECONDS)
    )


def apply_order(order):
    """Evidentira odobren zahtev u MongoDB bazi podataka."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if order.get("order_type") == "BUY":
        document = {
            "name": order.get("name"),
            "categories": order.get("categories", []),
            "buying_price": order.get("buying_price"),
            "buying_date": now,
            "info": order.get("info", {}),
        }
        result = assets().insert_one(document)
        return str(result.inserted_id)

    if order.get("order_type") == "SELL":
        assets().update_one(
            {"_id": ObjectId(order.get("id"))},
            {"$set": {"selling_price": order.get("selling_price"), "selling_date": now}},
        )
        return order.get("id")

    raise ValueError(f"Nepoznat tip zahteva: {order.get('order_type')}")


def finalize_order(order_uuid, approved, order=None):
    """Zavrsna obrada zahteva: upis u MongoDB (ako je odobren) i brisanje iz Redis servisa."""
    if not claim_order(order_uuid):
        return False

    if approved:
        if order is None:
            order = load_order(order_uuid)
        if order is not None:
            apply_order(order)

    remove_order(order_uuid)
    return True


def category_statistics():
    """Agregacija po kategorijama: potroseno i zaradjeno, sa trazenim sortiranjem.

    Ukoliko imovina pripada vise kategorija, racuna se u statistiku svake od njih.
    U zaradu ulazi samo imovina koja ima i cenu i datum prodaje.
    """
    pipeline = [
        {"$unwind": "$categories"},
        {
            "$group": {
                "_id": "$categories",
                "spent": {"$sum": {"$ifNull": ["$buying_price", 0]}},
                "earned": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": [{"$ifNull": ["$selling_price", None]}, None]},
                                    {"$ne": [{"$ifNull": ["$selling_date", None]}, None]},
                                ]
                            },
                            "$selling_price",
                            0,
                        ]
                    }
                },
            }
        },
        {"$project": {"_id": 0, "category": "$_id", "spent": 1, "earned": 1}},
        {"$sort": {"earned": -1, "spent": 1, "category": 1}},
    ]

    return list(assets().aggregate(pipeline))
