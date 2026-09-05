"""Nadgledanje pametnih ugovora u pozadini.

Zaposleni glasaju u trenutku koji nije unapred poznat, pa je neophodno
periodicno proveravati stanje svakog aktivnog ugovora. Kada ugovor
prikupi potrebnu vecinu glasova, zahtev se evidentira u MongoDB bazi
(ako je odobren) i uklanja iz Redis servisa.
"""

import json
import threading
import time

from application.blockchain import contract_status
from application.configuration import Configuration
from application.db import cache
from application.orders import finalize_order

_started = threading.Lock()
_is_started = False


def register_contract(order_uuid, address, order):
    """Belezi novi ugovor koji treba nadgledati."""
    cache().hset(
        Configuration.REDIS_CONTRACTS_KEY,
        order_uuid,
        json.dumps({"address": address, "order": order}),
    )


def check_once():
    """Jedan prolaz kroz sve registrovane ugovore."""
    contracts = cache().hgetall(Configuration.REDIS_CONTRACTS_KEY)

    for order_uuid, raw in contracts.items():
        try:
            entry = json.loads(raw)
            finished, approved = contract_status(entry["address"])
            if not finished:
                continue

            if finalize_order(order_uuid, approved, entry.get("order")):
                outcome = "odobren" if approved else "odbijen"
                print(f"[watcher] Zahtev {order_uuid} je {outcome} glasanjem.", flush=True)
            else:
                # zahtev je vec obradjen u drugom procesu
                cache().hdel(Configuration.REDIS_CONTRACTS_KEY, order_uuid)
        except Exception as exception:  # noqa: BLE001
            print(f"[watcher] Greska pri obradi {order_uuid}: {exception}", flush=True)


def _loop():
    print("[watcher] Nadgledanje glasanja je pokrenuto.", flush=True)
    while True:
        try:
            check_once()
        except Exception as exception:  # noqa: BLE001
            # Redis ili blockchain simulator mogu biti privremeno nedostupni
            # (npr. odmah nakon pokretanja sistema); nit ne sme da se ugasi.
            print(f"[watcher] Neocekivana greska u prolazu: {exception}", flush=True)
        time.sleep(Configuration.WATCHER_INTERVAL)


def start_watcher():
    """Pokrece nadzornu nit najvise jednom po procesu."""
    global _is_started
    with _started:
        if _is_started or not Configuration.WATCHER_ENABLED:
            return
        _is_started = True
        thread = threading.Thread(target=_loop, name="voting-watcher", daemon=True)
        thread.start()
